"""Webhook handling endpoints."""

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client
from ai_code_reviewer.core.config import Config
from ai_code_reviewer.core.review_engine import process_commit_review, process_pull_request_review


logger = logging.getLogger(__name__)
router = APIRouter()


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


@router.post("/webhook/code-review")
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

        # Get clients
        bitbucket_client = get_bitbucket_client()
        llm_client = get_llm_client()

        # Handle pull request events
        if event_key in ["pr:opened", "pr:modified", "pr:from_ref_updated"]:
            background_tasks.add_task(process_pull_request_review, bitbucket_client, llm_client, payload)

        # Handle push events (commits)
        elif event_key == "repo:refs_changed":
            background_tasks.add_task(process_commit_review, bitbucket_client, llm_client, payload)

        else:
            logger.info(f"Ignoring event: {event_key}")

        return {"status": "accepted", "event": event_key}
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON payload in webhook: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
