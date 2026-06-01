"""
reply_drafter.py — draft suggested replies for the top 2 ticket categories.
"""

import os
import time
from collections import Counter
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
                temperature=0.4,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < retries:
                time.sleep(2 ** attempt * 2)
            else:
                raise


def get_top_categories(tickets: list[TriagedTicket], n: int = 2) -> list[Category]:
    counts = Counter(t.category for t in tickets)
    return [cat for cat, _ in counts.most_common(n)]


def draft_reply(ticket: TriagedTicket) -> str:
    template = _load_prompt("reply.txt")
    truncated = ticket.original_text[:1000] if len(ticket.original_text) > 1000 else ticket.original_text
    prompt = (
        template
        .replace("{category}", ticket.category.value)
        .replace("{ticket_text}", truncated)
    )
    return _call_groq(prompt)


def draft_replies_for_top_categories(
    tickets: list[TriagedTicket],
    delay: float = 0.2,
) -> list[TriagedTicket]:
    top_cats = get_top_categories(tickets, n=2)
    print(f"  ✓ Top 2 categories: {[c.value for c in top_cats]}")

    eligible = [t for t in tickets if t.category in top_cats and not t.escalate]
    print(f"  ✓ Drafting replies for {len(eligible)} tickets (non-escalated, top 2 categories)")

    ticket_map = {t.ticket_id: t for t in tickets}
    total = len(eligible)

    for i, ticket in enumerate(eligible):
        print(f"  Drafting reply {i+1}/{total} — {ticket.ticket_id}", end="\r")
        try:
            reply = draft_reply(ticket)
            ticket_map[ticket.ticket_id].suggested_reply = reply
        except Exception as e:
            ticket_map[ticket.ticket_id].suggested_reply = f"[Draft failed: {e}]"
        if delay and i < total - 1:
            time.sleep(delay)

    print(f"  ✓ Replies drafted{' ' * 30}")
    return list(ticket_map.values())
