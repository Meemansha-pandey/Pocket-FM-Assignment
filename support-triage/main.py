#!/usr/bin/env python3
"""
main.py — Support Triage Agent for PocketToons

Usage:
    python main.py data/customer_support_tickets.csv
    python main.py data/customer_support_tickets.csv --max 100
    python main.py data/customer_support_tickets.csv --output-dir outputs/run1
"""

import argparse
import os
import sys
from pathlib import Path

from preprocessor import load_tickets
from classifier import classify_all
from escalation import apply_escalation_to_all
from reply_drafter import draft_replies_for_top_categories
from output import save_csv, save_json, print_summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI support ticket triage agent for PocketToons.",
    )
    parser.add_argument("csv_file", help="Path to support tickets CSV file")
    parser.add_argument("--max", type=int, default=200, help="Max tickets to process (default: 200)")
    parser.add_argument("--output-dir", default="outputs", help="Output directory (default: outputs/)")
    return parser.parse_args()


def main():
    args = parse_args()
    output_dir = Path(args.output_dir)

    # ── Check API key ────────────────────────────────────────────────────────
    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable is not set.")
        print("  Windows PowerShell: $env:GROQ_API_KEY='your-groq-key-here'")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"  Support Triage Agent — PocketToons")
    print(f"{'─'*60}")
    print(f"  Input  : {args.csv_file}")
    print(f"  Max    : {args.max} tickets")
    print(f"  Output : {output_dir}/")
    print(f"{'─'*60}\n")

    # ── Step 1: Load & preprocess ────────────────────────────────────────────
    print("[ Step 1: Loading tickets... ]")
    try:
        df = load_tickets(args.csv_file, max_tickets=args.max)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    tickets_raw = df.to_dict("records")
    print(f"  ✓ Ready to process {len(tickets_raw)} tickets\n")

    # ── Step 2: Classify ─────────────────────────────────────────────────────
    print("[ Step 2: Classifying tickets... ]")
    triaged = classify_all(tickets_raw)
    print()

    # ── Step 3: Escalation ───────────────────────────────────────────────────
    print("[ Step 3: Applying escalation rules... ]")
    triaged = apply_escalation_to_all(triaged)
    escalated_count = sum(1 for t in triaged if t.escalate)
    print(f"  ✓ {escalated_count} tickets flagged for escalation\n")

    # ── Step 4: Draft replies ────────────────────────────────────────────────
    print("[ Step 4: Drafting replies for top 2 categories... ]")
    triaged = draft_replies_for_top_categories(triaged)
    print()

    # ── Step 5: Save outputs ─────────────────────────────────────────────────
    print("[ Step 5: Saving outputs... ]")
    save_csv(triaged, str(output_dir / "triaged_tickets.csv"))
    save_json(triaged, str(output_dir / "triaged_tickets.json"))

    # ── Summary ──────────────────────────────────────────────────────────────
    print_summary(triaged)


if __name__ == "__main__":
    main()
