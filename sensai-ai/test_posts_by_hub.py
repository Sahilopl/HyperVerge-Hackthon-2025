#!/usr/bin/env python3
"""
Debug script for get_posts_by_hub functionality
"""
import sys
import os
import asyncio

# Add the src directory to the Python path
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

# Change to src directory
os.chdir(src_dir)

async def test_get_posts_by_hub():
    """Test the get_posts_by_hub function directly"""
    try:
        from api.db.enhanced_hub import get_posts_by_hub
        print("Testing get_posts_by_hub function...")
        
        result = await get_posts_by_hub(hub_id=1)
        print(f"Posts result: {result}")
        
    except Exception as e:
        print(f"Error testing get_posts_by_hub: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_get_posts_by_hub())
