import base64
import json
import re
from googleapiclient.discovery import build
from routers.auth import token_store
from fastapi import APIRouter, HTTPException
from providers.provider_factory import get_provider
from typing import Literal
from pydantic import BaseModel, Field, ValidationError
import html

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

def fetch_message_metadata(service, message_id: str) -> dict:
    msg = service.users().messages().get(userId="me", id=message_id, format="metadata", metadataHeaders=["Subject", "From"]).execute()

    return {
        "id": msg["id"],
        "threadId": msg["threadId"],
        "subject": extract_header(msg, "Subject"),
        "sender": extract_header(msg, "From"),
        # Gmail HTML-escapes the snippet for its own web UI; the body (text/plain) does not need this.
        "snippet": html.unescape(msg.get("snippet", "")), 
    }

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

# Returns metadata (subject, sender, snippet) for the 10 most recent inbox messages.
# Body is NOT fetched here — /reply-suggest and /prioritize fetch it per-message on demand.
@router.get("/emails")
async def list_emails():
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)
    results = service.users().messages().list(userId="me", maxResults=10, labelIds=["INBOX"]).execute()

    ids = []

    for msg in results.get("messages", []):
        ids.append(msg.get("id"))

    return [fetch_message_metadata(service, msg_id) for msg_id in ids]

# Returns the full content of a single Gmail message, including body.
@router.get("/emails/{message_id}")
async def get_email(message_id: str):
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)
    return fetch_message(service, message_id)

# Generates a reply suggestion for a given Gmail message.
# Email content lives only in memory during this call — never persisted.
@router.post("/emails/{message_id}/reply-suggest")
async def reply_suggest(message_id: str):
    credentials = token_store["credentials"]
    service = build("gmail", "v1", credentials=credentials)

    message = fetch_message(service, message_id) 

    # Provider selected via AI_PROVIDER env var (local Ollama or cloud Anthropic)
    provider = get_provider()
    responseSuggestion = await provider.complete(
        f"""You are the recipient of the email below.
            Write a short, natural reply to it.
            Reply as if you were the person being addressed.

            Email:
            {message['body']}

            Your reply:"""

    )

    return {"response": responseSuggestion}

@router.post("/emails/{message_id}/prioritize", response_model=PrioritizeResponse)
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

    




    

    
