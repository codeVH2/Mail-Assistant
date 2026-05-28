import base64
import json
import re
from googleapiclient.discovery import build
from routers.auth import token_store
from fastapi import APIRouter, HTTPException
from providers.provider_factory import get_provider
from typing import Literal
from pydantic import BaseModel, Field, ValidationError



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


def fetch_message(service, message_id: str) -> dict:
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    return {
        "subject": extract_header(msg, "Subject"),
        "sender": extract_header(msg, "From"),
        "body": extract_body(msg["payload"]),
    }


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

Category = Literal["urgent", "work", "personal", "newsletter", "promotional"]

class PrioritizeResponse(BaseModel):
    category: Category
    score: float = Field(ge=0.0, le=1.0)


def parse_llm_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    match = re.search(r"\{[^{}]*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output: {raw!r}")
    return json.loads(match.group(0))


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

    return {"response": responseSuggestion}

@router.post("/prioritize", response_model=PrioritizeResponse)
async def prioritize(message_id: str):
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)

    message = fetch_message(service, message_id)

    prompt = f"""You are an email classifier. Classify the email below into exactly one category and assign a relevance score.

                Categories (use exactly these names, lowercase, no quotes):
                - urgent: time-sensitive; requires action within hours (deadlines, problems, direct asks)
                - work: professional correspondence, not time-sensitive
                - personal: friends, family, personal life
                - newsletter: subscribed updates, digests, blogs
                - promotional: marketing, offers, ads, unsolicited promotions

                Precedence: if an email fits multiple categories, prefer the earlier one in this list (urgent > work > personal > newsletter > promotional).

                Score (0.0 to 1.0): how much the recipient should care about this email right now.
                - 0.0-0.2: ignore / archive
                - 0.3-0.5: read when convenient
                - 0.6-0.8: read soon
                - 0.9-1.0: read now

                Email:
                From: {message['sender']}
                Subject: {message['subject']}
                Body: {message['body']}

                Respond with ONLY a JSON object, no prose, no markdown fences:
                {{"category": "<one of the five>", "score": <float between 0 and 1>}}"""
    

    provider = get_provider()

    response = await provider.complete(prompt)
    
    try:
        parsed = parse_llm_json(response)
        return PrioritizeResponse(**parsed)
    except (ValueError, json.JSONDecodeError, ValidationError) as e:
        raise HTTPException(status_code=502, detail=f"LLM produced invalid output: {e}")

    




    

    
