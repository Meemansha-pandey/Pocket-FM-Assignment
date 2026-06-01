#!/usr/bin/env python3
"""
main.py — CLI entrypoint for PRD-to-Test-Cases Generator.

Usage:
    python main.py <prd_file> [--output-dir <dir>]

Examples:
    python main.py sample_prds/prd_login.md
    python main.py sample_prds/prd_payments.pdf --output-dir outputs/payments
"""

import argparse
import sys
import os
from pathlib import Path

from extractor import extract_text
from generator import generate_test_plan
from output import save_json, save_csv, print_summary


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a QA test plan from a PRD file (PDF, Markdown, or TXT).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "prd_file",
        help="Path to the PRD file (.pdf, .md, or .txt)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory to save JSON and CSV outputs (default: outputs/)",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    prd_path = args.prd_file
    output_dir = Path(args.output_dir)

    # ── Check API key ────────────────────────────────────────────────────────
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable is not set.")
        print("  Windows PowerShell: $env:GEMINI_API_KEY='your-key-here'")
        sys.exit(1)

    # ── Check input file ─────────────────────────────────────────────────────
    if not Path(prd_path).exists():
        print(f"ERROR: File not found: {prd_path}")
        sys.exit(1)

    print(f"\n{'─'*60}")
    print(f"  PRD → Test Plan Generator")
    print(f"{'─'*60}")
    print(f"  Input : {prd_path}")
    print(f"  Output: {output_dir}/")
    print(f"{'─'*60}\n")

    # ── Step 1: Extract text ─────────────────────────────────────────────────
    print("[ Extracting text from PRD... ]")
    try:
        prd_text = extract_text(prd_path)
    except Exception as e:
        print(f"ERROR during text extraction: {e}")
        sys.exit(1)

    char_count = len(prd_text)
    print(f"  ✓ Extracted {char_count:,} characters\n")

    if char_count < 100:
        print("WARNING: Very short PRD text. Results may be poor.")
    if char_count > 30_000:
        print("WARNING: PRD is very long. Consider splitting it for best results.")

    # ── Step 2: Generate test plan ───────────────────────────────────────────
    print("[ Running LLM pipeline... ]")
    try:
        plan = generate_test_plan(prd_text)
    except Exception as e:
        print(f"\nERROR during generation: {e}")
        sys.exit(1)

    # ── Step 3: Save outputs ──────────────────────────────────────────────────
    stem = Path(prd_path).stem
    print("\n[ Saving outputs... ]")
    save_json(plan, str(output_dir / f"{stem}_test_plan.json"))
    save_csv(plan,  str(output_dir / f"{stem}_test_plan.csv"))

    # ── Step 4: Print summary ─────────────────────────────────────────────────
    print_summary(plan)


if __name__ == "__main__":
    main()
