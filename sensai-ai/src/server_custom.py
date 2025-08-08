#!/usr/bin/env python3
"""
Custom server script to run the FastAPI backend on port 8002.
"""
import uvicorn
from api.main import app

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        reload_dirs=["src"]
    )
