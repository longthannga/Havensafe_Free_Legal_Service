# Havensafe Free Legal Service Automation

> This project was created during my volunteer internship at [Havensafe](https://havensafe.org)

## 🏢 About Havensafe
**Our Mission:**  
*"Prevent homelessness by connecting at-risk people with resources including eviction support, educating stakeholders like landlords on available services, and fostering stronger connections between organizations to create a more efficient ecosystem of homelessness assistance."*

Havensafe works at the intersection of housing justice and homelessness prevention in the Bay Area, providing critical resources and support to vulnerable communities.

---

This repository contains an automated system that updates legal service information for several Bay Area organizations. The system scrapes websites for current office hours, phone numbers, and other details, then updates a Google Sheet with this information.

## ✨ Features
- Web scraping of 4 legal service organizations
- Automatic Google Sheets updating
- Scheduled weekly updates (every Monday)
- Secure credential handling

## ⚙️ How It Works
1. **Scraping**: The `legal_hours_check.py` script collects:
   - Organization names
   - Office hours
   - Phone numbers
   - Website URLs
   from 4 different legal service websites

2. **Google Sheets Update**: The `main.py` script:
   - Connects to Google Sheets API
   - Clears existing data
   - Updates with new information
   - Formats the sheet for readability
   - Adds last updated timestamp

3. **Automation**: The GitHub Action workflow:
   - Runs every Monday at 9 AM UTC (1-2 AM PST)
   - Securely accesses credentials
   - Executes the scripts
   - Commits any changes back to the repository

## 🛠️ Technical Requirements
- Python 3.10+
- Packages listed in `requirements.txt`
- Google Service Account credentials (stored securely in GitHub Secrets)

## 🔒 Security
- Credentials are stored in GitHub Secrets
- `credential.json` is excluded via `.gitignore`
- Service account has limited Google Sheets access

## ⏱️ Scheduled Updates
The system automatically updates the Google Sheet every Monday morning. You can also trigger updates manually:
1. Go to **Actions** tab
2. Select **Update Legal Services Sheet**
3. Click **Run workflow**

## 🚀 Getting Started
1. Clone this repository
2. Install requirements: `pip install -r requirements.txt`
3. Add your `credential.json` file (not committed)
4. Run locally: `python main.py`

## 📝 Project Context
Developed during my volunteer internship at Havensafe, this automation helps maintain accurate legal service information for:
- Tenants facing eviction
- Landlords seeking resources
- Community organizations
- Homelessness prevention advocates

> "By automating critical information updates, we ensure those in housing crisis can access timely legal support when they need it most."

## Data Protection

This repository does not handle personal user data. All automation interacts only with:
- Public websites (via web scraping)
- Google Sheets API (using service account credentials)
