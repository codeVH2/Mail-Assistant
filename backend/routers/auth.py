from google_auth_oauthlib.flow import Flow

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from config import settings

client_config = {
    "web": {
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uris": [settings.google_redirect_uri],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

router = APIRouter()

# Stores OAuth credentials in memory for the duration of the server process
token_store: dict = {}

@router.get("/auth/gmail")
async def login_gmail():
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    
    flow.redirect_uri = settings.google_redirect_uri
    authorization_url, state = flow.authorization_url()
    return RedirectResponse(authorization_url)

@router.get("/auth/callback")
async def gmail_callback(code: str):
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    
    flow.redirect_uri = settings.google_redirect_uri
    flow.fetch_token(code=code)
    token_store["credentials"] = flow.credentials
    return {"message": "Login successful"}
