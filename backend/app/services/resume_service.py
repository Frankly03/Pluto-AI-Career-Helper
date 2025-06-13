import json
import logging
import re
from typing import Optional, List, Dict, Any
from sentence_transformers import SentenceTransformer, util
import json5  

from app.core.config import settings
from app.core.ollama_client import OllamaClient
from app.models.resume import ResumeMatchRequest, ResumeMatchResult, PrebuiltJD


logger = logging.getLogger(__name__)

STANDARDIZED_SECTIONS: Dict[str, List[str]] = {
    "PROFILE": ["summary", "objective", "profile", "about me", "personal profile", "professional summary", "career summary"],
    "SKILLS": ["skills", "technical skills", "hard skills", "soft skills", "proficiencies", "technical proficiencies", "expertise", "tools & technologies", "languages and technologies", "technologies"],
    "EXPERIENCE": ["experience", "work experience", "professional experience", "employment history", "work history", "relevant experience", "business experience", "internships", "internship experience", "internship", "intern experience", "industrial training"],
    "PROJECTS": ["projects", "project", "academic projects", "personal projects", "portfolio", "key projects", "technical projects"],
    "EDUCATION": ["education", "education background", "educational qualifications", "academic background", "academic qualifications", "scholastic achievements"],
    "CERTIFICATIONS": ["certifications", "licenses & certifications", "courses", "training", "professional development", "online courses"],
    "OTHERS": ["achievements", "awards", "honors", "miscellaneous", "extracurricular activities", "hobbies", "languages", "volunteer experience", "references", "additional information", "personal details"]
}

