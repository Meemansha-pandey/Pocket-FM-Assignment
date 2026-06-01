# Support Triage Agent — PocketToons

An AI system that automatically classifies customer support tickets, drafts suggested replies for the top 2 ticket categories, and flags tickets that need human escalation.

Built as part of the PocketToons Applied AI Engineer take-home assignment.

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Place your dataset
# Download from: https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset
# Put the CSV inside: data/customer_support_tickets.csv

# 3. Set your Groq API key (PowerShell)
$env:GROQ_API_KEY='gsk_your-key-here'

# 4. Run
python main.py data/customer_support_tickets.csv

# Optional: limit tickets for a quick test
python main.py data/customer_support_tickets.csv --max 100
```

---

## Dataset

**Source:** Kaggle — [Customer Support Ticket Dataset by suraj520](https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset)

~8,400 synthetic customer support tickets covering billing, technical issues, account problems, and general feedback. The dataset was chosen because it closely mirrors the ticket distribution expected for a subscription/PPV product like PocketToons. The tool samples 200 tickets by default (configurable via `--max`).

**Note on synthetic data:** The Kaggle dataset is synthetically generated — ticket descriptions follow templated patterns (e.g. `{product_purchased}` placeholders are visible in some rows). This affected two things: (a) the classifier occasionally defaulted to `general_feedback` on low-signal tickets, fixed by including the `Ticket Type` column as a classification hint; (b) escalation rate was 0% on tested samples because synthetic tickets don't contain real legal/fraud language. In production with real tickets, the keyword escalation rules would trigger on genuine signals like legal threats, fraud claims, and high-value refund disputes.

---

## Project Structure

```
support-triage/
├── main.py               # CLI entrypoint
├── preprocessor.py       # Load + clean the Kaggle CSV
├── classifier.py         # Groq-based ticket classification
├── escalation.py         # Rule-based escalation logic
├── reply_drafter.py      # Draft replies for top 2 categories
├── models.py             # Pydantic schemas
├── output.py             # CSV + JSON writers + summary
├── debug_escalation.py   # Debug script to inspect escalation triggers
├── requirements.txt
├── prompts/
│   ├── classify.txt      # Classification prompt
│   └── reply.txt         # Reply drafting prompt
├── data/
│   └── customer_support_tickets.csv   # ← place Kaggle CSV here
└── outputs/
    ├── triaged_tickets.csv
    └── triaged_tickets.json
