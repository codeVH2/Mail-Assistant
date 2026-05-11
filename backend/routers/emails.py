import base64

from googleapiclient.discovery import build
from routers.auth import token_store
from fastapi import APIRouter
from providers.provider_factory import get_provider


# Gmail returns either a simple body or a multipart payload (HTML + plain text + attachments).
# This helper handles both and returns the plain-text version, base64 decoded.
def extract_body(payload):
    if "data" in payload.get("body", {}):
        data = payload["body"]["data"]
        return base64.urlsafe_b64decode(data).decode("utf-8")

    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/plain":
            data = part["body"]["data"]
            return base64.urlsafe_b64decode(data).decode("utf-8")

    return ""


router = APIRouter()

# Returns the 10 most recent message IDs from the user's inbox.
# Body and metadata are NOT included — call /reply-suggest to fetch a specific email.
@router.get("/emails")
async def list_emails():
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)
    results = service.users().messages().list(userId="me", maxResults=10).execute()
    return results


# Generates a reply suggestion for a given Gmail message.
# Email content lives only in memory during this call — never persisted.
@router.post("/reply-suggest")
async def reply_suggest(message_id: str):
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)

    # Fetch the email
    message = service.users().messages().get(
        userId="me", id=message_id, format="full"
    ).execute()

    # Decode body from base64
    body_text = extract_body(message["payload"])

    # Provider selected via AI_PROVIDER env var (local Ollama or cloud Anthropic)
    provider = get_provider()
    responseSuggestion = await provider.complete(
        f"Suggest short answer for this email:\n\n{body_text}"
    )

    return {"respose": responseSuggestion}



    

    
