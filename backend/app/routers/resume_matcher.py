# backend/app/routers/resume_matcher.py

# import fitz
# import docx
from fastapi import APIRouter, HTTPException, Body, Depends, UploadFile, File, Form
from typing import List, Dict, Optional

from app.utils.file_parser import extract_text_from_pdf, extract_text_from_docx
from app.services.resume_service import resume_service_instance, ResumeService
from app.models.resume import ResumeMatchRequest, ResumeMatchResult, PrebuiltJD, JobDescriptionInput

router = APIRouter()

# Dependency for resume service
def get_resume_service():
    return resume_service_instance

@router.post("/match", response_model=ResumeMatchResult)
async def match_resume(
    resume_file: UploadFile = File(...),
    job_description_text: Optional[str] = Form(None), # For custom JD
    prebuilt_jd_id: Optional[str] = Form(None), # For prebuilt JD
    service: ResumeService = Depends(get_resume_service)
):
    """
    Endpoint for resume matching.
    Accepts a resume file (text, pdf, docx - needs parsing) and
    either custom job description text or an ID for a prebuilt JD.
    """
    if not resume_file:
        raise HTTPException(status_code=400, detail="Resume file is required.")
    if not job_description_text and not prebuilt_jd_id:
        raise HTTPException(status_code=400, detail="Either custom_jd_text or prebuilt_jd_id must be provided.")
    if job_description_text and prebuilt_jd_id:
        raise HTTPException(status_code=400, detail="Provide either custom_jd_text or prebuilt_jd_id, not both.")

    try:
        # --- Resume File Handling ---
        # For simplicity, assuming resume_file is plain text.
        # In a real app, you'd parse PDF, DOCX, etc.
        # Example:
        # if resume_file.content_type == "application/pdf":
        #     resume_text = await parse_pdf(resume_file.file)
        # elif resume_file.content_type in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/msword"]:
        #     resume_text = await parse_docx(resume_file.file) # (or .doc)
        # else: # assume plain text or try general text extraction
        #     contents = await resume_file.read()
        #     resume_text = contents.decode('utf-8') # Specify encoding or detect
        
        # Simplified: expecting plain text content for now
        resume_contents = await resume_file.read()
        content_type = resume_file.content_type
        resume_text = ""

        if content_type == "application/pdf":
            resume_text = extract_text_from_pdf(resume_contents)
        elif content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]:
            resume_text = extract_text_from_docx(resume_contents)
        else:
            try:
                resume_text = resume_contents.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings or raise error
                try:
                    resume_text = resume_contents.decode('latin-1')
                except Exception:
                    raise HTTPException(status_code=400, detail="Could not decode resume file. Please ensure it's UTF-8 or plain text.")
            
            if not resume_text.strip():
                 raise HTTPException(status_code=400, detail="Resume file is empty or could not be read.")


        # --- Job Description Handling ---
        final_jd_text = ""
        if job_description_text:
            final_jd_text = job_description_text
        elif prebuilt_jd_id:
            jd_object = service.get_prebuilt_jd_by_id(prebuilt_jd_id)
            if not jd_object:
                raise HTTPException(status_code=404, detail=f"Prebuilt JD with ID '{prebuilt_jd_id}' not found.")
            final_jd_text = jd_object.description
        
        if not final_jd_text.strip():
            raise HTTPException(status_code=400, detail="Job description is empty.")

        match_request = ResumeMatchRequest(
            resume_text=resume_text,
            job_description_text=final_jd_text
        )
        
        result = await service.match_resume_to_jd(match_request)
        if result is None:
            # Service layer should log specifics of LLM failure
            raise HTTPException(status_code=500, detail="Failed to get matching result from the analysis service.")
        return result

    except HTTPException:
        raise # Re-raise HTTPException
    except Exception as e:
        # logger.error(f"Error in resume matching endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred during resume matching: {str(e)}")


@router.get("/prebuilt-jds", response_model=List[Dict[str,str]])
async def get_prebuilt_job_descriptions_options(
    service: ResumeService = Depends(get_resume_service)
):
    """
    Retrieves a list of available prebuilt job descriptions (ID and title)
    for populating a dropdown in the frontend.
    """
    try:
        options = service.list_prebuilt_jds_options()
        return options
    except Exception as e:
        # logger.error(f"Error fetching prebuilt JD options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve prebuilt JD options: {str(e)}")

# Placeholder for parsing functions (these would need actual implementations with libraries like PyPDF2, python-docx)
# async def parse_pdf(file_obj) -> str:
#     # import PyPDF2
#     # reader = PyPDF2.PdfReader(file_obj)
#     # text = ""
#     # for page in reader.pages:
#     #     text += page.extract_text()
#     # return text
#     raise NotImplementedError("PDF parsing not implemented yet.")

# async def parse_docx(file_obj) -> str:
#     # import docx
#     # doc = docx.Document(file_obj)
#     # text = "\n".join([para.text for para in doc.paragraphs])
#     # return text
#     raise NotImplementedError("DOCX parsing not implemented yet.")
