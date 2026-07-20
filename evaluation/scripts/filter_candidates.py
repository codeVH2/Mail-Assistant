"""Pre-filter Berkeley Enron candidates for the evaluation dataset.

Reads emails from folder 1 (Company Business -> work) and folder 2
(Purely Personal -> personal), keeps only those with 2-annotator
agreement on the primary coarse-genre label, and applies quality
filters (body length, no forward chains, no heavy quoting).

Outputs:
    evaluation/dataset/candidates_work.json
    evaluation/dataset/candidates_personal.json
"""

from __future__ import annotations

import json
import re
from email import message_from_string
from email.message import Message
from pathlib import Path

RAW_ROOT = Path(__file__).resolve().parent.parent / "raw_data" / "enron_with_categories"
DATASET_ROOT = Path(__file__).resolve().parent.parent / "dataset"

# Patterns that mark the start of a quoted/forwarded section: we cut the body
# here and keep only the text above. The original message is what we want.
QUOTE_SPLIT_PATTERNS = [
    re.compile(r"-+\s*Forwarded by", re.IGNORECASE),
    re.compile(r"-+\s*Original Message", re.IGNORECASE),
    re.compile(r"<\S+@\S+>\s+on\s+\d", re.IGNORECASE),
    re.compile(r"^\s*Sent by:\s", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*To:\s+\S+@", re.MULTILINE),
    re.compile(r"^\s*From:\s+\S+@", re.MULTILINE),
    re.compile(r"\d{1,2}/\d{1,2}/\d{2,4}\s+\d{1,2}:\d{2}"),
    re.compile(r"wrote:\s*$", re.IGNORECASE | re.MULTILINE),
]

# Patterns that disqualify the email entirely — inline quote markers can't be
# cleanly stripped without destroying the original.
HARD_REJECT_PATTERNS = [
    re.compile(r"^\s*>+\s", re.MULTILINE),
]

MIN_WORDS = 20
MAX_WORDS = 400


def parse_cats(cats_path: Path) -> list[tuple[int, int, int]]:
    labels: list[tuple[int, int, int]] = []
    for line in cats_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(",")
        if len(parts) == 3:
            labels.append((int(parts[0]), int(parts[1]), int(parts[2])))
    return labels


def has_label(labels: list[tuple[int, int, int]], target: tuple[int, int, int]) -> bool:
    return target in labels


def extract_body(msg: Message) -> str:
    payload = msg.get_payload()
    if isinstance(payload, list):
        for part in payload:
            if part.get_content_type() == "text/plain":
                raw = part.get_payload(decode=True)
                if isinstance(raw, bytes):
                    return raw.decode("utf-8", errors="replace")
        return ""
    return payload if isinstance(payload, str) else ""


def is_hard_reject(body: str) -> bool:
    return any(p.search(body) for p in HARD_REJECT_PATTERNS)


def clean_body(body: str) -> str:
    """Trim everything from the first quote/forward marker onward."""
    earliest = len(body)
    for pattern in QUOTE_SPLIT_PATTERNS:
        match = pattern.search(body)
        if match and match.start() < earliest:
            earliest = match.start()
    return body[:earliest].rstrip()


def word_count(text: str) -> int:
    return len(text.split())


def filter_folder(folder: int, target_label: tuple[int, int, int]) -> list[dict]:
    folder_path = RAW_ROOT / str(folder)
    candidates: list[dict] = []

    for cats_file in sorted(folder_path.glob("*.cats")):
        labels = parse_cats(cats_file)
        if not has_label(labels, target_label):
            continue

        txt_file = cats_file.with_suffix(".txt")
        if not txt_file.exists():
            continue

        raw = txt_file.read_text(encoding="utf-8", errors="replace")
        msg = message_from_string(raw)
        body = extract_body(msg).strip()

        if is_hard_reject(body):
            continue

        body = clean_body(body)
        wc = word_count(body)
        if not (MIN_WORDS <= wc <= MAX_WORDS):
            continue

        candidates.append(
            {
                "id": cats_file.stem,
                "folder": str(folder),
                "source_path": str(txt_file.relative_to(RAW_ROOT.parent.parent)),
                "from": msg.get("From", ""),
                "to": msg.get("To", ""),
                "subject": msg.get("Subject", ""),
                "date": msg.get("Date", ""),
                "body": body,
                "word_count": wc,
                "labels": [list(t) for t in labels],
            }
        )

    candidates.sort(key=lambda c: c["word_count"])
    return candidates


def main() -> None:
    DATASET_ROOT.mkdir(parents=True, exist_ok=True)

    work = filter_folder(folder=1, target_label=(1, 1, 2))
    personal = filter_folder(folder=2, target_label=(1, 2, 2))

    (DATASET_ROOT / "candidates_work.json").write_text(
        json.dumps(work, indent=2, ensure_ascii=False)
    )
    (DATASET_ROOT / "candidates_personal.json").write_text(
        json.dumps(personal, indent=2, ensure_ascii=False)
    )

    print(f"work candidates:     {len(work):4d}  -> evaluation/dataset/candidates_work.json")
    print(f"personal candidates: {len(personal):4d}  -> evaluation/dataset/candidates_personal.json")


if __name__ == "__main__":
    main()