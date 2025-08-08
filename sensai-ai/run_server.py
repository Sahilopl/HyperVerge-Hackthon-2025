#!/usr/bin/env python3
"""
Simple server runner script for the AI API
"""
import sys
import os
import uvicorn

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Change to src directory
os.chdir(src_dir)

# Import and run the app
if __name__ == "__main__":
    # Import after setting path
    from api.main import app
    
    print("Starting AI Learning Hub API server...")
    print(f"Server will be available at http://127.0.0.1:8003")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8003,
        reload=True,
        log_level="info"
    )
