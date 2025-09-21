import logging
import hashlib
import hmac
from typing import Dict, Any
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

from config import Config
from bitbucket_client import BitbucketClient
from llm_client import LLMClient

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Code Reviewer",
    description="AI-powered code review agent for Bitbucket Enterprise Server",
    version="1.0.0"
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

class WebhookPayload(BaseModel):
    eventKey: str
    date: str
    actor: Dict[str, Any]
    repository: Dict[str, Any]
    pullRequest: Dict[str, Any] = None
    changes: list = None

def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """Verify webhook signature if secret is configured"""
    if not Config.WEBHOOK_SECRET:
        return True  # Skip verification if no secret is configured
    
    expected_signature = hmac.new(
        Config.WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(f"sha256={expected_signature}", signature)

async def process_pull_request_review(payload: Dict[str, Any]):
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
            # Post review comment
            await bitbucket_client.post_pull_request_comment(
                project_key, repo_slug, pr_id, f"🤖 **AI Code Review**\n\n{review}"
            )
            logger.info(f"Posted AI review for PR {pr_id}")
        else:
            logger.info(f"No issues found in PR {pr_id}, no comment posted")
            
    except Exception as e:
        logger.error(f"Error processing pull request review: {str(e)}")

async def process_commit_review(payload: Dict[str, Any]):
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
                # Post review comment
                await bitbucket_client.post_commit_comment(
                    project_key, repo_slug, commit_id, f"🤖 **AI Code Review**\n\n{review}"
                )
                logger.info(f"Posted AI review for commit {commit_id}")
            else:
                logger.info(f"No issues found in commit {commit_id}, no comment posted")
                
    except Exception as e:
        logger.error(f"Error processing commit review: {str(e)}")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Code Reviewer is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Validate configuration
        Config.validate_config()
        
        # Test Bitbucket connection
        bitbucket_status = await bitbucket_client.test_connection()
        
        # Test LLM connection
        llm_status = await llm_client.test_connection()
        
        return {
            "status": "healthy",
            "bitbucket": bitbucket_status,
            "llm": llm_status,
            "config": {
                "bitbucket_url": Config.BITBUCKET_URL,
                "llm_provider": Config.LLM_PROVIDER,
                "llm_model": Config.LLM_MODEL
            }
        }
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

@app.post("/webhook/code-review")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """Handle Bitbucket webhooks for code review"""
    try:
        # Get raw payload for signature verification
        payload_bytes = await request.body()
        
        # Verify webhook signature if configured
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not verify_webhook_signature(payload_bytes, signature):
            raise HTTPException(status_code=401, detail="Invalid webhook signature")
        
        # Parse JSON payload
        payload = await request.json()
        
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
        
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/manual-review")
async def manual_review(
    project_key: str,
    repo_slug: str,
    pr_id: int = None,
    commit_id: str = None
):
    """Manually trigger a code review"""
    try:
        if pr_id:
            # Review pull request
            diff = await bitbucket_client.get_pull_request_diff(project_key, repo_slug, pr_id)
            if diff:
                review = await llm_client.get_code_review(diff)
                if review and review.strip() != "No issues found.":
                    await bitbucket_client.post_pull_request_comment(
                        project_key, repo_slug, pr_id, f"🤖 **AI Code Review (Manual)**\n\n{review}"
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
                    await bitbucket_client.post_commit_comment(
                        project_key, repo_slug, commit_id, f"🤖 **AI Code Review (Manual)**\n\n{review}"
                    )
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
        uvicorn.run(
            "main:app",
            host=Config.HOST,
            port=Config.PORT,
            reload=False,
            log_level=Config.LOG_LEVEL.lower()
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")
        exit(1)

