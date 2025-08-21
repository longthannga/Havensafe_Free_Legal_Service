import os
import json
import gspread
from google.oauth2.service_account import Credentials
import legal_hours_check
from datetime import datetime
from zoneinfo import ZoneInfo
import availability_calculator


scopes = [
    "https://www.googleapis.com/auth/spreadsheets"    
    ]


creds = Credentials.from_service_account_file("credential.json", scopes = scopes)
client = gspread.authorize(creds)
sheet_id = os.environ.get('SHEET_ID')
work_book = client.open_by_key(sheet_id)



sheet = work_book.worksheets()[0]

data = legal_hours_check.get_data()
# Clear existing data
sheet.clear()


# Prepare header and data rows
headers = ["Organization", "Office Hours"]
rows = [headers]

for i in range(len(data['name'])):
    # Combine name and website in the same cell with line break
    org_with_website = f"{data['name'][i]}\n{data['phone'][i]}"
    rows.append([
        org_with_website,
        data['office hours'][i],
    ])


# Write all data to the sheet
sheet.update(values=rows, range_name='A3')  # Fixed parameter order



# Apply basic formatting
sheet.merge_cells("A1:B1")
sheet.merge_cells("A2:B2")

sheet.format("A3:B3", {
    "textFormat": {"bold": True,
            "foregroundColor": {  
            "red": 1.0,
            "green": 1.0,
            "blue": 1.0
            }
            },
    "backgroundColor": {
        "red": 42/255,
        "green": 76/255,
        "blue": 68/255
        },
    "horizontalAlignment": "CENTER"
})


# Update the range to accommodate the new organization (now 5 organizations instead of 4)
sheet.format(f"A4:B{len(rows)+3}", {
    "wrapStrategy": "WRAP",
    "verticalAlignment": "TOP",
    "textFormat": {"foregroundColor": {  
            "red": 42/255,
            "green": 76/255,
            "blue": 68/255
            }
        },
    "horizontalAlignment": "CENTER"
})


# Add hyperlinks using HYPERLINK formula
for i in range(len(data['name'])):
    row_index = i + 4  # +4 for header rows and starting position
    url = data['website'][i]
    display_text = f"{data['name'][i]}\n{data['phone'][i]}"
    
    # Create HYPERLINK formula
    formula = f'=HYPERLINK("{url}", "{display_text}")'
    
    # Update the cell with the formula
    sheet.update_cell(row_index, 1, formula)


#Date update - adjust row number for the new organization
# Now we have 5 organizations, so the date should go in row 9 instead of 8
date_row = len(data['name']) + 4  # 5 orgs + 3 header/spacing rows + 1 for next available row
sheet.format(f"A{date_row}", {
    "horizontalAlignment": "RIGHT"
})
california_date = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
sheet.update_cell(date_row, 1, "Last updated: " + str(california_date))

# Also need to merge the cells for the date row
sheet.merge_cells(f"A{date_row}:B{date_row}")


# Generate recommendations from scraped data
recommendations = availability_calculator.generate_recommendations(data)
sheet.update(range_name= "A1", values=[[recommendations]])


# Format the new sheet
sheet.format('A1', {
    "wrapStrategy": "WRAP",
    "verticalAlignment": "TOP",
    "textFormat": {
        "foregroundColor": {"red": 42/255, "green": 76/255, "blue": 68/255},
    }
})