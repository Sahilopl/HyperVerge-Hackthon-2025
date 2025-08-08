import os
from os.path import exists
from api.models import LeaderboardViewType, TaskInputType, TaskAIResponseType, TaskType

if exists("/appdata"):
    data_root_dir = "/appdata"
    root_dir = "/demo"
    log_dir = "/appdata/logs"
else:
    root_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(root_dir)

    data_root_dir = f"{parent_dir}/db"
    log_dir = f"{parent_dir}/logs"

if not exists(data_root_dir):
    os.makedirs(data_root_dir)

if not exists(log_dir):
    os.makedirs(log_dir)


sqlite_db_path = f"{data_root_dir}/db.sqlite"
log_file_path = f"{log_dir}/backend.log"

chat_history_table_name = "chat_history"
tasks_table_name = "tasks"
questions_table_name = "questions"
blocks_table_name = "blocks"
tests_table_name = "tests"
cohorts_table_name = "cohorts"
course_tasks_table_name = "course_tasks"
course_milestones_table_name = "course_milestones"
courses_table_name = "courses"
course_cohorts_table_name = "course_cohorts"
task_scoring_criteria_table_name = "task_scoring_criteria"
groups_table_name = "groups"
user_cohorts_table_name = "user_cohorts"
user_groups_table_name = "user_groups"
milestones_table_name = "milestones"
tags_table_name = "tags"
task_tags_table_name = "task_tags"
users_table_name = "users"
badges_table_name = "badges"
cv_review_usage_table_name = "cv_review_usage"
organizations_table_name = "organizations"
user_organizations_table_name = "user_organizations"
task_completions_table_name = "task_completions"
scorecards_table_name = "scorecards"
question_scorecards_table_name = "question_scorecards"
group_role_learner = "learner"
group_role_mentor = "mentor"
course_generation_jobs_table_name = "course_generation_jobs"
task_generation_jobs_table_name = "task_generation_jobs"
org_api_keys_table_name = "org_api_keys"
code_drafts_table_name = "code_drafts"

hubs_table_name = "hubs"
posts_table_name = "posts"
post_votes_table_name = "post_votes"
post_links_table_name = "post_links"
poll_options_table_name = "poll_options"
poll_votes_table_name = "poll_votes"
post_tags_table_name = "post_tags"
user_reputation_table_name = "user_reputation"
post_reports_table_name = "post_reports"
moderation_actions_table_name = "moderation_actions"
post_task_links_table_name = "post_task_links"
post_skill_links_table_name = "post_skill_links"
post_badge_links_table_name = "post_badge_links"
user_follows_table_name = "user_follows"
hub_subscriptions_table_name = "hub_subscriptions"

UPLOAD_FOLDER_NAME = "uploads"

uncategorized_milestone_name = "[UNASSIGNED]"
uncategorized_milestone_color = "#808080"

openai_plan_to_model_name = {
    "reasoning": "o3-mini-2025-01-31",
    "text": "gpt-4.1-2025-04-14",
    "text-mini": "gpt-4.1-mini-2025-04-14",
    "audio": "gpt-4o-audio-preview-2024-12-17",
    "router": "gpt-4.1-mini-2025-04-14",
}
