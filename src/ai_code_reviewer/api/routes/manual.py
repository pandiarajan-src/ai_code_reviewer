"""Manual review trigger endpoints."""

import logging

from fastapi import APIRouter, HTTPException

from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client
from ai_code_reviewer.core.review_engine import send_review_email


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
                    await send_review_email(
                        bitbucket_client, project_key, repo_slug, review, "AI Code Review (Manual)", pr_id=pr_id
                    )

                return {"status": "completed", "review": review}
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
                    await send_review_email(
                        bitbucket_client, project_key, repo_slug, review, "AI Code Review (Manual)", commit_id=commit_id
                    )

                return {"status": "completed", "review": review}
            else:
                return {"status": "no_diff", "message": "No diff found"}

        else:
            raise HTTPException(status_code=400, detail="Either pr_id or commit_id must be provided")

    except Exception as e:
        logger.error(f"Error in manual review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
