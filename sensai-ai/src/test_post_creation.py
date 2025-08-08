"""
Test script to debug post creation issue
"""
import asyncio
import aiohttp
import json

async def test_post_creation():
    """Test post creation endpoint."""
    # Test both regular and enhanced endpoints
    regular_url = "http://127.0.0.1:8003/hubs/posts"
    enhanced_url = "http://127.0.0.1:8003/enhanced-hubs/posts"
    
    test_data = {
        "hub_id": 1,
        "user_id": 1,
        "title": "Test Post",
        "content": "This is a test post to debug the frontend issue",
        "post_type": "thread"
    }
    
    # Test enhanced endpoint first
    print(f"Testing Enhanced POST to {enhanced_url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(enhanced_url, json=test_data) as response:
                print(f"Enhanced Response Status: {response.status}")
                text = await response.text()
                print(f"Enhanced Response Text: {text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(text)
                        print(f"Enhanced Response JSON: {json.dumps(data, indent=2)}")
                    except:
                        print("Could not parse enhanced response as JSON")
                else:
                    print("Enhanced request failed!")
                    
        except Exception as e:
            print(f"Enhanced Error: {e}")
    
    print("\n" + "="*50 + "\n")
    
    # Now test regular endpoint
    url = regular_url
    
    print(f"Testing POST to {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=test_data) as response:
                print(f"Response Status: {response.status}")
                text = await response.text()
                print(f"Response Text: {text}")
                
                if response.status == 200:
                    try:
                        data = json.loads(text)
                        print(f"Response JSON: {json.dumps(data, indent=2)}")
                    except:
                        print("Could not parse response as JSON")
                else:
                    print("Request failed!")
                    
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_post_creation())
