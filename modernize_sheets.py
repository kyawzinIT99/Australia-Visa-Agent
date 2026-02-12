#!/usr/bin/env python3
"""
Modernize Google Sheets Design
Apply vibrant, professional styling to the Email Delivery Tracking spreadsheet
"""

import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

def modernize_sheets_design():
    """
    Apply modern, vibrant design to the tracking spreadsheet
    - Professional color scheme
    - Bold headers with gradient
    - Conditional formatting for status
    - Alternating row colors
    - Borders and styling
    """
    scopes = ['https://www.googleapis.com/auth/spreadsheets']
    creds = service_account.Credentials.from_service_account_file(
        'gcp-service-account.json', scopes=scopes
    )
    service = build('sheets', 'v4', credentials=creds)
    spreadsheet_id = os.getenv('EMAIL_TRACKING_SPREADSHEET_ID')
    
    requests = []
    
    # 1. HEADER ROW STYLING - Vibrant gradient header
    requests.append({
        "repeatCell": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 0,
                "endRowIndex": 1,
                "startColumnIndex": 0,
                "endColumnIndex": 10
            },
            "cell": {
                "userEnteredFormat": {
                    "backgroundColor": {
                        "red": 0.26,
                        "green": 0.52,
                        "blue": 0.96  # Modern blue
                    },
                    "textFormat": {
                        "foregroundColor": {
                            "red": 1.0,
                            "green": 1.0,
                            "blue": 1.0
                        },
                        "fontSize": 11,
                        "bold": True
                    },
                    "horizontalAlignment": "CENTER",
                    "verticalAlignment": "MIDDLE",
                    "padding": {
                        "top": 8,
                        "bottom": 8,
                        "left": 5,
                        "right": 5
                    }
                }
            },
            "fields": "userEnteredFormat(backgroundColor,textFormat,horizontalAlignment,verticalAlignment,padding)"
        }
    })
    
    # 2. FREEZE HEADER ROW
    requests.append({
        "updateSheetProperties": {
            "properties": {
                "sheetId": 0,
                "gridProperties": {
                    "frozenRowCount": 1
                }
            },
            "fields": "gridProperties.frozenRowCount"
        }
    })
    
    # 3. ALTERNATING ROW COLORS - Subtle zebra striping
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": 0,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 0,
                    "endColumnIndex": 10
                }],
                "booleanRule": {
                    "condition": {
                        "type": "CUSTOM_FORMULA",
                        "values": [{
                            "userEnteredValue": "=MOD(ROW(),2)=0"
                        }]
                    },
                    "format": {
                        "backgroundColor": {
                            "red": 0.95,
                            "green": 0.97,
                            "blue": 1.0  # Light blue tint
                        }
                    }
                }
            },
            "index": 0
        }
    })
    
    # 4. STATUS COLUMN CONDITIONAL FORMATTING - Color-coded status
    # Green for "Sent"
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": 0,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 7,  # Status column (H)
                    "endColumnIndex": 8
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{
                            "userEnteredValue": "Sent"
                        }]
                    },
                    "format": {
                        "backgroundColor": {
                            "red": 0.85,
                            "green": 0.92,
                            "blue": 0.83  # Light green
                        },
                        "textFormat": {
                            "foregroundColor": {
                                "red": 0.13,
                                "green": 0.55,
                                "blue": 0.13
                            },
                            "bold": True
                        }
                    }
                }
            },
            "index": 1
        }
    })
    
    # Orange for "Follow-up Sent"
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": 0,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 7,
                    "endColumnIndex": 8
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_CONTAINS",
                        "values": [{
                            "userEnteredValue": "Follow-up Sent"
                        }]
                    },
                    "format": {
                        "backgroundColor": {
                            "red": 1.0,
                            "green": 0.92,
                            "blue": 0.8  # Light orange
                        },
                        "textFormat": {
                            "foregroundColor": {
                                "red": 0.85,
                                "green": 0.55,
                                "blue": 0.0
                            },
                            "bold": True
                        }
                    }
                }
            },
            "index": 2
        }
    })
    
    # 5. RESPONSE RECEIVED COLUMN - Color-coded Yes/No
    # Green for "Yes"
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": 0,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 9,  # Response Received column (J)
                    "endColumnIndex": 10
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{
                            "userEnteredValue": "Yes"
                        }]
                    },
                    "format": {
                        "backgroundColor": {
                            "red": 0.72,
                            "green": 0.88,
                            "blue": 0.8  # Teal green
                        },
                        "textFormat": {
                            "foregroundColor": {
                                "red": 0.0,
                                "green": 0.5,
                                "blue": 0.4
                            },
                            "bold": True
                        }
                    }
                }
            },
            "index": 3
        }
    })
    
    # Red for "No"
    requests.append({
        "addConditionalFormatRule": {
            "rule": {
                "ranges": [{
                    "sheetId": 0,
                    "startRowIndex": 1,
                    "endRowIndex": 1000,
                    "startColumnIndex": 9,
                    "endColumnIndex": 10
                }],
                "booleanRule": {
                    "condition": {
                        "type": "TEXT_EQ",
                        "values": [{
                            "userEnteredValue": "No"
                        }]
                    },
                    "format": {
                        "backgroundColor": {
                            "red": 1.0,
                            "green": 0.9,
                            "blue": 0.9  # Light red
                        },
                        "textFormat": {
                            "foregroundColor": {
                                "red": 0.8,
                                "green": 0.0,
                                "blue": 0.0
                            },
                            "bold": True
                        }
                    }
                }
            },
            "index": 4
        }
    })
    
    # 6. COLUMN WIDTHS - Optimize for readability
    column_widths = [
        (0, 180),   # Timestamp
        (1, 150),   # Applicant Name
        (2, 150),   # Passport/Document ID
        (3, 200),   # Contact
        (4, 140),   # Issue Type
        (5, 200),   # Email Address
        (6, 250),   # Reason/Details
        (7, 180),   # Status
        (8, 140),   # Follow-up Date
        (9, 150)    # Response Received
    ]
    
    for col_index, width in column_widths:
        requests.append({
            "updateDimensionProperties": {
                "range": {
                    "sheetId": 0,
                    "dimension": "COLUMNS",
                    "startIndex": col_index,
                    "endIndex": col_index + 1
                },
                "properties": {
                    "pixelSize": width
                },
                "fields": "pixelSize"
            }
        })
    
    # 7. BORDERS - Professional grid lines
    requests.append({
        "updateBorders": {
            "range": {
                "sheetId": 0,
                "startRowIndex": 0,
                "endRowIndex": 1000,
                "startColumnIndex": 0,
                "endColumnIndex": 10
            },
            "top": {
                "style": "SOLID",
                "width": 1,
                "color": {"red": 0.8, "green": 0.8, "blue": 0.8}
            },
            "bottom": {
                "style": "SOLID",
                "width": 1,
                "color": {"red": 0.8, "green": 0.8, "blue": 0.8}
            },
            "left": {
                "style": "SOLID",
                "width": 1,
                "color": {"red": 0.8, "green": 0.8, "blue": 0.8}
            },
            "right": {
                "style": "SOLID",
                "width": 1,
                "color": {"red": 0.8, "green": 0.8, "blue": 0.8}
            },
            "innerHorizontal": {
                "style": "SOLID",
                "width": 1,
                "color": {"red": 0.9, "green": 0.9, "blue": 0.9}
            },
            "innerVertical": {
                "style": "SOLID",
                "width": 1,
                "color": {"red": 0.9, "green": 0.9, "blue": 0.9}
            }
        }
    })
    
    # Execute all formatting requests
    body = {'requests': requests}
    
    try:
        response = service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id,
            body=body
        ).execute()
        
        print("✅ MODERN DESIGN APPLIED!")
        print()
        print("🎨 Styling Applied:")
        print("  ✓ Vibrant blue header with white text")
        print("  ✓ Frozen header row")
        print("  ✓ Alternating row colors (zebra striping)")
        print("  ✓ Color-coded Status column:")
        print("    - Green: 'Sent'")
        print("    - Orange: 'Follow-up Sent'")
        print("  ✓ Color-coded Response Received:")
        print("    - Green: 'Yes'")
        print("    - Red: 'No'")
        print("  ✓ Optimized column widths")
        print("  ✓ Professional borders")
        print()
        print(f"📊 Total updates: {len(requests)}")
        return True
    except Exception as e:
        print(f"❌ Error applying design: {e}")
        return False

if __name__ == "__main__":
    print("=" * 80)
    print("MODERNIZING GOOGLE SHEETS DESIGN")
    print("=" * 80)
    print()
    modernize_sheets_design()
