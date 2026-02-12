---
description: How to update the Agent's Contact Information
---

# Updating Agent Contact Information

The agent's contact details (Name, Email, Phone, Address) are stored in a simple JSON configuration file. To update them, follow these steps:

1.  **Open the Configuration File**:
    - Locate `agent_config.json` in the root directory: `/Users/berry/Antigravity/Australia Agent/agent_config.json`

2.  **Edit the JSON Definition**:
    - Update the values inside the quotes.
    - **Note**: Ensure you keep the JSON format valid (double quotes, commas between items).

    ```json
    {
        "agent_name": "Your New Name",
        "email": "new.email@example.com",
        "phone": "+61 400 123 456",
        "address": "New Address, Sydney, NSW",
        "website": "www.new-website.com"
    }
    ```

3.  **Restart the System**:
    - For the changes to take effect, you must restart the application.
    - Stop the current process (Ctrl+C).
    - Run `./venv/bin/python3 run_system.py` again.

// turbo
4.  **Verify Changes**:
    - Open the Chat Widget.
    - Ask: "What are your contact details?"
    - The AI should respond with the new information.
