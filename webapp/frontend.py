"""Serves the built React app (frontend/ -> `npm run build` -> webapp/static)."""

from pathlib import Path

from fastapi import FastAPI, status
from fastapi.responses import FileResponse, PlainTextResponse

STATIC_DIR = Path(__file__).resolve().parent / "static"


def register_frontend(app: FastAPI) -> None:
    """Catch-all route: files from STATIC_DIR, unknown paths get index.html (SPA routing).

    Must be registered after every other route.
    """

    @app.get("/{path:path}", include_in_schema=False, response_model=None)
    async def frontend(path: str) -> FileResponse | PlainTextResponse:
        index = STATIC_DIR / "index.html"
        if not index.is_file():
            return PlainTextResponse(
                "Frontend is not built: run `npm run build` in frontend/",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        file = (STATIC_DIR / path).resolve()
        if path and file.is_file() and file.is_relative_to(STATIC_DIR):
            # Hashed assets never change; index.html must always be fresh
            cache = "public, max-age=31536000, immutable" if path.startswith("assets/") else None
            return FileResponse(file, headers={"Cache-Control": cache} if cache else None)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})
