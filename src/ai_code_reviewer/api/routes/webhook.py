"""Webhook handling endpoints."""

import hashlib
import hmac
import json
import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel

from ai_code_reviewer.api.core.config import Config
from ai_code_reviewer.api.core.review_engine import (
    log_review_failure,
    process_commit_review,
    process_pull_request_review,
)
from ai_code_reviewer.api.dependencies import get_bitbucket_client, get_llm_client


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
    payload_bytes = None
    try:
        # Get raw payload for signature verification
        payload_bytes = await request.body()

        # # Verify webhook signature if configured
        # signature = request.headers.get("X-Hub-Signature-256", "")
        # if not verify_webhook_signature(payload_bytes, signature):
        #     raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse JSON payload
        try:
            payload = json.loads(payload_bytes.decode("utf-8"))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload in webhook: {str(e)}")
            # Log webhook parsing failure
            await log_review_failure(
                event_type="webhook",
                event_key="unknown",
                failure_stage="webhook_parsing",
                error=e,
                request_payload={
                    "raw_body": payload_bytes.decode("utf-8", errors="replace") if payload_bytes else None
                },
            )
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Handle BitBucket test connection
        if payload.get("test") is True:
            logger.info("Received Bitbucket test connection webhook")
            return {"status": "success", "message": "Test connection received"}

        event_key = payload.get("eventKey", "")
        logger.info(f"Received webhook event: {event_key}")

        # Get clients
        try:
            bitbucket_client = get_bitbucket_client()
            llm_client = get_llm_client()
        except Exception as e:
            logger.error(f"Error initializing clients: {str(e)}")
            await log_review_failure(
                event_type="webhook",
                event_key=event_key,
                failure_stage="client_initialization",
                error=e,
                request_payload=payload,
            )
            raise HTTPException(status_code=500, detail="Failed to initialize clients")

        # Handle pull request events
        if event_key in ["pr:opened", "pr:modified", "pr:from_ref_updated"]:
            background_tasks.add_task(process_pull_request_review, bitbucket_client, llm_client, payload)

        # Handle push events (commits)
        elif event_key == "repo:refs_changed":
            background_tasks.add_task(process_commit_review, bitbucket_client, llm_client, payload)

        else:
            logger.info(f"Ignoring event: {event_key}")

        return {"status": "accepted", "event": event_key}
    except HTTPException:
        # Re-raise HTTP exceptions without logging (already logged above)
        raise
    except Exception as e:
        logger.error(f"Error handling webhook: {str(e)}")
        # Log unexpected webhook handler errors
        await log_review_failure(
            event_type="webhook",
            event_key=payload.get("eventKey") if payload else "unknown",
            failure_stage="webhook_handler",
            error=e,
            request_payload=payload,
        )
        raise HTTPException(status_code=500, detail=str(e))
