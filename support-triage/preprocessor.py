"""
preprocessor.py — load and clean the Kaggle customer support ticket dataset.
"""

import pandas as pd
from pathlib import Path


POSSIBLE_TEXT_COLS = [
    "Ticket Description", "ticket_description", "description", "body", "text",
    "Body", "Text", "content", "message"
]
POSSIBLE_SUBJECT_COLS = [
    "Ticket Subject", "ticket_subject", "subject", "Subject", "title", "Title", "summary"
]
POSSIBLE_TYPE_COLS = [
    "Ticket Type", "ticket_type", "type", "Type", "category", "Category"
]
POSSIBLE_ID_COLS = [
    "Ticket ID", "ticket_id", "id", "ID", "index"
]


def load_tickets(csv_path: str, max_tickets: int = 200) -> pd.DataFrame:
    """
    Load the Kaggle support ticket CSV, normalise column names,
    and return a clean DataFrame with columns: ticket_id, text.
    """
    path = Path(csv_path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at: {csv_path}\n"
            f"Download from: https://www.kaggle.com/datasets/suraj520/customer-support-ticket-dataset\n"
            f"and place the CSV in the data/ folder."
        )

    df = pd.read_csv(csv_path)
    print(f"  ✓ Loaded {len(df):,} rows. Columns: {list(df.columns)}")

    # ── Find columns ──────────────────────────────────────────────────────────
    text_col    = _find_col(df, POSSIBLE_TEXT_COLS)
    subject_col = _find_col(df, POSSIBLE_SUBJECT_COLS)
    type_col    = _find_col(df, POSSIBLE_TYPE_COLS)
    id_col      = _find_col(df, POSSIBLE_ID_COLS)

    if text_col is None and subject_col is None:
        raise ValueError(
            f"Could not find a text column. Available columns: {list(df.columns)}"
        )

    # ── Build unified text: Type + Subject + Description ─────────────────────
    # Including Ticket Type gives the classifier a strong signal
    text_parts = []
    if type_col:
        text_parts.append("Ticket Type: " + df[type_col].fillna("").astype(str))
    if subject_col:
        text_parts.append("Subject: " + df[subject_col].fillna("").astype(str))
    if text_col:
        text_parts.append(df[text_col].fillna("").astype(str))

    combined = text_parts[0].copy()
    for part in text_parts[1:]:
        combined = combined + "\n" + part
    df["_text"] = combined

    # ── Build ticket ID ───────────────────────────────────────────────────────
    if id_col:
        df["_id"] = df[id_col].astype(str)
    else:
        df["_id"] = ["TKT-" + str(i + 1).zfill(4) for i in range(len(df))]

    # ── Clean ─────────────────────────────────────────────────────────────────
    df["_text"] = df["_text"].str.strip()
    df = df[df["_text"].str.len() > 10].reset_index(drop=True)

    if len(df) > max_tickets:
        df = df.sample(n=max_tickets, random_state=42).reset_index(drop=True)
        print(f"  ✓ Sampled {max_tickets} tickets for processing")

    return df[["_id", "_text"]].rename(columns={"_id": "ticket_id", "_text": "text"})


def _find_col(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    lower_cols = {c.lower(): c for c in df.columns}
    for col in candidates:
        if col.lower() in lower_cols:
            return lower_cols[col.lower()]
    return None
