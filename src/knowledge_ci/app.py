"""Minimal HTTP entry point. T01 exposes health only."""

from fastapi import FastAPI

from knowledge_ci import __version__
from knowledge_ci.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings()
    app = FastAPI(title="Knowledge CI", version=__version__)
    app.state.settings = settings

    @app.get("/healthz", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    return app
