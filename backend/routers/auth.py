from google_auth_oauthlib.flow import Flow

from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from config import settings

# Describes our app to Google. Same shape google_auth_oauthlib expects from the JSON downloaded
# from the Cloud Console — but we keep secrets in .env, not on disk.
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

# Step 1 of OAuth: build the Google login URL and send the browser there.
@router.get("/auth/gmail")
async def login_gmail():
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    
    flow.redirect_uri = settings.google_redirect_uri
    authorization_url, state = flow.authorization_url() ## URL where user goes with parameters from the client(the app)
    return RedirectResponse(authorization_url)

# Step 2 of OAuth: Google sends the user back here with a one-time `code`
# which we exchange for access + refresh tokens.
@router.get("/auth/callback")
async def gmail_callback(code: str):
    flow = Flow.from_client_config(
        client_config,
        scopes=["https://www.googleapis.com/auth/gmail.readonly"])
    
    flow.redirect_uri = settings.google_redirect_uri ##comfirm that the redirect is the same as the one used in the authorization step
    flow.fetch_token(code=code)
    token_store["credentials"] = flow.credentials ##acess token and refresh token stored
    return {"message": "Login successful"}
