# 🚀 Quick Start Guide

## Starting the System

### Option 1: Using the start script (Recommended)
```bash
./start.sh
```

### Option 2: Manual start
```bash
source venv/bin/activate
python3 run_system.py
```

## Checking System Health

```bash
source venv/bin/activate
python3 monitor_system.py
```

## What You'll See

The system runs 3 components:
- **[DASHBOARD]** - Web interface at http://localhost:5001
- **[AGENT]** - Document processing (checks Google Drive every 30 seconds)
- **[SCHEDULER]** - Notification system (checks every 6 hours)

## Features

✅ **Auto-restart** - If any component crashes, it automatically restarts  
✅ **Detailed logging** - Every action is logged with timestamps  
✅ **Self-healing** - No manual intervention needed  

## Stopping the System

Press `Ctrl+C` in the terminal where the system is running.

## Troubleshooting

If you see "Port 5001 is in use":
```bash
lsof -ti:5001 | xargs kill -9
```

Then restart the system.
