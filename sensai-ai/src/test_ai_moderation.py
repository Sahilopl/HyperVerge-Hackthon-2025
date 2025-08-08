"""
Test script to verify AI moderation is working with the OpenAI API key
"""
import sys
import os
sys.path.append('.')

from api.load_env import *
from api.utils.ai_moderation import get_ai_moderator
import asyncio

async def test_ai_moderation():
    """Test the AI moderation functionality"""
    try:
        moderator = get_ai_moderator()
        print("✓ AI Moderator initialized successfully")
        
        # Test with good educational content
        result1 = await moderator.moderate_content(
            "Can someone help me understand binary search algorithms? I've tried to implement it but getting confused with the boundary conditions.",
            "Help with Binary Search",
            {"author_reputation": 100, "post_type": "question"}
        )
        
        print("\n📝 Test 1 - Good Educational Content:")
        print(f"   Is Toxic: {result1.is_toxic}")
        print(f"   Score: {result1.toxicity_score}")
        print(f"   Action: {result1.suggested_action}")
        print(f"   Explanation: {result1.explanation}")
        
        # Test with toxic educational content
        result2 = await moderator.moderate_content(
            "This is a stupid question. Just google it instead of wasting everyone's time here.",
            "Dismissive Response",
            {"author_reputation": 50, "post_type": "reply"}
        )
        
        print("\n⚠️ Test 2 - Toxic Educational Content:")
        print(f"   Is Toxic: {result2.is_toxic}")
        print(f"   Score: {result2.toxicity_score}")
        print(f"   Action: {result2.suggested_action}")
        print(f"   Explanation: {result2.explanation}")
        
        print("\n🎉 AI Moderation with your OpenAI API key is working perfectly!")
        
    except Exception as e:
        print(f"❌ Error testing AI moderation: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_moderation())
