"""Manual review trigger endpoints."""

import logging
from datetime import UTC, datetime

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

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


@router.post("/review-diff")
async def review_diff_file(
    file: UploadFile = File(..., description="Diff file to review"),  # noqa: B008
    project_key: str = Form(default="MANUAL", description="Project identifier"),  # noqa: B008
    repo_slug: str = Form(default="diff-upload", description="Repository identifier"),  # noqa: B008
    author_name: str = Form(default="Anonymous", description="Author name"),  # noqa: B008
    author_email: str | None = Form(default=None, description="Author email"),  # noqa: B008
    description: str | None = Form(default=None, description="Optional description of the changes"),  # noqa: B008
):
    """Review an uploaded .diff file using AI.

    This endpoint accepts a diff file upload, processes it through the LLM,
    and returns markdown-formatted review feedback. All reviews are persisted
    to the database for auditing. No Bitbucket integration or email sending.

    Args:
        file: The .diff file to review (max 10MB)
        project_key: Project identifier for tracking (default: "MANUAL")
        repo_slug: Repository identifier for tracking (default: "diff-upload")
        author_name: Name of the author (default: "Anonymous")
        author_email: Email of the author (optional)
        description: Optional description of the changes

    Returns:
        JSON response with markdown-formatted review and metadata including record_id
    """
    start_time = datetime.now(UTC)
    filename = file.filename or "unknown.diff"

    # Maximum file size: 10MB
    max_file_size = 10 * 1024 * 1024

    try:
        # Step 1: Validate file extension
        if not filename.endswith((".diff", ".patch")):
            error = ValueError(f"Invalid file type. Expected .diff or .patch file, got: {filename}")
            logger.error(str(error))
            await log_review_failure(
                event_type="manual",
                event_key="diff_upload",
                failure_stage="file_validation",
                error=error,
                project_key=project_key,
                repo_slug=repo_slug,
                author_name=author_name,
                author_email=author_email,
                request_payload={"filename": filename, "description": description},
            )
            raise HTTPException(status_code=400, detail=str(error))

        # Step 2: Read and validate file content
        try:
            diff_content = await file.read()

            # Check file size
            if len(diff_content) > max_file_size:
                error = ValueError(f"File too large: {len(diff_content)} bytes (max: {max_file_size} bytes)")
                logger.error(str(error))
                await log_review_failure(
                    event_type="manual",
                    event_key="diff_upload",
                    failure_stage="file_validation",
                    error=error,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    author_name=author_name,
                    author_email=author_email,
                    request_payload={"filename": filename, "size": len(diff_content)},
                )
                raise HTTPException(status_code=400, detail=str(error))

            # Decode as UTF-8
            try:
                diff_text = diff_content.decode("utf-8")
            except UnicodeDecodeError as e:
                error = ValueError(f"File must be UTF-8 encoded text: {str(e)}")
                logger.error(str(error))
                await log_review_failure(
                    event_type="manual",
                    event_key="diff_upload",
                    failure_stage="file_parsing",
                    error=error,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    author_name=author_name,
                    author_email=author_email,
                    request_payload={"filename": filename, "size": len(diff_content)},
                )
                raise HTTPException(status_code=400, detail=str(error))

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error reading file: {str(e)}")
            await log_review_failure(
                event_type="manual",
                event_key="diff_upload",
                failure_stage="file_parsing",
                error=e,
                project_key=project_key,
                repo_slug=repo_slug,
                author_name=author_name,
                author_email=author_email,
                request_payload={"filename": filename},
            )
            raise HTTPException(status_code=500, detail=f"Failed to read file: {str(e)}")

        # Step 3: Basic diff validation
        diff_text_stripped = diff_text.strip()
        if not diff_text_stripped:
            error = ValueError("Diff file is empty")
            logger.error(str(error))
            await log_review_failure(
                event_type="manual",
                event_key="diff_upload",
                failure_stage="diff_validation",
                error=error,
                project_key=project_key,
                repo_slug=repo_slug,
                author_name=author_name,
                author_email=author_email,
                request_payload={"filename": filename, "size": len(diff_content)},
            )
            raise HTTPException(status_code=400, detail=str(error))

        # Add description as metadata prefix if provided
        diff_with_metadata = f"# Description: {description}\n\n{diff_text}" if description else diff_text

        # Step 4: Get LLM review
        try:
            llm_client = get_llm_client()
            review = await llm_client.get_code_review(diff_text)

            if not review:
                error = ValueError("LLM returned empty review")
                logger.error(str(error))
                await log_review_failure(
                    event_type="manual",
                    event_key="diff_upload",
                    failure_stage="llm_review",
                    error=error,
                    project_key=project_key,
                    repo_slug=repo_slug,
                    author_name=author_name,
                    author_email=author_email,
                    request_payload={"filename": filename, "diff_size": len(diff_text)},
                )
                raise HTTPException(status_code=500, detail="Failed to get review from LLM")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting LLM review: {str(e)}")
            await log_review_failure(
                event_type="manual",
                event_key="diff_upload",
                failure_stage="llm_review",
                error=e,
                project_key=project_key,
                repo_slug=repo_slug,
                author_name=author_name,
                author_email=author_email,
                request_payload={"filename": filename, "diff_size": len(diff_text)},
            )
            raise HTTPException(status_code=500, detail=f"Failed to get LLM review: {str(e)}")

        # Step 5: Save to database (ALWAYS)
        try:
            record_id = await save_review_to_database(
                review_type="manual",
                trigger_type="diff_upload",
                project_key=project_key,
                repo_slug=repo_slug,
                diff_content=diff_with_metadata,
                review_feedback=review,
                commit_id=None,
                pr_id=None,
                author_name=author_name,
                author_email=author_email,
                email_recipients=None,
                email_sent=False,
            )

            if not record_id:
                logger.warning("Database save returned None, review may not have been persisted")

        except Exception as e:
            logger.error(f"Error saving review to database: {str(e)}")
            await log_review_failure(
                event_type="manual",
                event_key="diff_upload",
                failure_stage="database_save",
                error=e,
                project_key=project_key,
                repo_slug=repo_slug,
                author_name=author_name,
                author_email=author_email,
                request_payload={"filename": filename, "diff_size": len(diff_text)},
            )
            # Don't raise - still return the review to the user
            record_id = None

        # Step 6: Calculate metrics and return response
        end_time = datetime.now(UTC)
        processing_time = (end_time - start_time).total_seconds()

        # Count lines in diff
        lines_total = len(diff_text.splitlines())
        lines_added = sum(1 for line in diff_text.splitlines() if line.startswith("+") and not line.startswith("+++"))
        lines_removed = sum(1 for line in diff_text.splitlines() if line.startswith("-") and not line.startswith("---"))

        logger.info(
            f"Completed diff review: {filename} "
            f"({lines_total} lines, +{lines_added}/-{lines_removed}) "
            f"in {processing_time:.2f}s, record_id={record_id}"
        )

        return {
            "status": "success",
            "review_markdown": review,
            "metadata": {
                "record_id": record_id,
                "filename": filename,
                "diff_size_bytes": len(diff_text),
                "lines_total": lines_total,
                "lines_added": lines_added,
                "lines_removed": lines_removed,
                "project_key": project_key,
                "repo_slug": repo_slug,
                "author_name": author_name,
                "author_email": author_email,
                "description": description,
                "processing_time_seconds": round(processing_time, 2),
                "review_timestamp": end_time.isoformat(),
                "llm_provider": llm_client.provider,
                "llm_model": llm_client.model,
            },
        }

    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in diff review: {str(e)}")
        await log_review_failure(
            event_type="manual",
            event_key="diff_upload",
            failure_stage="unknown",
            error=e,
            project_key=project_key,
            repo_slug=repo_slug,
            author_name=author_name,
            author_email=author_email,
            request_payload={"filename": filename},
        )
        raise HTTPException(status_code=500, detail=str(e))
