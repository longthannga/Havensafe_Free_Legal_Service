"""Write hours.json and the next-available message to the Google Sheet.

Reads only the local data file, so it can run every 30 minutes for free.
"""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from google.oauth2.service_account import Credentials

import availability

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GREEN = {"red": 42 / 255, "green": 76 / 255, "blue": 68 / 255}
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}


def get_client():
    # In GitHub Actions, put the service-account JSON in a secret called
    # GOOGLE_CREDENTIALS. Locally, credential.json still works.
    raw = os.environ.get("GOOGLE_CREDENTIALS")
    if raw:
        creds = Credentials.from_service_account_info(json.loads(raw), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("credential.json", scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheet_id():
    # GitHub Actions uses the SHEET_ID secret. Locally, you can instead add
    # "sheet_id": "..." to credential.json.
    sheet_id = os.environ.get("SHEET_ID")
    if not sheet_id and os.path.exists("credential.json"):
        with open("credential.json", encoding="utf-8") as f:
            sheet_id = json.load(f).get("sheet_id")
    if not sheet_id:
        raise SystemExit('No sheet ID found. Set SHEET_ID, or add "sheet_id" to credential.json.')
    return sheet_id


def org_cell_request(sheet_id, row_index, orgs):
    """Put "name<newline>phone" in column A, with only the name linked.

    This uses a rich-text link (like Insert > Link in Sheets) instead of a
    HYPERLINK formula, because the formula doesn't stay clickable when the
    text has a line break in it.
    """
    rows = []
    for org in orgs:
        text = f"{org['name']}\n{org['phone']}"
        rows.append({"values": [{
            "userEnteredValue": {"stringValue": text},
            "textFormatRuns": [
                {"startIndex": 0, "format": {"link": {"uri": org["website"]}}},
                {"startIndex": len(org["name"]), "format": {}},  # phone: no link
            ],
        }]})
    return {"updateCells": {
        "rows": rows,
        "fields": "userEnteredValue,textFormatRuns",
        "start": {"sheetId": sheet_id, "rowIndex": row_index, "columnIndex": 0},
    }}


def main():
    hours = availability.load_hours()
    orgs = hours["organizations"]
    tz = ZoneInfo(hours.get("timezone", "America/Los_Angeles"))

    sheet = get_client().open_by_key(get_sheet_id()).get_worksheet(0)

    # Layout:
    #   row 1  recommendations (A1:B1 merged)
    #   row 2  blank spacer
    #   row 3  headers
    #   row 4+ one row per organization
    #   last   "Last updated"
    first_org_row = 4
    date_row = first_org_row + len(orgs)

    rows = [
        [availability.generate_recommendations(hours), ""],
        ["", ""],
        ["Organization", "Office Hours"],
    ]
    for org in orgs:
        # Column A is filled in with links further down.
        rows.append(["", org["display_hours"]])
    stamp = datetime.now(tz).strftime("%Y-%m-%d %H:%M %Z")
    rows.append([f"Last updated: {stamp}", ""])

    # Clear old values and merges first, in case the number of orgs changed.
    sheet.clear()
    sheet.unmerge_cells("A1:B100")

    # RAW so Sheets never treats any text as a formula.
    sheet.update(values=rows, range_name="A1", value_input_option="RAW")

    for r in (1, 2, date_row):
        sheet.merge_cells(f"A{r}:B{r}")

    sheet.batch_format([
        {"range": "A1", "format": {
            "wrapStrategy": "WRAP", "verticalAlignment": "TOP",
            "textFormat": {"foregroundColor": GREEN}}},
        {"range": "A3:B3", "format": {
            "textFormat": {"bold": True, "foregroundColor": WHITE},
            "backgroundColor": GREEN, "horizontalAlignment": "CENTER"}},
        {"range": f"A{first_org_row}:B{date_row - 1}", "format": {
            "wrapStrategy": "WRAP", "verticalAlignment": "TOP",
            "textFormat": {"foregroundColor": GREEN}, "horizontalAlignment": "CENTER"}},
        {"range": f"A{date_row}", "format": {"horizontalAlignment": "RIGHT"}},
    ])

    # Done after the formatting so the links keep their link styling.
    sheet.spreadsheet.batch_update({"requests": [
        org_cell_request(sheet.id, first_org_row - 1, orgs)
    ]})


if __name__ == "__main__":
    main()