"""
output.py — write TestPlan to JSON and CSV formats.
"""

import csv
import json
from pathlib import Path
from models import TestPlan


def save_json(plan: TestPlan, output_path: str) -> None:
    """Save the full test plan (requirements + test cases + gaps) as JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    data = {
        "prd_title": plan.prd_title,
        "summary": {
            "total_requirements": len(plan.requirements),
            "total_test_cases": len(plan.test_cases),
            "coverage_gaps": len(plan.coverage_gaps),
            "by_priority": _count_by(plan, "priority"),
            "by_test_type": _count_by(plan, "test_type"),
        },
        "requirements": [r.model_dump() for r in plan.requirements],
        "test_cases": [tc.model_dump() for tc in plan.test_cases],
        "coverage_gaps": plan.coverage_gaps,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"  ✓ JSON saved → {path}")


def save_csv(plan: TestPlan, output_path: str) -> None:
    """
    Save test cases as CSV.
    Compatible with TestRail/Zephyr bulk import format.
    Steps and preconditions are newline-joined for readability.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "test_case_id",
        "requirement_id",
        "scenario",
        "preconditions",
        "steps",
        "expected_result",
        "priority",
        "test_type",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for tc in plan.test_cases:
            writer.writerow({
                "test_case_id": tc.test_case_id,
                "requirement_id": tc.requirement_id,
                "scenario": tc.scenario,
                "preconditions": "\n".join(tc.preconditions),
                "steps": "\n".join(tc.steps),
                "expected_result": tc.expected_result,
                "priority": tc.priority.value,
                "test_type": tc.test_type.value,
            })

    print(f"  ✓ CSV saved  → {path}")


def print_summary(plan: TestPlan) -> None:
    """Print a human-readable summary to stdout."""
    print("\n" + "═" * 60)
    print(f"  TEST PLAN: {plan.prd_title}")
    print("═" * 60)
    print(f"  Requirements : {len(plan.requirements)}")
    print(f"  Test cases   : {len(plan.test_cases)}")

    by_priority = _count_by(plan, "priority")
    print(f"  By priority  : {by_priority}")

    by_type = _count_by(plan, "test_type")
    print(f"  By type      : {by_type}")

    if plan.coverage_gaps:
        print(f"\n  ⚠ Coverage gaps ({len(plan.coverage_gaps)}):")
        for gap in plan.coverage_gaps:
            print(f"    • {gap}")
    else:
        print("\n  ✓ Full coverage — all requirements have test cases")
    print("═" * 60 + "\n")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _count_by(plan: TestPlan, field: str) -> dict:
    counts: dict = {}
    for tc in plan.test_cases:
        val = str(getattr(tc, field).value if hasattr(getattr(tc, field), "value") else getattr(tc, field))
        counts[val] = counts.get(val, 0) + 1
    return dict(sorted(counts.items()))
