"""
Debug search functionality specifically
"""
import asyncio
import aiohttp
import json

async def test_search_debug():
    """Test search endpoint with detailed error info."""
    url = "http://127.0.0.1:8003/enhanced-hubs/search"
    
    search_data = {
        "query": "test",
        "limit": 10,
        "offset": 0,
        "sort_by": "relevance"
    }
    
    print(f"Testing Search POST to {url}")
    print(f"Data: {json.dumps(search_data, indent=2)}")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=search_data) as response:
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
                    print("Search request failed!")
                    
        except Exception as e:
            print(f"Search Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_search_debug())
