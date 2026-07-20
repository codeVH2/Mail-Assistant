from __future__ import annotations

import asyncio
import json
import re
import sys
from pathlib import Path

# --- Make the backend importable ---------------------------------------------
# The providers live in backend/ and do `from config import settings`, so
# backend/ must be on sys.path for the imports below to resolve.
BACKEND = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND))

from providers.local_provider import LocalProvider  
from providers.cloud_provider import CloudProvider 

# --- Config ------------------------------------------------------------------
DATASET = Path(__file__).resolve().parents[1] / "dataset" / "eval_set.json"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
N_RUNS = 3


# --- Prompt ------------------------------------------------------------------
# IMPORTANT: this MUST be the same prompt the product sends in
# backend/routers/emails.py (the /prioritize handler). If the two drift, the
# study no longer measures what the product ships.
# Decision to make: either import a shared prompt builder from the backend, or
# copy the prompt here and keep it in sync manually.
def build_prioritize_prompt(email: dict) -> str:
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
                From: {email["from"]}
                Subject: {email["subject"]}
                Body: {email["body"]}

                Respond with ONLY a JSON object, no prose, no markdown fences:
                {{"category": "<one of the five>", "score": <float between 0 and 1>}}"""
    
    return prompt
    




# --- Parsing -----------------------------------------------------------------
def parse_llm_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    match = re.search(r"\{[^{}]*\}", cleaned, flags=re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in LLM output: {raw!r}")
    return json.loads(match.group(0))


# --- Core --------------------------------------------------------------------
async def evaluate(provider, provider_name: str, emails: list[dict]) -> list[dict]:
    """Run every email through one provider N_RUNS times; return flat records."""
    records: list[dict] = []
    for email in emails:
        prompt = build_prioritize_prompt(email)
        for run in range(N_RUNS):

            raw = await provider.complete(prompt)

            try:
                parsed = parse_llm_json(raw)
                category_from_ai = parsed["category"]
                score_from_ai = parsed["score"]
            except (ValueError, json.JSONDecodeError, KeyError) as e:
                category_from_ai = None
                score_from_ai = None
                print(f"Error parsing LLM output for email {email['id']} (run {run}): {e}")
                print(f"Raw LLM output: {raw!r}")

            records.append(
                {
                    "id": email["id"],
                    "category_gold": email["category"],
                    "score_gold": email["score_gold"],
                    "provider": provider_name,
                    "run": run,
                    "categoryFromAI": category_from_ai,
                    "scoreFromAI": score_from_ai,
                    "raw": raw,
                }
            )

    return records


async def main() -> None:
    emails = json.loads(DATASET.read_text())
    RESULTS_DIR.mkdir(exist_ok=True)

    local_records = await evaluate(LocalProvider(), "local", emails)
    (RESULTS_DIR / "local.json").write_text(json.dumps(local_records, indent=2))

    cloud_records = await evaluate(CloudProvider(), "cloud", emails)
    (RESULTS_DIR / "cloud.json").write_text(json.dumps(cloud_records, indent=2))



if __name__ == "__main__":
    asyncio.run(main())
