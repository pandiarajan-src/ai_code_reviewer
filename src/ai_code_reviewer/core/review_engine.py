"""Core review processing logic."""

import logging
import traceback
from typing import Any

from ai_code_reviewer.clients.bitbucket_client import BitbucketClient
from ai_code_reviewer.clients.email_client import send_mail
from ai_code_reviewer.clients.llm_client import LLMClient
from ai_code_reviewer.core.config import Config
from ai_code_reviewer.core.email_formatter import format_review_to_html
from ai_code_reviewer.db.database import get_db_session
from ai_code_reviewer.db.repository import FailureLogRepository, ReviewRepository


logger = logging.getLogger(__name__)


async def log_review_failure(
    event_type: str,
    failure_stage: str,
    error: Exception,
    event_key: str | None = None,
    request_payload: dict | None = None,
    project_key: str | None = None,
    repo_slug: str | None = None,
    commit_id: str | None = None,
    pr_id: int | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
    retry_count: int = 0,
) -> int | None:
    """Log a review failure to database. Returns the failure log ID if successful, None otherwise."""
    try:
        async with get_db_session() as session:
            repo = FailureLogRepository(session)
            failure_log = await repo.create_failure_log(
                event_type=event_type,
                event_key=event_key,
                request_payload=request_payload,
                project_key=project_key,
                repo_slug=repo_slug,
                commit_id=commit_id,
                pr_id=pr_id,
                author_name=author_name,
                author_email=author_email,
                failure_stage=failure_stage,
                error_type=type(error).__name__,
                error_message=str(error),
                error_stacktrace=traceback.format_exc(),
                retry_count=retry_count,
            )
            failure_id: int = failure_log.id
            logger.info(f"Logged failure with ID: {failure_id}")
            return failure_id
    except Exception as e:
        logger.error(f"Error logging failure to database: {str(e)}")
        # Don't raise - failure logging should not break the system
        return None


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
) -> tuple[bool, list[str], str | None]:
    """Send review email to author and reviewers (for PRs). Returns (success, recipient_emails, author_name) tuple."""
    try:
        recipient_emails = []
        author_name = None
        subject_id = "Unknown"

        if commit_id:
            # Get commit info to extract author email
            commit_info = await bitbucket_client.get_commit_info(project_key, repo_slug, commit_id)
            if commit_info and commit_info.get("author"):
                author_data = commit_info["author"]
                author_email = author_data.get("emailAddress")
                author_name = author_data.get("displayName") or author_data.get("name")
                if author_email:
                    recipient_emails.append(author_email)
                subject_id = f"Commit {commit_id[:8]} authored by {author_name}"

        elif pr_id:
            # Get PR info to extract author and reviewers emails
            pr_info = await bitbucket_client.get_pull_request_info(project_key, repo_slug, pr_id)
            if pr_info and pr_info.get("author") and pr_info["author"].get("user"):
                user_data = pr_info["author"]["user"]
                author_email = user_data.get("emailAddress")
                author_name = user_data.get("displayName") or user_data.get("name")
                if author_email:
                    recipient_emails.append(author_email)

                # Extract reviewer emails
                reviewers = pr_info.get("reviewers", [])
                for reviewer in reviewers:
                    if reviewer.get("user"):
                        reviewer_email = reviewer["user"].get("emailAddress")
                        if reviewer_email and reviewer_email not in recipient_emails:
                            recipient_emails.append(reviewer_email)

                subject_id = f"Pull Request #{pr_id} authored by {author_name}"

        if not recipient_emails:
            logger.warning(f"Could not get recipient emails for {subject_id}, skipping email")
            return False, [], None

        # Create email subject
        subject = f"{review_type} - {subject_id}"

        # Format review as HTML
        html_body = format_review_to_html(f"🤖 **{review_type}**\n\n{review}")

        # Send email to all recipients
        recipients_str = ", ".join(recipient_emails)
        send_mail(
            to=recipients_str,
            cc="",  # No CC for now
            subject=subject,
            mailbody=html_body,
        )

        logger.info(
            f"Sent {review_type.lower()} email for {subject_id} to {len(recipient_emails)} recipient(s): {recipients_str}"
        )
        return True, recipient_emails, author_name

    except Exception as e:
        logger.error(f"Error sending {review_type.lower()} email for {subject_id}: {str(e)}")
        return False, [], None


