# Follow-up Email Format Example

## How the AI Generates Follow-up Emails

When the follow-up date arrives (as set by staff in the dropdown), the AI automatically generates a professional reminder email.

---

## Example Follow-up Email

### Scenario
- **Applicant**: John Smith
- **Original Issue**: Missing passport expiry date
- **Days Since Contact**: 7 days
- **Follow-up Date**: Set by staff to "7 days" in dropdown

### Generated Email

**Subject**: Follow-up: missing_elements - Australia Visa Application

**Body**:

```html
<p>Dear John Smith,</p>

<p>I hope this email finds you well.</p>

<p>I am following up on our previous correspondence regarding your missing_elements issue sent 7 days ago.</p>

<p>Original concern: Missing passport expiry date - Please provide updated document</p>

<p>We wanted to check if you have had the opportunity to address this matter or if you require any assistance from our team.</p>

<p>If you have already submitted the updated documents, please disregard this message. Otherwise, we are here to help guide you through the process.</p>

<p>Please feel free to reach out if you have any questions or need clarification.</p>

<p>Kind regards,<br>
<strong>Senior Immigration Consultant</strong><br>
Australia Visa Agent</p>
```

---

## Staff Control via Dropdown

Staff can change the follow-up timing in Google Sheets:

### Dropdown Options:
- **1 day** - Urgent follow-up
- **3 days** - Quick reminder
- **5 days** - Standard follow-up
- **7 days** - Default (one week)
- **14 days** - Two weeks
- **30 days** - One month
- **Custom** - Staff can enter any specific date (YYYY-MM-DD format)

### How It Works:

1. **Email sent** → Logged to Google Sheets with "7 days" default
2. **Staff reviews** → Changes dropdown to "3 days" for urgent case
3. **AI calculates** → 3 days from original send date
4. **Follow-up sent** → Automatically on the calculated date

---

## Custom Date Example

Staff can also enter specific dates:

- **Dropdown value**: `2026-02-20`
- **AI behavior**: Send follow-up on exactly Feb 20, 2026

---

## Email Tone

The AI maintains a:
- ✅ Professional and courteous tone
- ✅ References the original issue
- ✅ Offers assistance
- ✅ Doesn't pressure the applicant
- ✅ Provides clear next steps

---

## Automatic Tracking

After sending follow-up:
- Status column updated to "Follow-up Sent (timestamp)"
- No further follow-ups sent for that entry
- Staff can manually mark "Response Received" as "Yes" to close the loop
