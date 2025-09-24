import hashlib
import hmac
import json
import logging
import re
from datetime import datetime
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


# Load environment variables BEFORE importing config
load_dotenv()

from bitbucket_client import BitbucketClient  # noqa: E402
from config import Config  # noqa: E402
from llm_client import LLMClient  # noqa: E402
from send_email import send_mail  # noqa: E402


# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL), format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Code Reviewer",
    description="AI-powered code review agent for Bitbucket Enterprise Server",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
bitbucket_client = BitbucketClient()
llm_client = LLMClient()


def format_review_to_html(review_text: str) -> str:
    """Convert review text from markdown to HTML format for email"""
    # Convert markdown headers to HTML
    html_text = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', review_text, flags=re.MULTILINE)
    html_text = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html_text, flags=re.MULTILINE)

    # Convert bold text
    html_text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_text)

    # Convert code blocks
    html_text = re.sub(r'```(\w*)\n(.*?)```', r'<pre><code class="\1">\2</code></pre>', html_text, flags=re.DOTALL)

    # Convert inline code
    html_text = re.sub(r'`([^`]+)`', r'<code>\1</code>', html_text)

    # Convert bullet points
    html_text = re.sub(r'^   - (.*?)$', r'   <li>\1</li>', html_text, flags=re.MULTILINE)

    # Convert newlines to <br> for better formatting
    html_text = html_text.replace('\n', '<br>\n')

    # Wrap in basic HTML structure
    return f"""
<html>
<body>
<div style="font-family: Arial, sans-serif; max-width: 800px;">
{html_text}
</div>
</body>
</html>
"""


async def send_review_email(project_key: str, repo_slug: str, review: str, review_type: str = "AI Code Review", commit_id: str | None = None, pr_id: int | None = None) -> bool:
    """Send review email to author. Returns True if email was sent successfully, False otherwise."""
    try:
        author_email = None
        subject_id = "Unknown"

        if commit_id:
            # Get commit info to extract author email
            commit_info = await bitbucket_client.get_commit_info(project_key, repo_slug, commit_id)
            if commit_info and commit_info.get("author") and commit_info["author"].get("emailAddress"):
                author_email = commit_info["author"]["emailAddress"]
                subject_id = f"Commit {commit_id[:8]}"

        elif pr_id:
            # Get PR info to extract author email
            pr_info = await bitbucket_client.get_pull_request_info(project_key, repo_slug, pr_id)
            if pr_info and pr_info.get("author") and pr_info["author"].get("user") and pr_info["author"]["user"].get("emailAddress"):
                author_email = pr_info["author"]["user"]["emailAddress"]
                subject_id = f"PR #{pr_id}"

        if not author_email:
            logger.warning(f"Could not get author email for {subject_id}, skipping email")
            return False

        # Create email subject
        subject = f"{review_type} - {subject_id}"

        # Format review as HTML
        html_body = format_review_to_html(f"🤖 **{review_type}**\n\n{review}")

        # Send email
        send_mail(
            to=author_email,
            cc="",  # No CC for now
            subject=subject,
            mailbody=html_body
        )

        logger.info(f"Sent {review_type.lower()} email for {subject_id} to {author_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending {review_type.lower()} email for {subject_id}: {str(e)}")
        return False


class WebhookPayload(BaseModel):
    eventKey: str
    date: str
    actor: dict[str, Any]
    repository: dict[str, Any]
    pullRequest: dict[str, Any] | None = None
    changes: list | None = None


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature if secret is configured"""
    if not Config.WEBHOOK_SECRET:
        return True  # Skip verification if no secret is configured

    expected_signature = hmac.new(Config.WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()

    return hmac.compare_digest(f"sha256={expected_signature}", signature)


async def process_pull_request_review(payload: dict[str, Any]):
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
            await send_review_email(project_key, repo_slug, review, "AI Code Review", pr_id=pr_id)
            logger.info(f"Processed AI review for PR {pr_id}")
        else:
            logger.info(f"No issues found in PR {pr_id}, no email sent")

    except Exception as e:
        logger.error(f"Error processing pull request review: {str(e)}")


async def process_commit_review(payload: dict[str, Any]):
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
                await send_review_email(project_key, repo_slug, review, "AI Code Review", commit_id=commit_id)
                logger.info(f"Processed AI review for commit {commit_id}")
            else:
                logger.info(f"No issues found in commit {commit_id}, no email sent")

    except Exception as e:
        logger.error(f"Error processing commit review: {str(e)}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Code Reviewer is running", "status": "healthy"}


@app.get("/health")
async def health_check():
    """Basic health check - lightweight for container health checks"""
    try:
        # Only validate configuration (no external API calls)
        Config.validate_config()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "config": {
                "bitbucket_url": Config.BITBUCKET_URL,
                "llm_provider": Config.LLM_PROVIDER,
                "llm_model": Config.LLM_MODEL,
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.get("/health/detailed")
async def detailed_health_check():
    """Comprehensive health check with external API validation"""
    try:
        # Validate configuration
        Config.validate_config()

        # Test Bitbucket connection
        bitbucket_status = await bitbucket_client.test_connection()

        # Test LLM connection
        llm_status = await llm_client.test_connection()

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "bitbucket": bitbucket_status,
            "llm": llm_status,
            "config": {
                "bitbucket_url": Config.BITBUCKET_URL,
                "llm_provider": Config.LLM_PROVIDER,
                "llm_model": Config.LLM_MODEL,
            },
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/webhook/code-review")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """Handle Bitbucket webhooks for code review"""
    payload = None
    try:
        # Get raw payload for signature verification
        payload_bytes = await request.body()

        # # Verify webhook signature if configured
        # signature = request.headers.get("X-Hub-Signature-256", "")
        # if not verify_webhook_signature(payload_bytes, signature):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse JSON payload
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Handle BitBucket test connection
        if payload.get("test") is True:
            logger.info("Received Bitbucket test connection webhook")
            return {"status": "success", "message": "Test connection received"}

        event_key = payload.get("eventKey", "")
        logger.info(f"Received webhook event: {event_key}")

        # Handle pull request events
        if event_key in ["pr:opened", "pr:modified", "pr:from_ref_updated"]:
            background_tasks.add_task(process_pull_request_review, payload)

        # Handle push events (commits)
        elif event_key == "repo:refs_changed":
            background_tasks.add_task(process_commit_review, payload)

        else:
            logger.info(f"Ignoring event: {event_key}")

        return {"status": "accepted", "event": event_key}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload in webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/manual-review")
async def manual_review(project_key: str, repo_slug: str, pr_id: int | None = None, commit_id: str | None = None):
    """Manually trigger a code review"""
    try:
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
                    await send_review_email(project_key, repo_slug, review, "AI Code Review (Manual)", pr_id=pr_id)

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
                    await send_review_email(project_key, repo_slug, review, "AI Code Review (Manual)", commit_id=commit_id)

                return {"status": "completed", "review": review}
            else:
                return {"status": "no_diff", "message": "No diff found"}

        else:
            raise HTTPException(status_code=400, detail="Either pr_id or commit_id must be provided")

    except Exception as e:
        logger.error(f"Error in manual review: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    try:
        # Validate configuration on startup
        Config.validate_config()
        logger.info("Configuration validated successfully")

        # Start the server
        uvicorn.run("main:app", host=Config.HOST, port=Config.PORT, reload=False, log_level=Config.LOG_LEVEL.lower())
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        exit(1)