async def process_pull_request_review(
    bitbucket_client: BitbucketClient, llm_client: LLMClient, payload: dict[str, Any], is_manual: bool = False
):
    """Process pull request for AI review"""
    project_key = None
    repo_slug = None
    pr_id = None
    author_name = None
    author_email = None
    event_type = "manual" if is_manual else "webhook"
    event_key = "manual_review" if is_manual else payload.get("eventKey")

    try:
        # Validate payload structure
        if "pullRequest" not in payload:
            error = ValueError("Invalid payload: missing 'pullRequest' key")
            logger.error(str(error))
            await log_review_failure(
                event_type=event_type,
                event_key=event_key,
                failure_stage="payload_validation",
                error=error,
                request_payload=payload,
            )
            return

        pull_request = payload["pullRequest"]

        # Extract repository info from toRef (target branch)
        if "toRef" not in pull_request:
            error = ValueError("Invalid pull request payload: missing 'toRef' key")
            logger.error(str(error))
            await log_review_failure(
                event_type=event_type,
                event_key=event_key,
                failure_stage="payload_validation",
                error=error,
                request_payload=payload,
            )
            return

        to_ref = pull_request["toRef"]
        repository = to_ref.get("repository")

        if not repository:
            error = ValueError("Invalid pull request payload: missing 'repository' in toRef")
            logger.error(str(error))
            await log_review_failure(
                event_type=event_type,
                event_key=event_key,
                failure_stage="payload_validation",
                error=error,
                request_payload=payload,
            )
            return

        project_key = repository["project"]["key"]
        repo_slug = repository["slug"]
        pr_id = pull_request["id"]

        logger.info(f"Processing PR review for {project_key}/{repo_slug}/pull-requests/{pr_id}")

        # Get pull request diff
        try:
            diff = await bitbucket_client.get_pull_request_diff(project_key, repo_slug, pr_id)
        except Exception as e:
            logger.error(f"Error fetching PR diff: {str(e)}")
            await log_review_failure(
                event_type=event_type,
                event_key=event_key,
                failure_stage="bitbucket_fetch_diff",
                error=e,
                request_payload=payload,
                project_key=project_key,
                repo_slug=repo_slug,
                pr_id=pr_id,
            )
            return

        if not diff or len(diff.strip()) == 0:
            logger.info(f"No diff found for PR {pr_id}, skipping review")
            return

        # Get AI review
        try:
            review = await llm_client.get_code_review(diff)
        except Exception as e:
            logger.error(f"Error getting LLM review: {str(e)}")
            await log_review_failure(
                event_type=event_type,
                event_key=event_key,
                failure_stage="llm_review",
                error=e,
                request_payload=payload,
                project_key=project_key,
                repo_slug=repo_slug,
                pr_id=pr_id,
            )
            return

        if review and review.strip() != "No issues found.":
            # Comment out post_pull_request_comment for now
            # await bitbucket_client.post_pull_request_comment(
            #     project_key, repo_slug, pr_id, f"🤖 **AI Code Review**\n\n{review}"
            # )

            # Send review email
            review_type = "AI Code Review (Manual)" if is_manual else "AI Code Review"
            try:
                email_sent, recipient_emails, author_name = await send_review_email(
                    bitbucket_client, project_key, repo_slug, review, review_type, pr_id=pr_id
                )
                # Get author email (first in recipient list, which is always the author)
                author_email = recipient_emails[0] if recipient_emails else None
            except Exception as e:
                logger.error(f"Error sending review email: {str(e)}")
                await log_review_failure(
                    event_type=event_type,
                    event_key=event_key,
                    failure_stage="email_send",
                    error=e,
                    request_payload=payload,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    pr_id=pr_id,
                    author_name=author_name,
                    author_email=author_email,
                )
                # Continue to save review even if email fails
                email_sent = False
                recipient_emails = []

            # Save to database
            try:
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
                    email_recipients=recipient_emails if recipient_emails else None,
                    email_sent=email_sent,
                )
            except Exception as e:
                logger.error(f"Error saving review to database: {str(e)}")
                await log_review_failure(
                    event_type=event_type,
                    event_key=event_key,
                    failure_stage="database_save",
                    error=e,
                    request_payload=payload,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    pr_id=pr_id,
                    author_name=author_name,
                    author_email=author_email,
                )

            logger.info(f"Processed AI review for PR {pr_id}")
        else:
            logger.info(f"No issues found in PR {pr_id}, no email sent")

    except Exception as e:
        logger.error(f"Error processing pull request review: {str(e)}")
        await log_review_failure(
            event_type=event_type,
            event_key=event_key,
            failure_stage="unknown",
            error=e,
            request_payload=payload,
            project_key=project_key,
            repo_slug=repo_slug,
            pr_id=pr_id,
            author_name=author_name,
            author_email=author_email,
        )


