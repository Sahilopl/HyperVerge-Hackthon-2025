#!/usr/bin/env python3
"""
Debug script for leaderboard functionality
"""
import sys
import os
import asyncio

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Change to src directory
os.chdir(src_dir)

async def test_leaderboard():
    """Test the leaderboard function directly"""
    try:
        from api.db.enhanced_hub import get_leaderboard
        print("Testing leaderboard function...")
        
        result = await get_leaderboard(limit=5)
        print(f"Leaderboard result: {result}")
        
    except Exception as e:
        print(f"Error testing leaderboard: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_leaderboard())
