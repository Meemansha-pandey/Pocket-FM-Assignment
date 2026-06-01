# PRD-to-Test-Cases Generator

An AI-powered tool that converts a Product Requirements Document (PDF, Markdown, or plain text) into a structured QA test plan — covering happy paths, edge cases, and negative scenarios.

Built as a take-home assignment for PocketToons (PocketFM) Applied AI Engineer role.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your Anthropic API key
export ANTHROPIC_API_KEY=sk-ant-...

# 3. Run on a PRD
python main.py sample_prds/prd_offline_reading.md
python main.py sample_prds/prd_linear_priority_microadjust.md --output-dir outputs/linear
```

Outputs land in `outputs/` as both `.json` and `.csv`.

---

## Project Structure

```
prd-to-testcases/
├── main.py                                      # CLI entrypoint
├── extractor.py                                 # PDF/MD/TXT → plain text
├── generator.py                                 # Two-step LLM pipeline
├── models.py                                    # Pydantic schemas
├── output.py                                    # JSON + CSV writers
├── requirements.txt
├── prompts/
│   ├── extract_reqs.txt                         # Prompt 1: requirement extraction
│   └── generate_tests.txt                       # Prompt 2: test case generation
├── sample_prds/
│   ├── prd_offline_reading.md                   # PRD 1: PocketToons offline reading mode
│   └── prd_linear_priority_microadjust.md       # PRD 2: Linear priority micro-adjust (real, public PRD)
└── outputs/                                     # Generated test plans (JSON + CSV)
```

---

## Output Format

Each test case contains:

| Field | Description |
|---|---|
| `test_case_id` | Unique ID (TC-001, TC-002 …) |
| `requirement_id` | Linked requirement (REQ-001 …) |
| `scenario` | One-line description of what is tested |
| `preconditions` | All setup required before the test runs |
| `steps` | Numbered, executable steps a junior tester can follow |
| `expected_result` | The pass condition |
| `priority` | P0 / P1 / P2 |
| `test_type` | functional / edge / negative |

The JSON output also includes a `coverage_gaps` array listing any requirements that have no generated test cases.

---

## Sample PRDs Used

### PRD 1 — PocketToons Offline Reading Mode
A fictional PRD written for this assignment. Covers download management, DRM, storage limits, expiry, and offline library UX — chosen because it has rich edge cases (metered connections, storage full, subscription lapse, content removed from platform) that stress-test the generator's ability to surface non-obvious negative cases.

### PRD 2 — Linear Priority Micro-Adjust
A real, publicly available PRD written by Nan Yu (PM at Linear). Source: [linkedin.com/feed/update/urn:li:activity:7264312237106860033](https://www.linkedin.com/feed/update/urn:li:activity:7264312237106860033). This PRD was chosen because it is compact but non-trivial: it has interaction-level functional requirements (drag-and-drop edge cases, cross-bucket behaviour), non-functional requirements (latency, real-time sync), and an explicit migration requirement (bootstrapping from manual sort). It is a good stress-test for whether the tool can handle an interaction-heavy PRD rather than a form-based one.

---

## Write-Up

### 1. Prompt Strategy and Why

The core design decision is a **two-step pipeline** rather than a single end-to-end prompt.

**Step 1 — Requirement Extraction**

The PRD is sent to Claude with a prompt asking it to extract discrete, atomic, testable requirements and label each as `functional`, `non-functional`, or `constraint`. This step forces structured decomposition of the document before any test cases are generated.

Why this matters: a single "PRD → test cases" prompt tends to miss implicit requirements and produces uneven coverage across the document. By separating extraction from generation, we get a requirements list we can reason about independently — and run a coverage check against after generation.

**Step 2 — Test Case Generation**

The structured requirements list (as JSON) is passed to Claude with explicit rules: every requirement needs at least one test case; functional requirements need a happy path, an edge case, and a negative case; constraints need boundary and violation tests. The prompt specifies step granularity ("a junior tester should be able to follow these without interpretation") and precondition completeness.

Passing requirements as structured JSON — rather than re-sending the full PRD text — gives the model a tighter, more focused input and reduces the risk of the model inventing requirements that do not exist in the document.

**Coverage check**

After generation, the code cross-references every `req_id` from Step 1 against the `requirement_id` values in the generated test cases. Gaps are flagged in both the terminal output and the `coverage_gaps` field of the JSON output. This is the bonus feature — and it falls out naturally from the two-step design.

**Model choice:** `claude-opus-4-5`. The task demands reasoning about implicit requirements, security edge cases, and interaction subtleties (e.g. what happens mid-drag when a connection drops). A cheaper model would produce shallower tests. This is an offline batch job so latency is not a constraint; using the strongest available model is the right call.

**Prompt versioning:** Prompts are stored as plain text files in `prompts/` rather than being hardcoded into `generator.py`. This makes prompt iteration fast and keeps a natural git history of prompt changes — important for tracing regressions if output quality degrades.

---

### 2. Where This Would Fail or Produce Bad Output

**Vague or ambiguous PRDs.** "The system should be performant" generates a test case shell with no meaningful acceptance criteria. The tool cannot invent thresholds that the PRD omits. A pre-generation quality check prompt could flag under-specified requirements before wasting an LLM call on them.

**Implicit requirements.** If a PRD assumes platform behaviour (e.g. "follows iOS HIG guidelines"), the model may or may not surface that as a requirement depending on how prominent it is in the text. Coverage is only as good as what the model can infer from the document.

**Very long PRDs.** The current implementation warns when the PRD exceeds 30,000 characters but does not handle it. A chunking strategy — extract requirements per section, then deduplicate — would be needed for large documents.

**Phantom requirement IDs.** The model occasionally generates a `requirement_id` in a test case that does not exist in the extracted requirements list (e.g. `REQ-015` when only 12 requirements were extracted). The coverage checker catches this as an uncovered requirement but does not catch the phantom reference directly. A simple post-processing validation pass would close this gap.

**Step-level vagueness.** Steps like "Navigate to the settings page" without specifying which settings screen are technically correct but not useful. This is hard to prevent purely with prompting — human review of P0 tests before they enter a test suite is essential.

**Non-determinism.** Two runs on the same PRD may produce different test counts or different requirement groupings. For audit trails, saving the raw LLM response alongside the parsed output matters.

---

### 3. Guardrails for Production

| Guardrail | Status | Notes |
|---|---|---|
| Pydantic schema validation | ✅ Implemented | Malformed test cases are logged and skipped, not crashed |
| Coverage check | ✅ Implemented | Any requirement with zero test cases is flagged |
| Retry on rate limit | ✅ Implemented | Exponential backoff, 2 retries |
| PRD quality pre-check | ❌ Not implemented | A prompt scoring PRD clarity and flagging under-specified requirements before generation would save tokens and improve output |
| Phantom ID validation | ❌ Not implemented | Post-process check that all `requirement_id` values in test cases exist in the extracted requirements list |
| Step vagueness detector | ❌ Not implemented | Heuristic or model-based check flagging steps shorter than N words or missing a subject |
| Human review queue for P0 | ❌ Not implemented | Any P0 test case should require explicit human sign-off before entering the test suite |
| Prompt versioning in output | ❌ Not implemented | Saving the prompt version used alongside each output file enables regression tracking |
| Cost tracking | ❌ Not implemented | Log token usage per run; a large PRD can be expensive if run repeatedly |
| Duplicate detection | ❌ Not implemented | Near-duplicate test cases (same scenario, same steps) should be merged before saving |

---

### 4. How a Human QA Engineer Integrates This Into Their Workflow

This tool is a **force multiplier for QA, not a replacement**. Here is the intended workflow:

```
PM writes PRD
      ↓