async def process_commit_review(
    bitbucket_client: BitbucketClient, llm_client: LLMClient, payload: dict[str, Any], is_manual: bool = False
):
    """Process commit for AI review"""
    project_key = None
    repo_slug = None
    commit_id = None
    author_name = None
    author_email = None
    event_type = "manual" if is_manual else "webhook"
    event_key = "manual_review" if is_manual else payload.get("eventKey")

    try:
        repository = payload.get("repository")
        if not repository:
            error = ValueError("Invalid payload: missing 'repository' key")
            logger.error(str(error))
            await log_review_failure(
                event_type=event_type,
                event_key=event_key,
                failure_stage="payload_validation",
                error=error,
                request_payload=payload,
            )
            return

        changes = payload.get("changes", [])

        if not changes:
            logger.info("No changes found in commit payload")
            return

        project_key = repository["project"]["key"]
        repo_slug = repository["slug"]

        for change in changes:
            commit_id = change.get("toHash")
            if not commit_id:
                logger.warning("Skipping change without commit ID")
                continue

            logger.info(f"Processing commit review for {project_key}/{repo_slug}/commits/{commit_id}")

            # Get commit diff
            try:
                diff = await bitbucket_client.get_commit_diff(project_key, repo_slug, commit_id)
            except Exception as e:
                logger.error(f"Error fetching commit diff: {str(e)}")
                await log_review_failure(
                    event_type=event_type,
                    event_key=event_key,
                    failure_stage="bitbucket_fetch_diff",
                    error=e,
                    request_payload=payload,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    commit_id=commit_id,
                )
                continue

            if not diff or len(diff.strip()) == 0:
                logger.info(f"No diff found for commit {commit_id}, skipping review")
                continue

            # Get AI review
            try:
                review = await llm_client.get_code_review(diff)
            except Exception as e:
                logger.error(f"Error getting LLM review: {str(e)}")
                await log_review_failure(
                    event_type=event_type,
                    event_key=event_key,
                    failure_stage="llm_review",
                    error=e,
                    request_payload=payload,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    commit_id=commit_id,
                )
                continue

            if review and review.strip() != "No issues found.":
                # Comment out post_commit_comment for now
                # await bitbucket_client.post_commit_comment(
                #     project_key, repo_slug, commit_id, f"🤖 **AI Code Review**\n\n{review}"
                # )

                # Send review email
                review_type = "AI Code Review (Manual)" if is_manual else "AI Code Review"
                try:
                    email_sent, recipient_emails, author_name = await send_review_email(
                        bitbucket_client, project_key, repo_slug, review, review_type, commit_id=commit_id
                    )
                    # Get author email (first and only in recipient list for commits)
                    author_email = recipient_emails[0] if recipient_emails else None
                except Exception as e:
                    logger.error(f"Error sending review email: {str(e)}")
                    await log_review_failure(
                        event_type=event_type,
                        event_key=event_key,
                        failure_stage="email_send",
                        error=e,
                        request_payload=payload,
                        project_key=project_key,
                        repo_slug=repo_slug,
                        commit_id=commit_id,
                        author_name=author_name,
                        author_email=author_email,
                    )
                    # Continue to save review even if email fails
                    email_sent = False
                    recipient_emails = []

                # Save to database
                try:
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
                        email_recipients=recipient_emails if recipient_emails else None,
                        email_sent=email_sent,
                    )
                except Exception as e:
                    logger.error(f"Error saving review to database: {str(e)}")
                    await log_review_failure(
                        event_type=event_type,
                        event_key=event_key,
                        failure_stage="database_save",
                        error=e,
                        request_payload=payload,
                        project_key=project_key,
                        repo_slug=repo_slug,
                        commit_id=commit_id,
                        author_name=author_name,
                        author_email=author_email,
                    )

                logger.info(f"Processed AI review for commit {commit_id}")
            else:
                logger.info(f"No issues found in commit {commit_id}, no email sent")

    except Exception as e:
        logger.error(f"Error processing commit review: {str(e)}")
        await log_review_failure(
            event_type=event_type,
            event_key=event_key,
            failure_stage="unknown",
            error=e,
            request_payload=payload,
            project_key=project_key,
            repo_slug=repo_slug,
            commit_id=commit_id,
            author_name=author_name,
            author_email=author_email,
        )
