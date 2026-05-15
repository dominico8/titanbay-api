import logging
import uuid
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.config import get_settings
from app.exceptions import (
    ConflictError,
    DomainError,
    NotFoundError,
    ValidationError,
)
from app.routers import funds_router, investments_router, investors_router

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"

_DOMAIN_ERROR_CODES: dict[type[DomainError], str] = {
    NotFoundError: "NOT_FOUND",
    ConflictError: "CONFLICT",
    ValidationError: "VALIDATION_ERROR",
}


def _error_response(
    request: Request,
    status_code: int,
    code: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    error: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        error["details"] = details
    request_id = getattr(request.state, "request_id", None)
    if request_id is not None:
        error["request_id"] = request_id
    headers = {REQUEST_ID_HEADER: request_id} if request_id is not None else None
    return JSONResponse(
        status_code=status_code,
        content=jsonable_encoder({"error": error}),
        headers=headers,
    )


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


def create_app() -> FastAPI:
    settings = get_settings()

    logging.basicConfig(
        level=settings.log_level,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

    app = FastAPI(
        title="Titanbay API",
        version="0.1.0",
        description="REST API for the Titanbay private markets fund management platform.",
    )

    app.add_middleware(RequestIDMiddleware)

    register_exception_handlers(app)
    register_routers(app)

    return app


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
        code = _DOMAIN_ERROR_CODES.get(type(exc), "INTERNAL_ERROR")
        return _error_response(request, exc.status_code, code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def request_validation_error_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception", exc_info=exc)
        return _error_response(
            request,
            status_code=500,
            code="INTERNAL_ERROR",
            message="An internal error occurred",
        )


def register_routers(app: FastAPI) -> None:
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(funds_router)
    app.include_router(investors_router)
    app.include_router(investments_router)


app = create_app()
