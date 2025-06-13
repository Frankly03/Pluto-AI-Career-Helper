# backend/app/models/interest.py

from pydantic import BaseModel, Field
from typing import List, Dict

class UserInterestInput(BaseModel):
    """
    Model for user input regarding their interests.
    """
    selected_tags: List[str] = Field(..., description="A list of interest tags selected or entered by the user.")
    # Could add other fields like 'custom_input_text' if user can type free-form interests
    # custom_input_text: Optional[str] = None

class InterestTagGroup(BaseModel):
    """
    Represents a group of interest tags, typically categorized by a field.
    e.g., "Tech": ["Machine Learning", "Web Development"]
    """
    field_name: str
    tags: List[str]

class ProcessedInterests(BaseModel):
    """
    Model for the structure of `processed_interest_tags.json`.
    A dictionary where keys are field names (e.g., "Tech") and values are lists of tags.
    """
    interests_by_field: Dict[str, List[str]] = Field(..., description="Interest tags grouped by field.")

