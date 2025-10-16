"""Manual review trigger endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client
from ai_code_reviewer.core.review_engine import save_review_to_database, send_review_email


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/manual-review")
async def manual_review(project_key: str, repo_slug: str, pr_id: int | None = None, commit_id: str | None = None):
    """Manually trigger a code review"""
    try:
        # Get clients
        bitbucket_client = get_bitbucket_client()
        llm_client = get_llm_client()

        if pr_id:
            # Review pull request
            diff = await bitbucket_client.get_pull_request_diff(project_key, repo_slug, pr_id)
            if diff:
                review = await llm_client.get_code_review(diff)
                if review and review.strip() != "No issues found.":
                    # Comment out post_pull_request_comment for now
                    # await bitbucket_client.post_pull_request_comment(
                    #     project_key, repo_slug, pr_id, f"🤖 **AI Code Review (Manual)**\n\n{review}"
                    # )

                    # Send review email
                    email_sent, recipient_emails, author_name = await send_review_email(
                        bitbucket_client, project_key, repo_slug, review, "AI Code Review (Manual)", pr_id=pr_id
                    )

                    # Save to database
                    # Get author email (first in recipient list, which is always the author)
                    author_email = recipient_emails[0] if recipient_emails else None

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

                return {"status": "completed", "review": review, "record_id": record_id}
            else:
                return {"status": "no_diff", "message": "No diff found"}

        elif commit_id:
            # Review commit
            diff = await bitbucket_client.get_commit_diff(project_key, repo_slug, commit_id)
            if diff:
                review = await llm_client.get_code_review(diff)
                if review and review.strip() != "No issues found.":
                    # Comment out post_commit_comment for now
                    # await bitbucket_client.post_commit_comment(
                    #     project_key, repo_slug, commit_id, f"🤖 **AI Code Review (Manual)**\n\n{review}"
                    # )

                    # Send review email
                    email_sent, recipient_emails, author_name = await send_review_email(
                        bitbucket_client, project_key, repo_slug, review, "AI Code Review (Manual)", commit_id=commit_id
                    )

                    # Save to database
                    # Get author email (first and only in recipient list for commits)
                    author_email = recipient_emails[0] if recipient_emails else None

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

                return {"status": "completed", "review": review, "record_id": record_id}
            else:
                return {"status": "no_diff", "message": "No diff found"}

        else:
            raise HTTPException(status_code=400, detail="Either pr_id or commit_id must be provided")

    except Exception as e:
        logger.error(f"Error in manual review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
