from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, materials, topics
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="Tutor API",
    description="API for Tutor Bot — personalized study assistant",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(materials.router)
app.include_router(topics.router)


@app.on_event("startup")
async def startup() -> None:
    pass


@app.on_event("shutdown")
async def shutdown() -> None:
    pass