class SBERTMatcher:
    def __init__(self, model_name: str = "all-mpnet-base-v2"):
        try:
            self.model = SentenceTransformer(model_name)
            logger.info(f"SBERT model '{model_name}' loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load SBERT model '{model_name}': {e}")
            self.model = None

    def match(self, section_text: str, jd_text: str) -> float:
        if not self.model or not section_text.strip():
            return 0.0
        try:
            section_text = self.clean_text(section_text)
            jd_text = self.clean_text(jd_text)
            embeddings = self.model.encode([section_text, jd_text])
            similarity_score = util.cos_sim(embeddings[0], embeddings[1]).item()
            return round(similarity_score * 100, 2)
        except Exception as e:
            logger.error(f"Error during SBERT similarity computation: {e}")
            return 0.0
        
    def clean_text(self, text: str) -> str:
        text = re.sub(r'[^a-zA-Z\s]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.lower().strip()

class ResumeService:
    def __init__(self):
        self.ollama_client = OllamaClient()
        self.sbert_matcher = SBERTMatcher()
        self.prebuilt_jds: List[PrebuiltJD] = self._load_prebuilt_jds()

    def _load_prebuilt_jds(self) -> List[PrebuiltJD]:
        jds = []
        if not settings.PREBUILT_JDS_PATH.exists():
            logger.warning(f"Prebuilt JDs file not found: {settings.PREBUILT_JDS_PATH}")
            return []
        try:
            with open(settings.PREBUILT_JDS_PATH, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                jds = [PrebuiltJD(**item) for item in raw_data]
            logger.info(f"Loaded {len(jds)} prebuilt job descriptions.")
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {settings.PREBUILT_JDS_PATH}", exc_info=True)
        except Exception as e:
            logger.error(f"Error loading prebuilt JDs: {e}", exc_info=True)
        return jds

    def get_prebuilt_jd_by_id(self, jd_id: str) -> Optional[PrebuiltJD]:
        for jd in self.prebuilt_jds:
            if jd.id == jd_id:
                return jd
        return None

    def list_prebuilt_jds_options(self) -> List[Dict[str, str]]:
        return [{"id": jd.id, "job_title": jd.job_title} for jd in self.prebuilt_jds]

    def normalize_section_name(self, header: str) -> str:
        header = header.lower().strip()
        for normalized, aliases in STANDARDIZED_SECTIONS.items():
            if header in aliases:
                return normalized
        return "other"
    
    def extract_resume_sections(self, resume_text):
        sections = {}
        lines = resume_text.splitlines()
        current_section = "personalInfo"
        buffer = []

        for line in lines:
            normalized = self.normalize_section_name(line)
            if normalized != "other" and not line.strip().isdigit():
                if buffer:
                    content = "\n".join(buffer).strip()
                    sections[current_section] = content
                    buffer = []
                current_section = normalized
            else:
                buffer.append(line)

        if buffer:
            content = "\n".join(buffer).strip()
            sections[current_section] = content

        return sections
    
    def fix_malformed_json(self, text: str) -> str:
        # Remove markdown formatting and LLM preambles
        text = text.strip()
        text = re.sub(r"^```json|```$", "", text).strip()
        text = re.sub(r"(?i)^here is.*?json format[:\-]*", "", text).strip()

        # Try to extract the first JSON-like block
        json_start = text.find("{")
        if json_start == -1:
            return ""

        json_text = text[json_start:]

        # Heuristic fix: Count brackets and fix unclosed ones
        open_braces = json_text.count("{")
        close_braces = json_text.count("}")
        if open_braces > close_braces:
            json_text += "}" * (open_braces - close_braces)

        open_brackets = json_text.count("[")
        close_brackets = json_text.count("]")
        if open_brackets > close_brackets:
            json_text += "]" * (open_brackets - close_brackets)

        return json_text.strip()
    
    
    
    async def match_resume_to_jd(self, request: ResumeMatchRequest) -> Optional[ResumeMatchResult]:
        if not request.resume_text or not request.job_description_text:
            logger.warning("Resume text or Job Description text is empty. Cannot perform match.")
            return None
        
        # total_score = self.calculate_score(request.resume_text, request.job_description_text)
        resume = request.resume_text
        jd = request.job_description_text
        section_map = self.extract_resume_sections(resume)

        section_scores = {
            section: self.sbert_matcher.match(text, jd)
            for section, text in section_map.items()
        }
        is_experienced = 'EXPERIENCE' in section_map

        if is_experienced:
            total_score = (
                0.60 * section_scores.get('SKILLS', 0.0) +
                0.55 * section_scores.get('EXPERIENCE', 0.0) +
                0.35 * section_scores.get('PROJECTS', 0.0) +
                0.15 * section_scores.get('CERTIFICATIONS', 0.0) +
                0.20 * section_scores.get('EDUCATION', 0.0) +
                0.05 * section_scores.get('OTHERS', 0.0) +
                0.15 * section_scores.get('PROFILE', 0.0)
            )
        else:
            total_score = (
                0.60 * section_scores.get('SKILLS', 0.0) +
                0.60 * section_scores.get('PROJECTS', 0.0) +
                0.20 * section_scores.get('CERTIFICATIONS', 0.0) +
                0.25 * section_scores.get('EDUCATION', 0.0) +
                0.10 * section_scores.get('OTHERS', 0.0) +
                0.20 * section_scores.get('PROFILE', 0.0)
            )
        if total_score < 50 and total_score > 30:
            total_score = total_score * 1.15
        elif total_score <= 30:
            total_score = total_score * 1.25

        total_score = round(min(total_score, 100), 2)
        
        prompt_template = f"""
        You are an expert AI assistant helping a job candidate improve their resume by finding thier score by matching the resume with the job description.
        Here is their resume:
        ---
        {request.resume_text}
        ---

        Here is the job description they are applying for:
        ---
        {request.job_description_text}
        ---
        The candidate may be early-career professional or fresher. Your job is to provide honest, structured feedback on their resume's alignment with the job description — no sugarcoating, but keep it encouraging.
        Based on the job description and the resume, provide the following ONLY in JSON format:

        {{
            "match_score": rate a match score between the resume and job description 10-100,
            "feedback": "<Give helpful and honest feedback, explain what the candidate did well and what could be improved.>",
            "strengths": ["<Key strengths matching the JD>", "..."],
            "areas_for_improvement": ["<Areas the candidate lacks or can improve>", "..."],
            "keyword_suggestions": ["(list of strings) 2–3 important keywords or tech terms from the JD that are missing or weakly represented in the resume. Only suggest if truly relevant to the role."]
        }}
        Strictly Follow this:
        Respond ONLY with the JSON.Finish the json format completely. No preamble, no explanations.
        """

        logger.info(f"Calling LLM for resume feedback with hybrid score.")
        MAX_RETRIES = 2
        retry_count = 0
        llm_response_text = ""

        while retry_count <= MAX_RETRIES:
            llm_response_text = await self.ollama_client.get_text_response(prompt_template)
            if llm_response_text:
                break
            retry_count += 1
            logger.warning(f"Retrying LLM call... Attempt {retry_count}")

        if not llm_response_text:
            logger.error("No response from LLM during hybrid resume match.")
            return ResumeMatchResult(
                match_score=total_score,
                feedback="LLM feedback generation failed. Only similarity score is provided.",
                strengths=[],
                areas_for_improvement=[],
                keyword_suggestions=[]
            )
        try:
            llm_response_text = self.fix_malformed_json(llm_response_text)
            logger.debug(f"Cleaned LLM response: {llm_response_text}")
            try:
                match_data = json.loads(llm_response_text)
            except json.JSONDecodeError:
                logger.warning("Standard JSON parsing failed. Trying json5 fallback...")
                match_data = json5.loads(llm_response_text)
            if total_score != 0:
                match_data['match_score'] = total_score
            else:
                match_data['match_score'] = match_data.get("match_score", 0)

            return ResumeMatchResult(
                match_score=match_data.get("match_score", 0.0),
                feedback=match_data.get("feedback", ""),
                strengths=match_data.get("strengths", []),
                areas_for_improvement=match_data.get("areas_for_improvement", []),
                keyword_suggestions=match_data.get("keyword_suggestions", [])
            )
        except Exception as e:
            logger.error(f"Error parsing LLM JSON response: {e}", exc_info=True)
            logger.error(f"Failed LLM response (truncated): {llm_response_text[:]}")
            return ResumeMatchResult(
                match_score=total_score,
                feedback="LLM feedback generation failed. Only similarity score is provided.",
                strengths=[],
                areas_for_improvement=[],
                keyword_suggestions=[]
            )


resume_service_instance = ResumeService()