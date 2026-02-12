"""
Follow-up Date Parser
Converts dropdown values (e.g., "7 days") or custom dates to actual datetime objects
"""

from datetime import datetime, timedelta

def parse_followup_date(followup_value, reference_date=None):
    """
    Parse follow-up date from dropdown value or custom date
    
    Args:
        followup_value: String like "7 days", "2026-02-18", or "Custom"
        reference_date: Reference datetime (defaults to now)
    
    Returns:
        datetime object or None if invalid
    """
    if not followup_value:
        return None
    
    if reference_date is None:
        reference_date = datetime.now()
    
    followup_value = followup_value.strip()
    
    # Handle dropdown values like "7 days", "14 days", etc.
    if "day" in followup_value.lower():
        try:
            # Extract number from "X days"
            days = int(followup_value.split()[0])
            return reference_date + timedelta(days=days)
        except:
            pass
    
    # Handle "Custom" - return None to indicate staff needs to set it
    if followup_value.lower() == "custom":
        return None
    
    # Try to parse as actual date
    for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(followup_value.split()[0], fmt)
        except:
            continue
    
    return None

if __name__ == "__main__":
    # Test cases
    test_cases = [
        "7 days",
        "14 days",
        "2026-02-18",
        "02/18/2026",
        "Custom",
        "invalid"
    ]
    
    print("Testing follow-up date parser:")
    for test in test_cases:
        result = parse_followup_date(test)
        print(f"  '{test}' → {result}")
