"""
output.py — save triage results to CSV and JSON, print summary.
"""

import csv
import json
from collections import Counter
from pathlib import Path

from models import TriagedTicket


def save_csv(tickets: list[TriagedTicket], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "ticket_id",
        "category",
        "confidence",
        "escalate",
        "escalation_reason",
        "suggested_reply",
        "original_text",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in tickets:
            writer.writerow({
                "ticket_id": t.ticket_id,
                "category": t.category.value,
                "confidence": t.confidence,
                "escalate": t.escalate,
                "escalation_reason": t.escalation_reason or "",
                "suggested_reply": t.suggested_reply or "",
                "original_text": t.original_text[:300],  # truncate for readability
            })

    print(f"  ✓ CSV saved  → {path}")


def save_json(tickets: list[TriagedTicket], output_path: str) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = [t.model_dump() for t in tickets]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ JSON saved → {path}")


def print_summary(tickets: list[TriagedTicket]) -> None:
    total = len(tickets)
    escalated = sum(1 for t in tickets if t.escalate)
    replied = sum(1 for t in tickets if t.suggested_reply)
    cat_counts = Counter(t.category.value for t in tickets)

    print("\n" + "═" * 60)
    print("  SUPPORT TRIAGE SUMMARY")
    print("═" * 60)
    print(f"  Total tickets processed : {total}")
    print(f"  Escalated (needs human) : {escalated} ({escalated/total*100:.1f}%)")
    print(f"  Auto-reply drafted      : {replied}")
    print(f"\n  By category:")
    for cat, count in cat_counts.most_common():
        bar = "█" * int(count / total * 30)
        print(f"    {cat:<20} {count:>4}  {bar}")
    print("═" * 60 + "\n")
