from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# --- Make the backend importable ---------------------------------------------
# Same setup as run_evaluation.py: the providers live in backend/ and do
# `from config import settings`, so backend/ must be on sys.path.
BACKEND = Path(__file__).resolve().parents[2] / "backend"
sys.path.insert(0, str(BACKEND))

from providers.local_provider import LocalProvider
from providers.cloud_provider import CloudProvider

# --- Config ------------------------------------------------------------------
DATASET = Path(__file__).resolve().parents[1] / "dataset" / "reply_set.json"
RESULTS_DIR = Path(__file__).resolve().parents[1] / "results"
# N=1 on purpose: this feeds a human A/B preference test, not repeated sampling.
# One reply per provider per email → 12 replies for 6 emails.


# --- Prompt ------------------------------------------------------------------
# This is the prompt Study 2 was run with, kept here verbatim so the published
# results stay reproducible from this file alone. It is a standalone copy, not a
# shared import: the /reply-suggest handler in backend/routers/emails.py was
# later simplified to address a single email rather than a conversation, so the
# two wordings are no longer identical. The divergence is discussed in the
# thesis; do not edit this prompt, or the results here stop being reproducible.
# Each reply_set item is one inbound email, so the conversation is a single line.
def build_reply_prompt(email: dict) -> str:
    conversation = f"[{email['from']}]: {email['body']}"
    return f"""You are the recipient of the latest message in this email conversation.
            Write a short, natural reply to the latest message.
            Do not summarise the conversation. Reply as if you were the person being addressed.

            Conversation:
            {conversation}

            Your reply:"""


# --- Core --------------------------------------------------------------------
async def evaluate(provider, provider_name: str, emails: list[dict]) -> list[dict]:
    """Generate one reply per email for a single provider."""
    records: list[dict] = []
    for email in emails:
        prompt = build_reply_prompt(email)
        reply = await provider.complete(prompt)
        records.append(
            {
                "id": email["id"],
                "from": email["from"],
                "provider": provider_name,
                "reply": reply.strip(),
            }
        )
    return records


def write_pairs_txt(emails: list[dict], local: list[dict], cloud: list[dict]) -> Path:
    """Human-readable side-by-side dump for building the Google Form by hand."""
    local_by_id = {r["id"]: r["reply"] for r in local}
    cloud_by_id = {r["id"]: r["reply"] for r in cloud}
    blocks = []
    for e in emails:
        blocks.append(
            f"==================== {e['id']} (from {e['from']}) ====================\n"
            f"ORIGINAL EMAIL:\n{e['body']}\n\n"
            f"--- LOCAL (llama3.1:8b) ---\n{local_by_id[e['id']]}\n\n"
            f"--- CLOUD (Sonnet 4.6) ---\n{cloud_by_id[e['id']]}\n"
        )
    out = RESULTS_DIR / "reply_pairs.txt"
    out.write_text("\n\n".join(blocks), encoding="utf-8")
    return out


async def main() -> None:
    emails = json.loads(DATASET.read_text())
    RESULTS_DIR.mkdir(exist_ok=True)

    local = await evaluate(LocalProvider(), "local", emails)
    (RESULTS_DIR / "reply_local.json").write_text(
        json.dumps(local, indent=2, ensure_ascii=False)
    )

    cloud = await evaluate(CloudProvider(), "cloud", emails)
    (RESULTS_DIR / "reply_cloud.json").write_text(
        json.dumps(cloud, indent=2, ensure_ascii=False)
    )

    write_pairs_txt(emails, local, cloud)
    print(
        f"wrote reply_local.json, reply_cloud.json and reply_pairs.txt "
        f"({len(emails)} emails × 2 providers) to results/"
    )


if __name__ == "__main__":
    asyncio.run(main())
