#!/usr/bin/env python3
import sys
import os

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import and run the app
if __name__ == "__main__":
    import uvicorn
    from api.main import app
    
    print("Starting SensAI Backend Server...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
