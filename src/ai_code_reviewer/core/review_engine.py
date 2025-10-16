"""Core review processing logic."""

import logging
from typing import Any

from ai_code_reviewer.clients.bitbucket_client import BitbucketClient
from ai_code_reviewer.clients.email_client import send_mail
from ai_code_reviewer.clients.llm_client import LLMClient
from ai_code_reviewer.core.config import Config
from ai_code_reviewer.core.email_formatter import format_review_to_html
from ai_code_reviewer.db.database import get_db_session
from ai_code_reviewer.db.repository import ReviewRepository


logger = logging.getLogger(__name__)


async def save_review_to_database(
    review_type: str,
    trigger_type: str,
    project_key: str,
    repo_slug: str,
    diff_content: str,
    review_feedback: str,
    commit_id: str | None = None,
    pr_id: int | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
    email_recipients: list[str] | None = None,
    email_sent: bool = False,
) -> int | None:
    """Save review record to database. Returns the review record ID if successful, None otherwise."""
    try:
        async with get_db_session() as session:
            repo = ReviewRepository(session)
            record = await repo.create_review_record(
                review_type=review_type,
                trigger_type=trigger_type,
                project_key=project_key,
                repo_slug=repo_slug,
                diff_content=diff_content,
                review_feedback=review_feedback,
                commit_id=commit_id,
                pr_id=pr_id,
                author_name=author_name,
                author_email=author_email,
                email_recipients=email_recipients,
                email_sent=email_sent,
                llm_provider=Config.LLM_PROVIDER,
                llm_model=Config.LLM_MODEL,
            )
            record_id: int = record.id
            logger.info(f"Saved review record with ID: {record_id}")
            return record_id
    except Exception as e:
        logger.error(f"Error saving review to database: {str(e)}")
        return None


async def send_review_email(
    bitbucket_client: BitbucketClient,
    project_key: str,
    repo_slug: str,
    review: str,
    review_type: str = "AI Code Review",
    commit_id: str | None = None,
    pr_id: int | None = None,
) -> tuple[bool, str | None, str | None]:
    """Send review email to author. Returns (success, author_email, author_name) tuple."""
    try:
        author_email = None
        author_name = None
        subject_id = "Unknown"

        if commit_id:
            # Get commit info to extract author email
            commit_info = await bitbucket_client.get_commit_info(project_key, repo_slug, commit_id)
            if commit_info and commit_info.get("author"):
                author_data = commit_info["author"]
                author_email = author_data.get("emailAddress")
                author_name = author_data.get("displayName") or author_data.get("name")
                subject_id = f"Commit {commit_id[:8]}"

        elif pr_id:
            # Get PR info to extract author email
            pr_info = await bitbucket_client.get_pull_request_info(project_key, repo_slug, pr_id)
            if pr_info and pr_info.get("author") and pr_info["author"].get("user"):
                user_data = pr_info["author"]["user"]
                author_email = user_data.get("emailAddress")
                author_name = user_data.get("displayName") or user_data.get("name")
                subject_id = f"PR #{pr_id}"

        if not author_email:
            logger.warning(f"Could not get author email for {subject_id}, skipping email")
            return False, None, None

        # Create email subject
        subject = f"{review_type} - {subject_id}"

        # Format review as HTML
        html_body = format_review_to_html(f"🤖 **{review_type}**\n\n{review}")

        # Send email
        send_mail(
            to=author_email,
            cc="",  # No CC for now
            subject=subject,
            mailbody=html_body,
        )

        logger.info(f"Sent {review_type.lower()} email for {subject_id} to {author_email}")
        return True, author_email, author_name

    except Exception as e:
        logger.error(f"Error sending {review_type.lower()} email for {subject_id}: {str(e)}")
        return False, None, None


