import subprocess
import time
import os
import sys

def cleanup_port(port):
    """Kill any process using the specified port"""
    try:
        result = subprocess.run(
            f"lsof -ti:{port}",
            shell=True,
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    os.kill(int(pid), 9)
                    print(f"🧹 Cleaned up process {pid} on port {port}")
                except:
                    pass
    except:
        pass

def run_system():
    print("🚀 Starting Australia Visa AI Agent System...")
    
    # Clean up port 5001 before starting
    cleanup_port(5001)
    
    # 1. Start Flask Dashboard
    print("📊 Launching Web Dashboard on http://localhost:5001...")
    dashboard_process = subprocess.Popen(
        ["./venv/bin/python3", "-u", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # 2. Give dashboard a moment to start
    time.sleep(2)
    
    # 3. Start Visa Agent
    print("🤖 Launching AI Agent in Polling Mode...")
    agent_process = subprocess.Popen(
        ["./venv/bin/python3", "-u", "core/agent.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # 4. Start Notification Scheduler
    print("⏰ Launching Notification Scheduler...")
    scheduler_process = subprocess.Popen(
        ["./venv/bin/python3", "-u", "scheduled_notifications.py", "--daemon"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    print("\n✅ System is running!")
    print("Press Ctrl+C to stop all processes.\n")
    
    processes = {
        "DASHBOARD": dashboard_process,
        "AGENT": agent_process,
        "SCHEDULER": scheduler_process
    }
    
    try:
        while True:
            # Check each process and restart if crashed
            for name, proc in list(processes.items()):
                # Read and print output
                line = proc.stdout.readline()
                if line:
                    print(f"[{name}] {line.strip()}")
                
                # Check if process has died
                if proc.poll() is not None:
                    print(f"\n⚠️  WARNING: {name} process died! Restarting...")
                    
                    # Restart based on process type
                    if name == "DASHBOARD":
                        processes[name] = subprocess.Popen(
                            ["./venv/bin/python3", "-u", "app.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )
                    elif name == "AGENT":
                        processes[name] = subprocess.Popen(
                            ["./venv/bin/python3", "-u", "core/agent.py"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )
                    elif name == "SCHEDULER":
                        processes[name] = subprocess.Popen(
                            ["./venv/bin/python3", "-u", "scheduled_notifications.py", "--daemon"],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True
                        )
                    
                    print(f"✅ {name} restarted successfully")
                    
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nStopping system...")
        for name, proc in processes.items():
            proc.terminate()
        print("Done.")

if __name__ == "__main__":
    run_system()
