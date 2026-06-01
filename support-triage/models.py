from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class Category(str, Enum):
    BILLING_REFUND = "billing_refund"
    CONTENT_ACCESS = "content_access"
    TECHNICAL_BUG = "technical_bug"
    ACCOUNT_ISSUE = "account_issue"
    SUBSCRIPTION = "subscription"
    GENERAL_FEEDBACK = "general_feedback"


class TriagedTicket(BaseModel):
    ticket_id: str
    original_text: str
    category: Category
    confidence: int = Field(..., ge=1, le=5, description="1=very uncertain, 5=very confident")
    suggested_reply: Optional[str] = None
    escalate: bool = False
    escalation_reason: Optional[str] = None