async def process_pull_request_review(
    bitbucket_client: BitbucketClient, llm_client: LLMClient, payload: dict[str, Any], is_manual: bool = False
):
    """Process pull request for AI review"""
    try:
        repository = payload["repository"]
        pull_request = payload["pullRequest"]

        project_key = repository["project"]["key"]
        repo_slug = repository["slug"]
        pr_id = pull_request["id"]

        logger.info(f"Processing PR review for {project_key}/{repo_slug}/pull-requests/{pr_id}")

        # Get pull request diff
        diff = await bitbucket_client.get_pull_request_diff(project_key, repo_slug, pr_id)

        if not diff or len(diff.strip()) == 0:
            logger.info(f"No diff found for PR {pr_id}, skipping review")
            return

        # Get AI review
        review = await llm_client.get_code_review(diff)

        if review and review.strip() != "No issues found.":
            # Comment out post_pull_request_comment for now
            # await bitbucket_client.post_pull_request_comment(
            #     project_key, repo_slug, pr_id, f"🤖 **AI Code Review**\n\n{review}"
            # )

            # Send review email
            review_type = "AI Code Review (Manual)" if is_manual else "AI Code Review"
            email_sent, author_email, author_name = await send_review_email(
                bitbucket_client, project_key, repo_slug, review, review_type, pr_id=pr_id
            )

            # Save to database
            await save_review_to_database(
                review_type="manual" if is_manual else "auto",
                trigger_type="pull_request",
                project_key=project_key,
                repo_slug=repo_slug,
                diff_content=diff,
                review_feedback=review,
                pr_id=pr_id,
                author_name=author_name,
                author_email=author_email,
                email_recipients=[author_email] if author_email else None,
                email_sent=email_sent,
            )

            logger.info(f"Processed AI review for PR {pr_id}")
        else:
            logger.info(f"No issues found in PR {pr_id}, no email sent")

    except Exception as e:
        logger.error(f"Error processing pull request review: {str(e)}")


async def process_commit_review(
    bitbucket_client: BitbucketClient, llm_client: LLMClient, payload: dict[str, Any], is_manual: bool = False
):
    """Process commit for AI review"""
    try:
        repository = payload["repository"]
        changes = payload.get("changes", [])

        if not changes:
            logger.info("No changes found in commit payload")
            return

        project_key = repository["project"]["key"]
        repo_slug = repository["slug"]

        for change in changes:
            commit_id = change["toHash"]

            logger.info(f"Processing commit review for {project_key}/{repo_slug}/commits/{commit_id}")

            # Get commit diff
            diff = await bitbucket_client.get_commit_diff(project_key, repo_slug, commit_id)

            if not diff or len(diff.strip()) == 0:
                logger.info(f"No diff found for commit {commit_id}, skipping review")
                continue

            # Get AI review
            review = await llm_client.get_code_review(diff)

            if review and review.strip() != "No issues found.":
                # Comment out post_commit_comment for now
                # await bitbucket_client.post_commit_comment(
                #     project_key, repo_slug, commit_id, f"🤖 **AI Code Review**\n\n{review}"
                # )

                # Send review email
                review_type = "AI Code Review (Manual)" if is_manual else "AI Code Review"
                email_sent, author_email, author_name = await send_review_email(
                    bitbucket_client, project_key, repo_slug, review, review_type, commit_id=commit_id
                )

                # Save to database
                await save_review_to_database(
                    review_type="manual" if is_manual else "auto",
                    trigger_type="commit",
                    project_key=project_key,
                    repo_slug=repo_slug,
                    diff_content=diff,
                    review_feedback=review,
                    commit_id=commit_id,
                    author_name=author_name,
                    author_email=author_email,
                    email_recipients=[author_email] if author_email else None,
                    email_sent=email_sent,
                )

                logger.info(f"Processed AI review for commit {commit_id}")
            else:
                logger.info(f"No issues found in commit {commit_id}, no email sent")

    except Exception as e:
        logger.error(f"Error processing commit review: {str(e)}")
