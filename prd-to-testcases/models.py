from pydantic import BaseModel, Field
from typing import Literal, List
from enum import Enum


class Priority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"


class TestType(str, Enum):
    FUNCTIONAL = "functional"
    EDGE = "edge"
    NEGATIVE = "negative"


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non-functional"
    CONSTRAINT = "constraint"


class Requirement(BaseModel):
    req_id: str = Field(..., description="e.g. REQ-001")
    description: str
    req_type: RequirementType


class TestCase(BaseModel):
    test_case_id: str = Field(..., description="e.g. TC-001")
    requirement_id: str = Field(..., description="Linked REQ id")
    scenario: str = Field(..., description="One-line description of what's being tested")
    preconditions: List[str] = Field(..., description="Setup conditions before test execution")
    steps: List[str] = Field(..., description="Step-by-step actions to execute")
    expected_result: str = Field(..., description="What should happen if test passes")
    priority: Priority
    test_type: TestType


class TestPlan(BaseModel):
    prd_title: str
    requirements: List[Requirement]
    test_cases: List[TestCase]
    coverage_gaps: List[str] = Field(
        default_factory=list,
        description="Requirements with no or insufficient test coverage"
    )
