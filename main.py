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


creds_json = os.environ['GCP_CREDENTIALS']
creds_dict = json.loads(creds_json)
creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)

# Get sheet ID from environment variable
sheet_id = os.environ['SHEET_ID']

client = gspread.authorize(creds)
work_book = client.open_by_key(sheet_id)



sheet = work_book.worksheets()[0]

data = legal_hours_check.get_data()
# Clear existing data
sheet.clear()


# Prepare header and data rows
headers = ["Organization", "Office Hours", "Phone Number"]
rows = [headers]

for i in range(len(data['name'])):
    # Combine name and website in the same cell with line break
    org_with_website = f"{data['name'][i]}\n{data['website'][i]}"
    rows.append([
        org_with_website,
        data['office hours'][i],
        data['phone'][i]
    ])


# Write all data to the sheet
sheet.update(values=rows, range_name='A3')  # Fixed parameter order



# Apply basic formatting
sheet.merge_cells("A1:C1")
sheet.merge_cells("B8:C8")
sheet.merge_cells("A2:C2")

sheet.format("A3:C3", {
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


sheet.format(f"A4:D{len(rows)+3}", {
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
    row_index = i + 4  # +2 for header row
    url = data['website'][i]
    display_text = f"{data['name'][i]}"
    
    # Create HYPERLINK formula
    formula = f'=HYPERLINK("{url}", "{display_text}")'
    
    # Update the cell with the formula
    sheet.update_cell(row_index, 1, formula)


#Date update
sheet.format("B8", {
    "horizontalAlignment": "RIGHT"
})
california_date = datetime.now(ZoneInfo('America/Los_Angeles')).strftime('%Y-%m-%d %H:%M %Z')
sheet.update_cell(8, 2, "Last updated: " + str(california_date))



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


# Auto-resize columns
sheet.columns_auto_resize(0, 2)
sheet.rows_auto_resize(0,8)

