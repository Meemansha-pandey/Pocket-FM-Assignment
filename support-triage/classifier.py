"""
classifier.py — classify support tickets using Groq.
"""

import json
import os
import re
import time
from pathlib import Path

from groq import Groq
from models import Category, TriagedTicket

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def _call_groq(prompt: str, retries: int = 2) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is not set.")
    client = Groq(api_key=api_key)
    for attempt in range(retries + 1):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200,
            )
            return response.choices[0].message.content
        except Exception as e:
            err = str(e)
            if "429" in err or "quota" in err.lower() or "rate" in err.lower():
                wait = 2 ** attempt * 5
                print(f"\n  Rate limited. Waiting {wait}s...")
                time.sleep(wait)
            elif attempt < retries:
                time.sleep(2)
            else:
                raise RuntimeError(f"Groq API error: {e}") from e


def _parse_json(raw: str) -> dict:
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    return json.loads(cleaned.strip())


def classify_ticket(ticket_id: str, text: str) -> TriagedTicket:
    template = _load_prompt("classify.txt")
    truncated = text[:1500] if len(text) > 1500 else text
    prompt = template.replace("{ticket_text}", truncated)

    try:
        raw = _call_groq(prompt)
        data = _parse_json(raw)
        category = Category(data.get("category", "general_feedback"))
        confidence = int(data.get("confidence", 3))
        confidence = max(1, min(5, confidence))
    except Exception as e:
        category = Category.GENERAL_FEEDBACK
        confidence = 1

    return TriagedTicket(
        ticket_id=ticket_id,
        original_text=text,
        category=category,
        confidence=confidence,
    )


def classify_all(tickets: list[dict], delay: float = 0.2) -> list[TriagedTicket]:
    results = []
    total = len(tickets)
    for i, row in enumerate(tickets):
        print(f"  Classifying {i+1}/{total} — {row['ticket_id']}", end="\r")
        result = classify_ticket(row["ticket_id"], row["text"])
        results.append(result)
        if delay and i < total - 1:
            time.sleep(delay)
    print(f"  ✓ Classified {total} tickets{' ' * 30}")
    return results