Tool generates draft test plan  (~90 seconds)
      ↓
QA Engineer reviews the draft:
  - Reads coverage_gaps and fills missing tests manually
  - Edits vague steps to reference specific UI elements
  - Approves or escalates all P0 cases — never auto-import
  - Deletes duplicate or irrelevant cases
      ↓
Import CSV into TestRail / Zephyr / Linear
      ↓
QA executes tests, logs results against the linked requirement IDs
```

**What the tool handles well (~60% of the work):**
- Generating the full scaffold of obvious test cases so QA never starts from a blank page
- Ensuring no requirement is completely untested
- Surfacing negative and edge cases that are easy to deprioritise under sprint pressure
- Producing the coverage gaps report so QA knows exactly where manual effort is needed

**What the QA engineer must own (the other 40%):**
- Judgment on priority — the model's P0/P1/P2 assignments are a starting point, not a decision
- Test data setup — the tool cannot know your environment's test accounts, seed data, or infrastructure
- Integration and end-to-end tests that span multiple PRDs or features
- Updating test cases when requirements change mid-sprint

The framing matters: this tool automates the mechanical first pass. The QA engineer's job is to review, correct, and own the output — not to run every generated test case uncritically.

---

## What I Would Add With More Time

**TestRail-native CSV format.** Export in TestRail's exact import schema (Section, Title, Steps, Expected Result columns with their specific delimiters) for zero-friction import rather than requiring the QA team to remap columns.

**PRD diff mode.** Given a previous test plan JSON and an updated PRD, generate only the delta — new tests for changed requirements, and flag test cases that are now stale because their requirement was removed or changed.

**Confidence scores per test case.** Ask the model to rate its own confidence (1–5) for each generated test case, surfacing low-confidence cases as the priority review queue for QA. Useful when a PRD has ambiguous requirements.

**Small eval set with metrics.** 20 hand-labelled PRD → test case pairs with precision/recall on requirement coverage would be the minimum honest evaluation of whether the tool actually works. I would have built this within the time budget but prioritised the write-up and the real PRD integration instead. The right eval metric here is not accuracy but coverage recall: of all the requirements a human QA would have tested, what fraction did the tool surface?

**Streamlit UI.** A simple file-upload interface so non-technical PMs and QA leads can run the tool without touching the CLI. Two inputs (upload PRD, click Generate), two outputs (download JSON, download CSV).

---

## Dependencies

- `anthropic` — Claude API client
- `pydantic` — schema validation and serialisation
- `pdfplumber` — PDF text extraction

## AI Assistance Disclosure

Claude (claude.ai) was used for initial code scaffolding and to assist with writing this README. All architecture decisions, the two-step prompt strategy, the coverage check design, and the write-up analysis are original. The prompts in `prompts/` were designed manually and iterated against both sample PRDs.
