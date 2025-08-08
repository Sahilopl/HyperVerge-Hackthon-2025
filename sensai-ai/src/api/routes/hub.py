# adityavofficial-hyperverge-hackathon-2025/sensai-ai/src/api/routes/hub.py

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
from api.db import hub as hub_db
from api.models import (
    CreateHubRequest,
    Hub,
    CreatePostRequest,
    PostVoteRequest,
    Post,
    PostWithComments
)

router = APIRouter()

@router.post("/", response_model=Hub)
async def create_hub(request: CreateHubRequest) -> Hub:
    """
    Creates a new learning hub within an organization.
    """
    hub_id = await hub_db.create_hub(request.org_id, request.name, request.description)
    return {
        "id": hub_id,
        "name": request.name,
        "description": request.description
    }

@router.get("/organization/{org_id}", response_model=List[Hub])
async def get_hubs_for_organization(org_id: int) -> List[Hub]:
    """
    Retrieves all learning hubs for a specific organization.
    """
    return await hub_db.get_hubs_by_org(org_id)
@router.get("/{hub_id}/posts", response_model=List[Post])
async def get_posts_for_hub(hub_id: int) -> List[Post]:
    """
    Retrieves all top-level posts (threads, questions, notes) for a specific hub.
    """
    try:
        posts = await hub_db.get_posts_by_hub(hub_id)
        # Manually add hub_id to each post dictionary if it's missing.
        for post in posts:
            if 'hub_id' not in post:
                post['hub_id'] = hub_id
        return posts
    except Exception as e:
        # Log the error for debugging
        print(f"Error fetching posts for hub {hub_id}: {e}")

@router.post("/posts", response_model=Dict[str, int])
async def create_post(request: CreatePostRequest) -> Dict[str, int]:
    """
    Creates a new post or a reply within a hub, supporting polls and QnA.
    """
    post_id = await hub_db.create_post(
        request.hub_id,
        request.user_id,
        request.title,
        request.content,
        str(request.post_type),
        request.parent_id,
        # Poll parameters
        request.poll_options,
        request.poll_duration_days,
        request.allow_multiple_answers,
        # QnA parameters
        request.category,
        request.tags
    )
    return {"id": post_id}

@router.get("/posts/{post_id}", response_model=PostWithComments)
async def get_post(post_id: int) -> PostWithComments:
    """
    Retrieves a single post along with its details and all associated comments.
    """
    post_details = await hub_db.get_post_with_details(post_id)
    if not post_details:
        raise HTTPException(status_code=404, detail="Post not found")

    # The following block is removed as hub_db.get_post_by_id does not exist.
    # The root cause is likely in hub_db.get_post_with_details not returning
    # all required fields, which should be fixed there.
    if 'hub_id' not in post_details:
        # Workaround: Fetch hub_id separately if not present.
        # A better long-term fix is to correct the get_post_with_details function.
        hub_id = await hub_db.get_hub_id_for_post(post_id)
        if hub_id is None:
             raise HTTPException(status_code=404, detail="Could not find hub for post")
        post_details['hub_id'] = hub_id

    # Propagate hub_id to comments and set a default post_type if missing.
    if post_details.get('comments'):
        for comment in post_details['comments']:
            comment.setdefault('hub_id', post_details['hub_id'])
            comment.setdefault('post_type', 'reply')

    return post_details


@router.post("/posts/{post_id}/vote", response_model=Dict[str, bool])
async def vote_on_post(post_id: int, request: PostVoteRequest) -> Dict[str, bool]:
    """
    Allows a user to cast a vote on a post (e.g., mark as helpful).
    """
    await hub_db.add_vote_to_post(post_id, request.user_id, request.vote_type, request.is_comment)
    return {"success": True}
@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: int):
    """
    Deletes a post or a comment by its ID.
    """
    await hub_db.delete_post(post_id)
    return


@router.post("/polls/{post_id}/vote", response_model=Dict[str, bool])
async def vote_on_poll(post_id: int, request: Dict[str, Any]):
    """
    Allows a user to vote on poll options.
    """
    user_id = request["user_id"]
    option_ids = request["option_ids"]  # List of option IDs
    
    await hub_db.vote_on_poll(post_id, user_id, option_ids)
    return {"success": True}


@router.get("/polls/{post_id}/votes/{user_id}", response_model=Dict[str, List[int]])
async def get_user_poll_votes(post_id: int, user_id: int):
    """
    Gets the options a user has voted for in a poll.
    """
    votes = await hub_db.get_user_poll_votes(post_id, user_id)
    return {"option_ids": votes}


@router.post("/questions/{post_id}/answer", response_model=Dict[str, bool])
async def mark_question_answered(post_id: int, request: Dict[str, Any]):
    """
    Marks a question as answered and optionally sets the accepted answer.
    """
    accepted_answer_id = request.get("accepted_answer_id")
    
    # Update the question post to mark as answered
    from api.utils.db import execute_db_operation
    from api.config import posts_table_name
    
    await execute_db_operation(
        f"UPDATE {posts_table_name} SET is_answered = ?, accepted_answer_id = ? WHERE id = ?",
        (True, accepted_answer_id, post_id)
    )
    
    return {"success": True}