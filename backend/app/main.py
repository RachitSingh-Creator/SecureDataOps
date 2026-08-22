import logging
import sys
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.api.users import router as users_router
from app.core.config import get_settings

settings = get_settings()

SERVICE_NAME = "securedataops"
REQUEST_ID_HEADER = "X-Request-ID"


def configure_logging() -> logging.Logger:
    logger = logging.getLogger(SERVICE_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not any(getattr(handler, "_securedataops_handler", False) for handler in logger.handlers):
        handler = logging.StreamHandler(sys.stdout)
        handler._securedataops_handler = True  # type: ignore[attr-defined]
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s service=securedataops "
                "logger=%(name)s message=%(message)s"
            )
        )
        logger.addHandler(handler)

    return logger


logger = configure_logging()

app = FastAPI(
    title="SecureDataOps",
    version="0.1.0",
    description="Phase 1 backend foundation for SecureDataOps.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.middleware("http")
async def observe_requests_and_add_security_headers(request: Request, call_next):
    request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled request error method=%s path=%s",
            request.method,
            request.url.path,
        )
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )

    duration_ms = (time.perf_counter() - started_at) * 1000
    response.headers[REQUEST_ID_HEADER] = request_id

    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"

    logger.info(
        "request request_id=%s method=%s path=%s status_code=%s duration_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response

@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(users_router, prefix="/api/v1")
