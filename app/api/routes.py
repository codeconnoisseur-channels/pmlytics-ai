"""FastAPI routes for the PMLytics AI API."""

import asyncio
import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.auth import AuthenticatedUser, get_current_user
from app.api.dependencies import get_api_settings, get_investigation_manager
from app.api.manager import InvestigationManager
from app.api.schemas import (
    HealthResponse,
    InvestigationCreateRequest,
    InvestigationDetailResponse,
    InvestigationRenameRequest,
    InvestigationStatusResponse,
    InvestigationSummaryResponse,
)
from app.config.settings import Settings

router = APIRouter(prefix="/api/v1", tags=["investigations"])


@router.post(
    "/investigations",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=InvestigationSummaryResponse,
    summary="Launch an asynchronous product investigation",
)
async def create_investigation(
    req: InvestigationCreateRequest,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationSummaryResponse:
    """Persist a new record, then launch its background investigation task."""
    context = {**req.context, "scope": req.scope.model_dump(mode="json")}
    record = await manager.create_owned_investigation(
        user_query=req.user_query,
        context=context,
        owner_id=user.user_id,
    )
    return InvestigationSummaryResponse(
        investigation_id=record.investigation_id,
        status=record.status,
        created_at=record.created_at,
        status_url=f"/api/v1/investigations/{record.investigation_id}",
        events_url=f"/api/v1/investigations/{record.investigation_id}/events",
        result_url=f"/api/v1/investigations/{record.investigation_id}/result",
    )


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationStatusResponse,
    summary="Retrieve current lifecycle status and active agent",
)
async def get_investigation_status(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationStatusResponse:
    """Retrieve progress state derived directly from the LangGraph investigation lifecycle."""
    record = await manager.get_owned(investigation_id, owner_id=user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    return manager.build_status_response(record)


@router.post(
    "/investigations/{investigation_id}/cancel",
    response_model=InvestigationStatusResponse,
    summary="Cancel an in-progress investigation",
)
async def cancel_investigation(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationStatusResponse:
    """Explicitly cancel an active investigation task."""
    record = await manager.get_owned(investigation_id, owner_id=user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )
    await manager.cancel_owned_investigation(investigation_id, owner_id=user.user_id)
    return manager.build_status_response(record)


@router.patch(
    "/investigations/{investigation_id}",
    response_model=InvestigationStatusResponse,
    summary="Rename an investigation in the owner's history",
)
async def rename_investigation(
    investigation_id: str,
    req: InvestigationRenameRequest,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationStatusResponse:
    record = await manager.rename_owned_investigation(
        investigation_id, user.user_id, req.display_name
    )
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found."
        )
    return manager.build_status_response(record)


@router.delete(
    "/investigations/{investigation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a completed investigation and its durable workflow history",
)
async def delete_investigation(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> None:
    try:
        deleted = await manager.delete_owned_investigation(investigation_id, user.user_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Investigation not found."
        )


@router.post(
    "/investigations/{investigation_id}/retry",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=InvestigationSummaryResponse,
    summary="Retry a failed investigation as a new run",
)
async def retry_investigation(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationSummaryResponse:
    record = await manager.retry_owned_investigation(investigation_id, user.user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only a failed investigation can be retried.",
        )
    return InvestigationSummaryResponse(
        investigation_id=record.investigation_id,
        status=record.status,
        created_at=record.created_at,
        status_url=f"/api/v1/investigations/{record.investigation_id}",
        events_url=f"/api/v1/investigations/{record.investigation_id}/events",
        result_url=f"/api/v1/investigations/{record.investigation_id}/result",
    )


@router.post(
    "/investigations/{investigation_id}/recover",
    response_model=InvestigationStatusResponse,
    summary="Resume a checkpointed investigation after an ambiguous interruption",
)
async def recover_investigation(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationStatusResponse:
    record = await manager.recover_owned_investigation(investigation_id, user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This investigation is not waiting for recovery.",
        )
    return manager.build_status_response(record)


@router.get(
    "/investigations/{investigation_id}/events",
    summary="Server-Sent Events (SSE) live progress stream",
)
async def stream_investigation_events(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> StreamingResponse:
    """Stream live progress milestones with immediate initial snapshot and clean completion."""
    record = await manager.get_owned(investigation_id, owner_id=user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    async def sse_event_generator() -> AsyncIterator[str]:
        try:
            async for event in manager.subscribe(investigation_id, owner_id=user.user_id):
                event_type = event.get("event", "message")
                payload = json.dumps(event)
                yield f"event: {event_type}\ndata: {payload}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        sse_event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/investigations/{investigation_id}/result",
    response_model=InvestigationDetailResponse,
    summary="Retrieve full structured recommendation and evidence ledger",
)
async def get_investigation_result(
    investigation_id: str,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> InvestigationDetailResponse:
    """Retrieve completed investigation findings.

    Returns HTTP 409 Conflict if the investigation is still actively executing.
    Returns HTTP 500 if execution failed. Never returns 200 for execution failures.
    """
    record = await manager.get_owned(investigation_id, owner_id=user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Investigation '{investigation_id}' not found.",
        )

    if record.status in (
        "pending",
        "planning",
        "gathering_evidence",
        "synthesizing",
        "reviewing",
        "revising",
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": f"Investigation '{investigation_id}' is still in progress (stage: {record.status}).",
                "status": record.status,
                "active_agent": record.active_agent,
                "elapsed_seconds": record.elapsed_seconds,
            },
        )

    if record.status == "failed":
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": f"Investigation '{investigation_id}' failed during execution.",
                "error": record.error,
                "elapsed_seconds": record.elapsed_seconds,
            },
        ) from None

    if record.status == "cancelled":
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Investigation '{investigation_id}' was cancelled.",
        ) from None

    if record.status not in ("completed", "partial"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "The investigation does not have a report available yet."},
        )

    try:
        return manager.build_detail_response(record)
    except Exception:
        import logging

        logging.getLogger(__name__).exception(
            "Failed to assemble investigation result %s", investigation_id
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "message": "The investigation report could not be assembled. Please retry the investigation.",
                "error": "result_unavailable",
            },
        ) from None


@router.get(
    "/investigations",
    response_model=list[InvestigationStatusResponse],
    summary="List recent investigations",
)
async def list_investigations(
    limit: int = 50,
    manager: InvestigationManager = Depends(get_investigation_manager),
    user: AuthenticatedUser = Depends(get_current_user),
) -> list[InvestigationStatusResponse]:
    """Return durable investigation history for the authenticated user."""
    records = await manager.list_recent_owned(owner_id=user.user_id, limit=limit)
    return [manager.build_status_response(r) for r in records]


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Sanitized system health and dependency readiness",
)
async def get_health(
    settings: Settings = Depends(get_api_settings),
    manager: InvestigationManager = Depends(get_investigation_manager),
) -> HealthResponse:
    """Return health status without leaking secrets, API keys, or project tokens."""
    dependencies = {
        "openrouter_configured": bool(settings.openrouter_api_key),
        "posthog_configured": bool(settings.posthog_api_key),
        "zendesk_mock_configured": bool(settings.zendesk_base_url),
        "jira_mock_configured": bool(settings.jira_base_url),
        "langsmith_tracing_enabled": bool(settings.langsmith_tracing),
        "database_configured": bool(settings.database_url),
    }

    if manager.repository:
        dependencies["database_reachable"] = await manager.repository.healthcheck()

    # System is ok if primary model inference is configured
    is_ok = (
        dependencies["openrouter_configured"]
        and dependencies["database_configured"]
        and dependencies.get("database_reachable", False)
    )
    return HealthResponse(
        status="ok" if is_ok else "degraded",
        process="healthy",
        investigation_service_initialized=manager.service is not None,
        active_investigations_count=len(
            [
                r
                for r in manager.list_recent()
                if r.status not in ("completed", "failed", "cancelled")
            ]
        ),
        dependencies=dependencies,
    )
