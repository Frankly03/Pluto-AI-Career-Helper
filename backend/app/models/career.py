# backend/app/models/career.py

from pydantic import BaseModel, Field
from typing import List, Optional

class Career(BaseModel):
    """
    Represents a career role with its attributes.
    This model is based on the structure of `career_data.json`.
    """
    career: str = Field(..., description="The broader career field, e.g., AI/ML, Web Development.")
    job_title: str = Field(..., description="The specific job title, e.g., ML Engineer, Full Stack Developer.")
    tagline: str = Field(..., description="A tagline[Short description] of the job role.")
    desc: str = Field(..., description="A description of the job role.")
    personality: Optional[str] = Field(None, description="Personality traits often associated with the role (e.g., Holland Codes like IAR).")
    interest_tags: List[str] = Field(default_factory=list, description="Tags representing interests related to this role.")
    skills: List[str] = Field(default_factory=list, description="Key skills required for this role.")
    field: List[str] = Field(default_factory=list, description="Categorical fields this role belongs to, e.g., Tech, Healthcare.")
    tech: bool = Field(..., description="Indicates if the role is predominantly tech-focused.")
    creativity: bool = Field(..., description="Indicates if the role requires significant creativity.")
    
    # Optional field for recommendation score or relevance, added by services
    score: Optional[float] = Field(None, description="Relevance score, e.g., from sentence similarity or LLM ranking.")
    justification: Optional[str] = Field(None, description="Justification for the recommendation by LLM.")

class CareerLite(BaseModel):
    career: str
    job_title: str
    tagline: str
    field: Optional[List[str]] = []

class RecommendedCareer(BaseModel):
    """
    A career recommendation object, typically a subset of Career fields
    plus any specific recommendation metadata.
    """
    job_title: str
    career_field: str # Maps to 'career' from Career model
    description: str
    relevance_score: Optional[float] = None # Could be from SBERT
    llm_justification: Optional[str] = None # From Ollama refinement
    required_skills: List[str]
    interest_tags_matched: Optional[List[str]] = None

class CareerDetail(Career):
    """
    Could be used if we need to return more details for a specific career,
    potentially including roadmap slug or other linked information.
    """
    roadmap_slug: Optional[str] = None

