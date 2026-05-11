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

    print("No plain text body found in this email")
    return ""

# Reads a single header (e.g. "From", "Subject") from a Gmail message.
# Headers live in a list of {name, value} pairs — there's no direct dict lookup.
def extract_header(message, header_name):
    for header in message["payload"]["headers"]:
        if header["name"] == header_name:
            return header["value"]
    return ""


# Flattens a Gmail thread into "[sender]: body" lines so the LLM gets the full
# conversation as context, not just the latest message in isolation.
def build_conversation(thread, user_email):
    lines = []
    for msg in thread["messages"]:
        sender = extract_header(msg, "From")
        if user_email in sender:
            sender = "Me"
        body = extract_body(msg["payload"])
        lines.append(f"[{sender}]: {body}")
    return "\n\n".join(lines)


router = APIRouter()

# Returns the 10 most recent message IDs from the user's inbox.
# Body and metadata are NOT included — call /reply-suggest to fetch a specific email.
@router.get("/emails")
async def list_emails():
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)
    results = service.users().messages().list(userId="me", maxResults=10, labelIds=["INBOX"]).execute()
    return results


# Generates a reply suggestion for a given Gmail message.
# Email content lives only in memory during this call — never persisted.
@router.post("/reply-suggest")
async def reply_suggest(thread_id: str):
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)

    thread = service.users().threads().get(
        userId="me", id=thread_id, format="full").execute()
    
    profile = service.users().getProfile(userId="me").execute()
    conversation = build_conversation(thread, profile["emailAddress"])

    # Provider selected via AI_PROVIDER env var (local Ollama or cloud Anthropic)
    provider = get_provider()
    responseSuggestion = await provider.complete(
        f"""You are the recipient of the latest message in this email conversation.
            Write a short, natural reply to the latest message.
            Do not summarise the conversation. Reply as if you were the person being addressed.

            Conversation:
            {conversation}

            Your reply:"""
    )


    return {"respose": responseSuggestion}



    

    
