"""
Enhanced Learning Hubs & Forums API routes with comprehensive features.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
from api.models import (
    CreatePostRequest, Post, Hub, EnhancedPost, EnhancedHub,
    CreateReportRequest, ModerationRequest, LinkPostRequest,
    FollowUserRequest, SubscribeHubRequest, SearchRequest,
    PersonalizedFeedRequest, AIModerationResult, UserReputation
)
from api.db.enhanced_hub import (
    get_user_reputation, create_post_with_moderation, moderate_post_content,
    link_post_to_task, link_post_to_skill, link_post_to_badge, get_post_links,
    apply_moderation_action, report_post, search_posts, get_personalized_feed,
    follow_user, unfollow_user, subscribe_to_hub, unsubscribe_from_hub,
    update_hub_stats, get_leaderboard, get_posts_by_hub
)
from api.db import hub as hub_db
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Enhanced Post Creation with AI Moderation
@router.post("/posts", response_model=Dict[str, Any])
async def create_enhanced_post(request: CreatePostRequest):
    """
    Create a new post with AI moderation, comprehensive features, and content linking.
    """
    try:
        post_id = await create_post_with_moderation(
            hub_id=request.hub_id,
            user_id=request.user_id,
            title=request.title,
            content=request.content,
            post_type=request.post_type,
            parent_id=request.parent_id,
            poll_options=request.poll_options,
            poll_duration_days=request.poll_duration_days,
            allow_multiple_answers=request.allow_multiple_answers,
            category=request.category,
            tags=request.tags
        )
        
        return {
            "id": post_id,
            "status": "created",
            "message": "Post created successfully and processed through AI moderation"
        }
    except Exception as e:
        logger.error(f"Error creating post: {e}")
        raise HTTPException(status_code=500, detail="Failed to create post")

# AI Moderation Endpoint
@router.post("/posts/{post_id}/moderate", response_model=AIModerationResult)
async def moderate_post(post_id: int):
    """
    Run AI moderation on an existing post.
    """
    try:
        # Get post details
        post = await hub_db.get_post(post_id)
        if not post:
            raise HTTPException(status_code=404, detail="Post not found")
        
        moderation_result = await moderate_post_content(
            post_id=post_id,
            title=post.get("title", ""),
            content=post["content"],
            author_id=post["user_id"],
            post_type=post["post_type"]
        )
        
        return AIModerationResult(
            is_toxic=moderation_result["moderation_status"] != "approved",
            toxicity_score=moderation_result.get("ai_moderation_score", 0.0),
            categories=["ai_flagged"] if moderation_result["moderation_status"] == "flagged" else [],
            suggested_action=moderation_result["moderation_status"],
            explanation=moderation_result["explanation"],
            requires_human_review=moderation_result["requires_human_review"]
        )
    except Exception as e:
        logger.error(f"Error moderating post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to moderate post")

# Content Linking
@router.post("/posts/{post_id}/link")
async def link_post_to_content(post_id: int, request: LinkPostRequest):
    """
    Link a post to tasks, skills, or badges for better knowledge mapping.
    """
    try:
        if request.link_type == "task":
            await link_post_to_task(post_id, request.link_id)
        elif request.link_type == "skill":
            await link_post_to_skill(post_id, str(request.link_id))  # Assuming skill name passed as ID
        elif request.link_type == "badge":
            await link_post_to_badge(post_id, request.link_id)
        else:
            raise HTTPException(status_code=400, detail="Invalid link type")
        
        return {"status": "success", "message": f"Post linked to {request.link_type}"}
    except Exception as e:
        logger.error(f"Error linking post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to link post")

@router.get("/posts/{post_id}/links", response_model=Dict[str, List[Dict]])
async def get_post_content_links(post_id: int):
    """
    Get all content links (tasks, skills, badges) for a post.
    """
    try:
        return await get_post_links(post_id)
    except Exception as e:
        logger.error(f"Error getting post links for {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get post links")

# Moderation and Reporting
@router.post("/posts/{post_id}/report")
async def report_post_endpoint(post_id: int, request: CreateReportRequest):
    """
    Report a post for moderation review.
    """
    try:
        report_id = await report_post(
            post_id=post_id,
            reporter_id=request.reporter_id,
            reason=request.reason,
            description=request.description
        )
        return {"id": report_id, "status": "reported", "message": "Post reported successfully"}
    except Exception as e:
        logger.error(f"Error reporting post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to report post")

@router.post("/posts/{post_id}/moderate")
async def apply_moderation(post_id: int, request: ModerationRequest):
    """
    Apply moderation action to a post (requires moderator privileges).
    """
    try:
        await apply_moderation_action(
            post_id=post_id,
            moderator_id=request.moderator_id,
            action_type=request.action_type,
            reason=request.reason,
            is_ai_moderated=False
        )
        return {"status": "success", "message": f"Moderation action '{request.action_type}' applied"}
    except Exception as e:
        logger.error(f"Error applying moderation to post {post_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to apply moderation")

# Advanced Search
@router.post("/search", response_model=List[Dict[str, Any]])
async def search_forum_content(request: SearchRequest):
    """
    Advanced search across all forum content with filtering and sorting.
    """
    try:
        logger.info(f"Search request: {request}")
        results = await search_posts(
            query=request.query,
            hub_ids=request.hub_ids,
            post_types=request.post_types,
            tags=request.tags,
            category=request.category,
            author_id=request.author_id,
            date_from=request.date_from,
            date_to=request.date_to,
            sort_by=request.sort_by,
            limit=request.limit,
            offset=request.offset
        )
        logger.info(f"Search results: {len(results)} posts found")
        return results
    except Exception as e:
        logger.error(f"Error searching posts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

# Personalized Feeds
@router.post("/feed", response_model=List[Dict[str, Any]])
async def get_personalized_feed_endpoint(request: PersonalizedFeedRequest):
    """
    Get personalized feed based on user preferences and activity.
    """
    try:
        feed = await get_personalized_feed(
            user_id=request.user_id,
            feed_type=request.feed_type,
            limit=request.limit,
            offset=request.offset
        )
        return feed
    except Exception as e:
        logger.error(f"Error getting personalized feed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get feed")

# User Reputation
@router.get("/users/{user_id}/reputation", response_model=Dict[str, int])
async def get_user_reputation_endpoint(user_id: int, hub_id: Optional[int] = Query(None)):
    """
    Get user reputation score and breakdown.
    """
    try:
        reputation = await get_user_reputation(user_id, hub_id)
        return reputation
    except Exception as e:
        logger.error(f"Error getting user reputation: {e}")
        raise HTTPException(status_code=500, detail="Failed to get reputation")

# User Following
@router.post("/users/follow")
async def follow_user_endpoint(request: FollowUserRequest):
    """
    Follow another user to see their posts in your feed.
    """
    try:
        await follow_user(request.follower_id, request.following_id)
        return {"status": "success", "message": "User followed successfully"}
    except Exception as e:
        logger.error(f"Error following user: {e}")
        raise HTTPException(status_code=500, detail="Failed to follow user")

@router.delete("/users/{follower_id}/follow/{following_id}")
async def unfollow_user_endpoint(follower_id: int, following_id: int):
    """
    Unfollow a user.
    """
    try:
        await unfollow_user(follower_id, following_id)
        return {"status": "success", "message": "User unfollowed successfully"}
    except Exception as e:
        logger.error(f"Error unfollowing user: {e}")
        raise HTTPException(status_code=500, detail="Failed to unfollow user")

# Hub Subscriptions
@router.post("/hubs/subscribe")
async def subscribe_to_hub_endpoint(request: SubscribeHubRequest):
    """
    Subscribe to a hub to receive notifications and see posts in feed.
    """
    try:
        await subscribe_to_hub(request.user_id, request.hub_id)
        return {"status": "success", "message": "Subscribed to hub successfully"}
    except Exception as e:
        logger.error(f"Error subscribing to hub: {e}")
        raise HTTPException(status_code=500, detail="Failed to subscribe")

@router.delete("/hubs/{hub_id}/subscribe/{user_id}")
async def unsubscribe_from_hub_endpoint(hub_id: int, user_id: int):
    """
    Unsubscribe from a hub.
    """
    try:
        await unsubscribe_from_hub(user_id, hub_id)
        return {"status": "success", "message": "Unsubscribed from hub successfully"}
    except Exception as e:
        logger.error(f"Error unsubscribing from hub: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsubscribe")

# Enhanced Hub Stats
@router.get("/hubs/{hub_id}/stats", response_model=Dict[str, Any])
async def get_hub_statistics(hub_id: int):
    """
    Get comprehensive hub statistics including activity metrics.
    """
    try:
        await update_hub_stats(hub_id)  # Refresh stats
        hub = await hub_db.get_hub(hub_id)
        
        if not hub:
            raise HTTPException(status_code=404, detail="Hub not found")
        
        return {
            "id": hub_id,
            "post_count": hub.get("post_count", 0),
            "subscriber_count": hub.get("subscriber_count", 0),
            "active_today": hub.get("active_today", 0),
            "topics": hub.get("topics", []),
            "moderators": hub.get("moderators", [])
        }
    except Exception as e:
        logger.error(f"Error getting hub statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get hub stats")

# Quick Actions for Learning Integration
@router.post("/posts/{post_id}/mark-helpful")
async def mark_post_helpful(post_id: int, user_id: int):
    """
    Mark a post as helpful (for reputation system).
    """
    try:
        # This would typically be handled through the voting system
        # but we can add a specific "helpful" action
        await hub_db.vote_on_post(post_id, user_id, "up", is_comment=False)
        
        # Update author reputation
        post = await hub_db.get_post(post_id)
        if post:
            from api.db.enhanced_hub import update_user_reputation
            await update_user_reputation(post["user_id"], post["hub_id"], "helpful_answers", points=10)
        
        return {"status": "success", "message": "Post marked as helpful"}
    except Exception as e:
        logger.error(f"Error marking post helpful: {e}")
        raise HTTPException(status_code=500, detail="Failed to mark post helpful")

@router.post("/posts/{post_id}/accept-answer")
async def accept_answer(post_id: int, answer_id: int, user_id: int):
    """
    Accept an answer to a question (for QnA functionality).
    """
    try:
        # Check if user is the question author
        question = await hub_db.get_post(post_id)
        if not question or question["user_id"] != user_id:
            raise HTTPException(status_code=403, detail="Only question author can accept answers")
        
        # Update question with accepted answer
        await hub_db.update_post_accepted_answer(post_id, answer_id)
        
        # Update answer author's reputation
        answer = await hub_db.get_post(answer_id)
        if answer:
            from api.db.enhanced_hub import update_user_reputation
            await update_user_reputation(answer["user_id"], answer["hub_id"], "accepted_answers", points=25)
        
        return {"status": "success", "message": "Answer accepted successfully"}
    except Exception as e:
        logger.error(f"Error accepting answer: {e}")
        raise HTTPException(status_code=500, detail="Failed to accept answer")

# Trending and Featured Content
@router.get("/hubs/{hub_id}/trending", response_model=List[Dict[str, Any]])
async def get_trending_posts(
    hub_id: int,
    timeframe: str = Query("week", regex="^(day|week|month)$"),
    limit: int = Query(10, ge=1, le=50)
):
    """
    Get trending posts in a hub based on engagement metrics.
    """
    try:
        # This would use the personalized feed with trending type, filtered by hub
        feed_request = PersonalizedFeedRequest(
            user_id=0,  # Anonymous trending
            feed_type="trending",
            limit=limit,
            offset=0
        )
        
        trending_posts = await get_personalized_feed(
            user_id=0,
            feed_type="trending",
            limit=limit,
            offset=0
        )
        
        # Filter by hub_id
        hub_trending = [post for post in trending_posts if post["hub_id"] == hub_id]
        
        return hub_trending
    except Exception as e:
        logger.error(f"Error getting trending posts: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trending posts")


# Leaderboard endpoint
@router.get("/leaderboard", response_model=List[Dict[str, Any]])
async def get_user_leaderboard(
    limit: int = Query(10, ge=1, le=100),
    time_period: str = Query("all_time", regex="^(all_time|month|week)$")
):
    """
    Get user leaderboard based on reputation and activity.
    """
    try:
        leaderboard = await get_leaderboard(limit=limit, time_period=time_period)
        return leaderboard
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get leaderboard")


# Get posts by hub ID endpoint
@router.get("/hubs/{hub_id}/posts", response_model=List[Dict[str, Any]])
async def get_hub_posts(hub_id: int):
    """
    Get all posts for a specific hub with enhanced features.
    """
    try:
        posts = await get_posts_by_hub(hub_id)
        return posts
    except Exception as e:
        logger.error(f"Error getting posts for hub {hub_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get hub posts")
