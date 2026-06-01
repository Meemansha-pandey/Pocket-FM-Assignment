"""
debug_escalation.py — run this once to see WHY tickets are being escalated.
Usage: python debug_escalation.py data/customer_support_tickets.csv
"""
import os, sys
import pandas as pd
from preprocessor import load_tickets
from classifier import classify_all
from escalation import apply_escalation_to_all, HARD_ESCALATION_KEYWORDS
import re

csv_path = sys.argv[1] if len(sys.argv) > 1 else "data/customer_support_tickets.csv"

# Load just 20 tickets
df = load_tickets(csv_path, max_tickets=20)
tickets = df.to_dict("records")

# Classify
os.environ.setdefault("GROQ_API_KEY", os.environ.get("GROQ_API_KEY", ""))
triaged = classify_all(tickets, delay=0.2)
triaged = apply_escalation_to_all(triaged)

print("\n── Escalation breakdown (20 tickets) ──")
for t in triaged:
    if t.escalate:
        print(f"\n[{t.ticket_id}] ESCALATED: {t.escalation_reason}")
        print(f"  text: {t.original_text[:150]}")
    else:
        print(f"[{t.ticket_id}] OK — {t.category.value} (conf={t.confidence})")

print(f"\nEscalated: {sum(1 for t in triaged if t.escalate)}/20")

# Also check which keywords are matching
print("\n── Keyword match test on first 20 tickets ──")
for t in triaged:
    text_lower = t.original_text.lower()
    for pattern in HARD_ESCALATION_KEYWORDS:
        if re.search(pattern, text_lower):
            print(f"  [{t.ticket_id}] matched pattern '{pattern}'")
            print(f"    text snippet: {t.original_text[:100]}")
            break
