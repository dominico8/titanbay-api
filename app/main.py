import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.exceptions import DomainError


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

    register_exception_handlers(app)
    register_routers(app)

    return app


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(DomainError)
    async def domain_error_handler(_: Request, exc: DomainError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.__class__.__name__, "message": exc.message},
        )


def register_routers(app: FastAPI) -> None:
    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}


app = create_app()
