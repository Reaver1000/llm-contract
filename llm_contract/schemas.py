"""Typed schemas. The JobPosting model is the demo contract, add your own."""
from typing import Literal, Optional

from pydantic import BaseModel, Field


class JobPosting(BaseModel):
    title: str
    company: str
    location: str = Field(description="City and country, or 'Remote'")
    remote_policy: Literal["remote", "hybrid", "onsite", "unknown"]
    salary_min: Optional[int] = Field(default=None, description="Lower bound of the stated salary range")
    salary_max: Optional[int] = None
    currency: Optional[Literal["EUR", "GBP", "USD", "unknown"]] = None
    min_years_experience: Optional[int] = Field(default=None, description="Stated minimum years of professional experience")
    german_level: Optional[Literal["none", "B1", "B2", "C1", "C2", "native", "required", "unknown"]] = None
    english_level: Optional[Literal["none", "B1", "B2", "C1", "C2", "native", "required", "unknown"]] = None
    requires_degree: Optional[bool] = None
    tech_stack: list[str] = Field(default_factory=list)
