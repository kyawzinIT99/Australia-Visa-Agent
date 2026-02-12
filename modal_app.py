import modal
import os

# Create Modal app
app = modal.App("australia-visa-agent")

# Define the image with all dependencies
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "openai",
        "sqlalchemy",
        "python-dotenv",
        "cryptography",
        "PyPDF2",
        "flask",
        "rarfile",
        "tavily-python",
        "pymupdf",
        "schedule",
        "python-dateutil",
    )
    .add_local_dir(".", remote_path="/root")
)

# Create a persistent volume for database and token storage
volume = modal.Volume.from_name("visa-agent-data", create_if_missing=True)

def setup_gcp_credentials():
    """Write GCP credentials from env var to file"""
    import json
    creds_json = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_json:
        with open("/root/gcp-service-account.json", "w") as f:
            f.write(creds_json)
        print("✅ GCP credentials file created")

@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("visa-agent-env"),
        modal.Secret.from_name("gcp-credentials")
    ],
    volumes={"/data": volume},
    min_containers=1,
    timeout=3600,
)
@modal.wsgi_app()
def web():
    """Flask web application endpoint"""
    import sys
    sys.path.insert(0, "/root")
    
    # Setup GCP credentials file
    setup_gcp_credentials()
    
    # Ensure data directory exists
    os.makedirs("/data", exist_ok=True)
    
    # Override DATABASE_URL to use persistent volume
    os.environ["DATABASE_URL"] = "sqlite:////data/visa_agent.db"
    
    # Import and return Flask app
    from app import app as flask_app
    return flask_app


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("visa-agent-env"),
        modal.Secret.from_name("gcp-credentials")
    ],
    volumes={"/data": volume},
    schedule=modal.Cron("*/5 * * * *"),  # Run every 5 minutes
    timeout=600,
)
def agent_worker():
    """Background agent that processes documents"""
    import sys
    sys.path.insert(0, "/root")
    
    # Setup GCP credentials file
    setup_gcp_credentials()
    
    # Ensure data directory exists
    os.makedirs("/data", exist_ok=True)
    
    # Override DATABASE_URL to use persistent volume
    os.environ["DATABASE_URL"] = "sqlite:////data/visa_agent.db"
    
    # Import and run agent
    from core.agent import VisaAgent
    from services.database_service import init_db
    
    print("🤖 Starting agent worker...")
    init_db()
    agent = VisaAgent()
    agent.run_once()
    print("✅ Agent worker completed")


@app.function(
    image=image,
    secrets=[
        modal.Secret.from_name("visa-agent-env"),
        modal.Secret.from_name("gcp-credentials")
    ],
    volumes={"/data": volume},
    schedule=modal.Cron("0 */6 * * *"),  # Run every 6 hours
    timeout=600,
)
def scheduler_worker():
    """Background scheduler for notifications"""
    import sys
    sys.path.insert(0, "/root")
    
    # Setup GCP credentials file
    setup_gcp_credentials()
    
    # Ensure data directory exists
    os.makedirs("/data", exist_ok=True)
    
    # Override DATABASE_URL to use persistent volume
    os.environ["DATABASE_URL"] = "sqlite:////data/visa_agent.db"
    
    # Import and run scheduler
    from scheduled_notifications import run_all_checks
    
    print("⏰ Starting scheduler worker...")
    run_all_checks()
    print("✅ Scheduler worker completed")


@app.local_entrypoint()
def main():
    """Local entrypoint for testing"""
    print("🚀 Testing Modal deployment...")
    agent_worker.remote()
    print("✅ Test completed")