```

---

## Output Format

Each ticket in the output CSV has:

| Field | Description |
|---|---|
| `ticket_id` | Original or generated ticket ID |
| `category` | One of 6 categories (see taxonomy below) |
| `confidence` | 1–5 score from the classifier (5 = very confident) |
| `escalate` | True/False — whether a human should handle this |
| `escalation_reason` | Why the ticket was escalated |
| `suggested_reply` | Drafted reply (only for top 2 categories, non-escalated) |
| `original_text` | First 300 chars of the ticket text |

---

## Write-Up

### 1. Approach and Why

**Category Taxonomy**

Six categories were defined based on the most common ticket types for a subscription/PPV comic app:

| Category | Covers |
|---|---|
| `billing_refund` | Wrong charges, refund requests, payment failures, double billing |
| `content_access` | Can't open comic, missing purchased content, paywall errors |
| `technical_bug` | App crashes, freezing, sync errors, notification failures |
| `account_issue` | Login failures, password reset, account locked/banned |
| `subscription` | Cancel/upgrade/downgrade, trial questions, renewal issues |
| `general_feedback` | Feature requests, complaints, compliments, unrelated queries |

This taxonomy was designed with two goals: categories must be mutually exclusive enough that a classifier can reliably distinguish them, and they must map to different resolution workflows (billing tickets go to a finance team, bugs go to engineering, etc.).

**Pipeline Design**

The system runs in four sequential steps:

1. **Preprocessing** — loads the CSV, normalises column names across dataset variants, builds a unified text field from `Ticket Type + Subject + Description`, and samples up to the requested ticket count. Including `Ticket Type` as a prefix gives the classifier a strong signal and significantly reduces `general_feedback` over-classification.

2. **Classification** — each ticket is sent to Groq (llama-3.3-70b) with a structured prompt defining all six categories precisely and asking for a confidence score (1–5). The model returns JSON with `category` and `confidence`. Tickets that fail to parse default to `general_feedback` with confidence 1 rather than crashing.

3. **Escalation** — a pure rule-based layer runs on top of classifier output. Three rules: (a) hard keyword match on legal threats, fraud, data breach, high-value refunds — using word-boundary regex (`\bsue\b`) to avoid false matches on words like "issue"; (b) strong negative sentiment on billing tickets; (c) tickets too short to action. Confidence score is deliberately excluded from escalation — the LLM's self-reported confidence on this synthetic dataset was unreliable and caused 95%+ false escalation rates in early testing.

4. **Reply drafting** — the top 2 categories by volume are identified, and a suggested reply is drafted for every non-escalated ticket in those categories. Escalated tickets are left for human agents; sending an auto-drafted reply to an angry or legally sensitive customer is worse than no reply.

**Model choice:** `llama-3.3-70b-versatile` via Groq — chosen for its generous free tier (14,400 requests/day), fast inference, and reliable JSON output for classification tasks. Groq was selected over Gemini and OpenAI after both hit quota/authentication issues during development. The classification prompt is tight enough that a large open-source model works well; a frontier model would be overkill for structured category selection.

**A real debugging catch:** During development, the escalation rule for `"sue"` (legal threat) was matching the substring inside `"issue"` — every ticket in the dataset contained the word "issue", causing 95-99% false escalation rates. Fixed by switching to `\bsue\b` (word-boundary regex). This is documented here because it's exactly the kind of edge case that production systems hit and eval sets catch.

---

### 2. How You Would Evaluate This

**Classification accuracy**

Build a small hand-labelled eval set (20–50 tickets manually categorised). Measure:
- Per-category precision and recall
- Macro-averaged F1 score
- Confusion matrix to identify which categories the model most often confuses

The most likely confusion pairs are `billing_refund` vs `subscription` (both involve payments) and `technical_bug` vs `content_access` (both involve something not working). Prompt refinement targets these pairs first.

**Escalation precision/recall**

Manually review 50 escalated and 50 non-escalated tickets:
- False positives (escalated unnecessarily) waste agent time
- False negatives (missed escalations) are the higher-risk failure — a legal threat that received an auto-reply is a serious incident

Target: recall > 0.95 on true escalations, even at the cost of precision.

**Reply quality**

Human eval by support team: rate 20 drafted replies on (a) accuracy, (b) tone, (c) actionability. A/B test auto-drafted vs human-written replies on CSAT scores over 2 weeks.

---

### 3. What Changes for Production at 10K Tickets/Month

**Architecture changes**

At 10K tickets/month (~330/day, ~14/hour) the current synchronous single-process design works fine — it doesn't need to become a distributed system. The main changes are operational:

- **Queue-based processing** — tickets arrive via webhook (Zendesk/Freshdesk API), get pushed to a queue (SQS or Redis), and a worker processes them asynchronously. No more batch CSV files.
- **Database** — results go into Postgres, not CSV files. Support agents query live rather than opening Excel.
- **Caching** — identical or near-identical tickets (duplicate submissions) can be detected with embedding similarity and served from cache, avoiding redundant LLM calls.
- **Monitoring** — track classification distribution over time. A sudden spike in `technical_bug` tickets is an incident signal before engineering notices it.

**What stays the same:** the core prompt logic, escalation rules, and reply drafting are all stateless and scale horizontally without changes.

---

### 4. Rough Cost Estimate at 10K Tickets/Month

Assumptions:
- Average ticket: ~200 tokens input + ~50 tokens output for classification
- Reply drafting (top 2 categories, ~60% of tickets, non-escalated ~80%): ~300 tokens input + ~150 tokens output
- Groq pricing for llama-3.3-70b: $0.59 / 1M input tokens, $0.79 / 1M output tokens

| Step | Tickets | Tokens | Cost |
|---|---|---|---|
| Classification (all tickets) | 10,000 | 2.5M input / 0.5M output | $1.87 |
| Reply drafting (~4,800 tickets) | 4,800 | 1.44M input / 0.72M output | $1.42 |
| **Total** | | | **~$3.30/month** |

At this scale, LLM cost is negligible. The real costs are engineering time for integration, monitoring infrastructure, and human agent review of escalated tickets (~15–20% of volume based on typical support benchmarks).

---

## What I Would Add With More Time

**Small eval set with metrics** — 20 hand-labelled tickets with per-category precision/recall. This is the most important missing piece; without it the accuracy claims are unverified.

**Embedding-based deduplication** — detect near-duplicate tickets before classification to avoid processing the same issue repeatedly during an outage.

**Batch API calls** — current design makes one API call per ticket sequentially. Processing in groups of 10 would reduce wall-clock time significantly for large runs.

**Zendesk/Freshdesk webhook integration** — replace CSV input with a real-time webhook so the agent processes tickets as they arrive, not in nightly batches.

**Real ticket dataset** — the Kaggle dataset is synthetic. Testing against real anonymised support tickets would surface classification errors the synthetic data hides, particularly around ambiguous or multi-issue tickets.

---

## AI Assistance Disclosure

Claude (claude.ai) was used for code scaffolding. All architecture decisions, taxonomy design, escalation rule logic, prompt design, and write-up are original. The `\bsue\b` regex bug was caught through actual debugging and testing, not code review.
