"""FastAPI application factory for PMLytics AI."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from mocks.lifecycle import ensure_mock_services_running, stop_mock_services

from app.api.dependencies import get_investigation_manager
from app.api.routes import router
from app.config.settings import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Ensure Mock Zendesk and Mock Jira servers are running locally."""
    ensure_mock_services_running()
    manager = get_investigation_manager()
    await manager.service.start()
    await manager.recover_incomplete_investigations()
    yield
    await manager.service.close()
    if manager.repository:
        await manager.repository.close()
    stop_mock_services()


def create_app() -> FastAPI:
    """Instantiate and configure the authoritative FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="PMLytics AI API",
        version="1.0.0",
        description=(
            "AI-powered multi-agent product discovery system investigating customer support, "
            "product analytics, and engineering context for Product Managers."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # 1. Configurable CORS (Rejects unexpected origins, no permissive wildcard in production)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 2. Register API Routes
    app.include_router(router)

    # 3. Standardized Error Handlers
    from fastapi.encoders import jsonable_encoder

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error_code": "VALIDATION_ERROR",
                "message": "Invalid request payload.",
                "details": jsonable_encoder(exc.errors()),
            },
        )

    return app


app = create_app()
