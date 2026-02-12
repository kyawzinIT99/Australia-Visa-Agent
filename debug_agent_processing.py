import os
import sys
from dotenv import load_dotenv

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from core.agent import VisaAgent
from services.database_service import init_db

def debug_agent_run():
    print("🐞 Starting Debug Agent Run...")
    
    # Initialize DB (just in case)
    init_db()
    
    try:
        agent = VisaAgent()
        print("✅ Agent initialized.")
        
        print("▶️ Running agent.run_once()...")
        agent.run_once()
        print("✅ Agent run complete.")
        
    except Exception as e:
        print(f"❌ Error during agent execution: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_agent_run()
