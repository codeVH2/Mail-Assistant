from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware ##for frontend be able to call backend API without CORS issues

from config import settings

import routers.auth


app = FastAPI(
    title="PrivMail",
    description="Privacy-first AI email assistant",
    version="0.1.0",
    debug=settings.debug,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "ai_provider": settings.ai_provider}

app.include_router(routers.auth.router)
