#!/usr/bin/env python3
"""
Startup script for the backend API server.
"""
import os
import sys
import uvicorn

# Add src directory to Python path
src_dir = os.path.join(os.path.dirname(__file__), "src")
sys.path.insert(0, src_dir)

# Change to src directory for proper module imports
os.chdir(src_dir)

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        reload_dirs=[src_dir]
    )
