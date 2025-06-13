# backend/app/models/resume.py

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ResumeUpload(BaseModel):
    """
    Model for resume text input.
    The actual file upload will be handled by FastAPI's UploadFile,
    and its content extracted into the 'resume_text' field.
    """
    resume_text: str = Field(..., description="The full text content of the user's resume.")

class JobDescriptionInput(BaseModel):
    """
    Model for job description input.
    Can be custom text or an ID for a prebuilt JD.
    """
    custom_jd_text: Optional[str] = Field(None, description="Custom job description text provided by the user.")
    prebuilt_jd_id: Optional[str] = Field(None, description="ID of a prebuilt job description selected by the user.")
    # Ensure at least one is provided (can be validated in the service/router)

class ResumeMatchRequest(BaseModel):
    """
    Request model for the resume matching feature.
    """
    resume_text: str = Field(..., description="Text content of the resume.")
    job_description_text: str = Field(..., description="Text content of the job description.")

class ResumeMatchResult(BaseModel):
    """
    Model for the result of a resume matching operation.
    The match_score is now derived from SBERT analysis of sectioned resume.
    The feedback fields are structured based on LLM output.
    """
    match_score: float = Field(..., description="A numerical score (0-100) from SBERT analysis indicating resume-JD similarity.", ge=0, le=100)
    # Detailed feedback from LLM
    feedback: str = Field(..., description="Overall assessment from LLM on resume-JD alignment.")
    strengths: List[str] = Field(default_factory=list, description="Key strengths identified by LLM.")
    areas_for_improvement: List[str] = Field(default_factory=list, description="Specific areas for improvement suggested by LLM.")
    keyword_suggestions: Optional[List[str]] = Field(default_factory=list, description="Keywords from JD to consider adding or emphasizing, suggested by LLM.")
    # Optional: to provide context on how the score was derived
    # section_scores: Optional[Dict[str, float]] = Field(None, description="Individual SBERT scores for each identified resume section against the JD.")


class PrebuiltJD(BaseModel):
    """
    Model for a prebuilt job description.
    """
    id: str
    job_title: str
    description: str
