"""
generator.py — two-step LLM pipeline:
  Step 1: Extract requirements from PRD text
  Step 2: Generate structured test cases from requirements
"""

import json
import os
import re
import time
from pathlib import Path

from google import genai
from models import Requirement, TestCase, TestPlan, RequirementType, Priority, TestType


# ── Prompt loading ──────────────────────────────────────────────────────────

PROMPTS_DIR = Path(__file__).parent / "prompts"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


# ── Gemini call ───────────────────────────────────────────────────────────────

def _call_claude(prompt: str, max_tokens: int = 4096, retries: int = 2) -> str:
    """Call Gemini and return the text response."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set.")
    
    for attempt in range(retries + 1):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            if attempt < retries:
                wait = 2 ** attempt * 3
                print(f"  Retrying in {wait}s... ({e})")
                time.sleep(wait)
            else:
                raise


# ── JSON parsing (robust) ────────────────────────────────────────────────────

def _parse_json(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned.strip(), flags=re.MULTILINE)
    cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model returned invalid JSON.\n"
            f"Parse error: {e}\n"
            f"Raw response (first 500 chars):\n{raw[:500]}"
        )


# ── Step 1: Requirement extraction ──────────────────────────────────────────

def extract_requirements(prd_text: str) -> tuple[str, list[Requirement]]:
    print("  → Step 1: Extracting requirements from PRD...")
    template = _load_prompt("extract_reqs.txt")
    prompt = template.replace("{prd_text}", prd_text)

    raw = _call_claude(prompt, max_tokens=2048)
    data = _parse_json(raw)

    prd_title = data.get("prd_title", "Untitled PRD")
    raw_reqs = data.get("requirements", [])

    requirements = []
    for r in raw_reqs:
        try:
            requirements.append(Requirement(
                req_id=r["req_id"],
                description=r["description"],
                req_type=RequirementType(r.get("req_type", "functional")),
            ))
        except Exception as e:
            print(f"  ⚠ Skipping malformed requirement {r.get('req_id', '?')}: {e}")

    print(f"  ✓ Extracted {len(requirements)} requirements")
    return prd_title, requirements


# ── Step 2: Test case generation ─────────────────────────────────────────────

def generate_test_cases(
    prd_title: str,
    requirements: list[Requirement],
) -> tuple[list[TestCase], list[str]]:
    print("  → Step 2: Generating test cases...")
    template = _load_prompt("generate_tests.txt")

    reqs_json = json.dumps([r.model_dump() for r in requirements], indent=2)
    prompt = (
        template
        .replace("{prd_title}", prd_title)
        .replace("{requirements_json}", reqs_json)
    )

    raw = _call_claude(prompt, max_tokens=8096)
    data = _parse_json(raw)

    raw_tcs = data.get("test_cases", [])
    coverage_gaps = data.get("coverage_gaps", [])

    test_cases = []
    for tc in raw_tcs:
        try:
            test_cases.append(TestCase(
                test_case_id=tc["test_case_id"],
                requirement_id=tc["requirement_id"],
                scenario=tc["scenario"],
                preconditions=tc.get("preconditions", []),
                steps=tc.get("steps", []),
                expected_result=tc["expected_result"],
                priority=Priority(tc.get("priority", "P1")),
                test_type=TestType(tc.get("test_type", "functional")),
            ))
        except Exception as e:
            print(f"  ⚠ Skipping malformed test case {tc.get('test_case_id', '?')}: {e}")

    print(f"  ✓ Generated {len(test_cases)} test cases")
    return test_cases, coverage_gaps


# ── Coverage check ────────────────────────────────────────────────────────────

def check_coverage(
    requirements: list[Requirement],
    test_cases: list[TestCase],
    coverage_gaps: list[str],
) -> list[str]:
    req_ids = {r.req_id for r in requirements}
    covered_ids = {tc.requirement_id for tc in test_cases}
    uncovered = req_ids - covered_ids

    all_gaps = list(coverage_gaps)
    for req_id in sorted(uncovered):
        req = next(r for r in requirements if r.req_id == req_id)
        gap_msg = f"{req_id}: No test cases generated — '{req.description[:80]}'"
        if gap_msg not in all_gaps:
            all_gaps.append(gap_msg)

    return all_gaps


# ── Main pipeline ─────────────────────────────────────────────────────────────

def generate_test_plan(prd_text: str) -> TestPlan:
    prd_title, requirements = extract_requirements(prd_text)
    test_cases, coverage_gaps = generate_test_cases(prd_title, requirements)
    final_gaps = check_coverage(requirements, test_cases, coverage_gaps)

    if final_gaps:
        print(f"  ⚠ Coverage gaps found: {len(final_gaps)}")
        for g in final_gaps:
            print(f"    - {g}")

    return TestPlan(
        prd_title=prd_title,
        requirements=requirements,
        test_cases=test_cases,
        coverage_gaps=final_gaps,
    )
