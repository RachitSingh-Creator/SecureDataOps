from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.users import router as users_router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="SecureDataOps",
    version="0.1.0",
    description="Phase 1 backend foundation for SecureDataOps.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "healthy"}


app.include_router(users_router, prefix="/api/v1")
