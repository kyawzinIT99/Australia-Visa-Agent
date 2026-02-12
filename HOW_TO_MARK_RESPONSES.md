# How to Mark Customer Responses

## Quick Guide for Staff

When a customer replies to an email, follow these simple steps:

### Step 1: Open Google Sheets
Go to: [Email Delivery Tracking](https://docs.google.com/spreadsheets/d/12U-yYTEoILM1M_w2NL3DvfATu7cMkosTu_450bN2COc/edit)

### Step 2: Find the Customer's Row
Look for the customer's name or email address in the spreadsheet.

### Step 3: Update "Response Received" Column
1. Click on the cell in column **J** (Response Received)
2. Change "No" to "Yes"
3. Press Enter

### What Happens Automatically:
✅ Cell turns **green** (visual confirmation)  
✅ No more follow-up emails will be sent to that customer  
✅ Status shows the customer responded  

---

## Example

**Before:**
| Applicant Name | Email Address | Response Received |
|---|---|---|
| Sarah Johnson | sarah.johnson@example.com | No |

**After:**
| Applicant Name | Email Address | Response Received |
|---|---|---|
| Sarah Johnson | sarah.johnson@example.com | Yes ✅ |

---

## For Sarah Johnson's Case

Since you received a reply from sarah.johnson@example.com:

1. Open the [spreadsheet](https://docs.google.com/spreadsheets/d/12U-yYTEoILM1M_w2NL3DvfATu7cMkosTu_450bN2COc/edit)
2. Find Sarah Johnson's row (should be row 4)
3. Click on cell **J4** (Response Received column)
4. Change "No" to "Yes"
5. Press Enter

The cell will turn green and no more follow-ups will be sent! 🎉

---

## Future Automation

For fully automatic reply detection (no manual updates needed), we would need to:
1. Enable Gmail API domain-wide delegation in Google Workspace Admin
2. Grant additional permissions to the service account
3. Uncomment the automated code in `services/gmail_reply_monitor.py`

This is optional and can be set up later if needed.
