from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware ##for frontend be able to call backend API without CORS issues
from config import settings
from routers import auth, emails
from db.database import Base, engine
from db import models  #registers the table on Base.metadata, need this import

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Mail Assistant",
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
    return {"status": "ok",}

app.include_router(auth.router)
app.include_router(emails.router)

