# Google Sheets Email Tracking - Setup Guide

## Prerequisites

You need:
1. A Google Spreadsheet for tracking emails
2. Google Sheets API enabled in Google Cloud Console
3. Your service account email (same one used for Google Drive)

## Step 1: Enable Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Go to "APIs & Services" > "Library"
4. Search for "Google Sheets API"
5. Click "Enable"

## Step 2: Create Tracking Spreadsheet

1. Create a new Google Spreadsheet
2. Name it "Email Delivery Tracking" (or any name you prefer)
3. Copy the Spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID_HERE/edit
   ```

## Step 3: Share Spreadsheet with Service Account

1. Open your spreadsheet
2. Click "Share"
3. Add your service account email (found in `gcpkyawzin.ccna.json`)
4. Give it "Editor" permissions

## Step 4: Update .env File

Add this line to your `.env` file:

```bash
EMAIL_TRACKING_SPREADSHEET_ID=your_spreadsheet_id_here
```

## Step 5: Test the Integration

Run this command to test:

```bash
source venv/bin/activate
python3 services/google_sheets_service.py
```

You should see:
- ✓ Initialized Google Sheets with headers
- ✓ Logged email to Google Sheets: Test Applicant - missing_elements

## Step 6: Restart the System

```bash
./start.sh
```

## What Happens Now

### Automatic Email Logging
Every time an email is sent to an applicant, it's automatically logged to Google Sheets with:
- Timestamp
- Applicant Name
- Passport/Document ID
- Contact
- Issue Type
- Email Address
- Reason/Details
- Status
- Follow-up Date (7 days later)
- Response Received

### Automatic Follow-ups
The scheduler checks every 6 hours for emails sent 7+ days ago and automatically sends follow-up reminders.

## Viewing the Tracking Sheet

Open your Google Spreadsheet to see real-time email tracking!

## Troubleshooting

**Error: "EMAIL_TRACKING_SPREADSHEET_ID not set"**
- Make sure you added the spreadsheet ID to `.env`
- Restart the system after updating `.env`

**Error: "Permission denied"**
- Make sure you shared the spreadsheet with your service account email
- Check that the service account has "Editor" permissions

**Follow-ups not sending**
- Check the scheduler logs for errors
- Verify the spreadsheet has data older than 7 days
- Make sure the "Response Received" column is "No"
