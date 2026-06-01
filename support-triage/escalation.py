"""
escalation.py — rule-based escalation only.
"""

import re
from models import Category, TriagedTicket

# Word boundary on "sue" so it doesn't match inside "issue"
HARD_ESCALATION_KEYWORDS = [
    "lawyer", "attorney", "legal action", r"\bsue\b", "lawsuit",
    "fraud", "scam", "chargeback",
    "data breach", "hacked", "unauthorized access",
    r"refund.*\$[1-9][0-9]{2}",
    "threatening", "abusive",
]

NEGATIVE_BILLING_WORDS = [
    "furious", "outrageous", "scammed", "incompetent",
]


def check_escalation(ticket: TriagedTicket) -> TriagedTicket:
    text_lower = ticket.original_text.lower()
    reasons = []

    for pattern in HARD_ESCALATION_KEYWORDS:
        if re.search(pattern, text_lower):
            reasons.append(f"keyword: '{pattern}'")
            break

    if ticket.category == Category.BILLING_REFUND:
        for word in NEGATIVE_BILLING_WORDS:
            if word in text_lower:
                reasons.append(f"negative billing sentiment: '{word}'")
                break

    if len(ticket.original_text.strip()) < 20:
        reasons.append("ticket too short")

    if reasons:
        ticket.escalate = True
        ticket.escalation_reason = "; ".join(reasons)

    return ticket


def apply_escalation_to_all(tickets: list[TriagedTicket]) -> list[TriagedTicket]:
    return [check_escalation(t) for t in tickets]
