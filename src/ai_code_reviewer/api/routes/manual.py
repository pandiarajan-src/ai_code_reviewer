"""Manual review trigger endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client
from ai_code_reviewer.core.review_engine import log_review_failure, save_review_to_database, send_review_email


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/manual-review")
async def manual_review(project_key: str, repo_slug: str, pr_id: int | None = None, commit_id: str | None = None):
    """Manually trigger a code review"""
    author_name = None
    author_email = None

    try:
        # Validate parameters
        if not pr_id and not commit_id:
            error = ValueError("Either pr_id or commit_id must be provided")
            await log_review_failure(
                event_type="manual",
                event_key="manual_review",
                failure_stage="parameter_validation",
                error=error,
                project_key=project_key,
                repo_slug=repo_slug,
            )
            raise HTTPException(status_code=400, detail=str(error))

        # Get clients
        try:
            bitbucket_client = get_bitbucket_client()
            llm_client = get_llm_client()
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            await log_review_failure(
                event_type="manual",
                event_key="manual_review",
                failure_stage="client_initialization",
                error=e,
                project_key=project_key,
                repo_slug=repo_slug,
                pr_id=pr_id,
                commit_id=commit_id,
            )
            raise HTTPException(status_code=500, detail="Failed to initialize clients")

        if pr_id:
            # Review pull request
            try:
                diff = await bitbucket_client.get_pull_request_diff(project_key, repo_slug, pr_id)
            except Exception as e:
                logger.error(f"Error fetching PR diff: {str(e)}")
                await log_review_failure(
                    event_type="manual",
                    event_key="manual_review",
                    failure_stage="bitbucket_fetch_diff",
                    error=e,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    pr_id=pr_id,
                )
                raise HTTPException(status_code=500, detail=f"Failed to fetch PR diff: {str(e)}")

            if diff:
                try:
                    review = await llm_client.get_code_review(diff)
                except Exception as e:
                    logger.error(f"Error getting LLM review: {str(e)}")
                    await log_review_failure(
                        event_type="manual",
                        event_key="manual_review",
                        failure_stage="llm_review",
                        error=e,
                        project_key=project_key,
                        repo_slug=repo_slug,
                        pr_id=pr_id,
                    )
                    raise HTTPException(status_code=500, detail=f"Failed to get LLM review: {str(e)}")

                if review and review.strip() != "No issues found.":
                    # Send review email
                    try:
                        email_sent, recipient_emails, author_name = await send_review_email(
                            bitbucket_client, project_key, repo_slug, review, "AI Code Review (Manual)", pr_id=pr_id
                        )
                        # Get author email (first in recipient list, which is always the author)
                        author_email = recipient_emails[0] if recipient_emails else None
                    except Exception as e:
                        logger.error(f"Error sending review email: {str(e)}")
                        await log_review_failure(
                            event_type="manual",
                            event_key="manual_review",
                            failure_stage="email_send",
                            error=e,
                            project_key=project_key,
                            repo_slug=repo_slug,
                            pr_id=pr_id,
                            author_name=author_name,
                            author_email=author_email,
                        )
                        # Continue without email
                        email_sent = False
                        recipient_emails = []

                    # Save to database
                    try:
                        record_id = await save_review_to_database(
                            review_type="manual",
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
                            event_type="manual",
                            event_key="manual_review",
                            failure_stage="database_save",
                            error=e,
                            project_key=project_key,
                            repo_slug=repo_slug,
                            pr_id=pr_id,
                            author_name=author_name,
                            author_email=author_email,
                        )
                        raise HTTPException(status_code=500, detail=f"Failed to save review: {str(e)}")

                return {"status": "completed", "review": review, "record_id": record_id}
            else:
                return {"status": "no_diff", "message": "No diff found"}

        elif commit_id:
            # Review commit
            try:
                diff = await bitbucket_client.get_commit_diff(project_key, repo_slug, commit_id)
            except Exception as e:
                logger.error(f"Error fetching commit diff: {str(e)}")
                await log_review_failure(
                    event_type="manual",
                    event_key="manual_review",
                    failure_stage="bitbucket_fetch_diff",
                    error=e,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    commit_id=commit_id,
                )
                raise HTTPException(status_code=500, detail=f"Failed to fetch commit diff: {str(e)}")

            if diff:
                try:
                    review = await llm_client.get_code_review(diff)
                except Exception as e:
                    logger.error(f"Error getting LLM review: {str(e)}")
                    await log_review_failure(
                        event_type="manual",
                        event_key="manual_review",
                        failure_stage="llm_review",
                        error=e,
                        project_key=project_key,
                        repo_slug=repo_slug,
                        commit_id=commit_id,
                    )
                    raise HTTPException(status_code=500, detail=f"Failed to get LLM review: {str(e)}")

                if review and review.strip() != "No issues found.":
                    # Send review email
                    try:
                        email_sent, recipient_emails, author_name = await send_review_email(
                            bitbucket_client,
                            project_key,
                            repo_slug,
                            review,
                            "AI Code Review (Manual)",
                            commit_id=commit_id,
                        )
                        # Get author email (first and only in recipient list for commits)
                        author_email = recipient_emails[0] if recipient_emails else None
                    except Exception as e:
                        logger.error(f"Error sending review email: {str(e)}")
                        await log_review_failure(
                            event_type="manual",
                            event_key="manual_review",
                            failure_stage="email_send",
                            error=e,
                            project_key=project_key,
                            repo_slug=repo_slug,
                            commit_id=commit_id,
                            author_name=author_name,
                            author_email=author_email,
                        )
                        # Continue without email
                        email_sent = False
                        recipient_emails = []

                    # Save to database
                    try:
                        record_id = await save_review_to_database(
                            review_type="manual",
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
                            event_type="manual",
                            event_key="manual_review",
                            failure_stage="database_save",
                            error=e,
                            project_key=project_key,
                            repo_slug=repo_slug,
                            commit_id=commit_id,
                            author_name=author_name,
                            author_email=author_email,
                        )
                        raise HTTPException(status_code=500, detail=f"Failed to save review: {str(e)}")

                return {"status": "completed", "review": review, "record_id": record_id}
            else:
                return {"status": "no_diff", "message": "No diff found"}

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error in manual review: {str(e)}")
        await log_review_failure(
            event_type="manual",
            event_key="manual_review",
            failure_stage="unknown",
            error=e,
            project_key=project_key,
            repo_slug=repo_slug,
            pr_id=pr_id,
            commit_id=commit_id,
            author_name=author_name,
            author_email=author_email,
        )
        raise HTTPException(status_code=500, detail=str(e))
