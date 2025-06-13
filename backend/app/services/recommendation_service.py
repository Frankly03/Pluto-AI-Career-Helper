# backend/app/services/recommendation_service.py

import json
import logging
from typing import List, Dict, Optional, Tuple

import numpy as np
from sentence_transformers.util import semantic_search # or cosine_similarity from sklearn

from app.core.config import settings
from app.core.ollama_client import OllamaClient
from app.ml.sentence_transformer_loader import SentenceTransformerLoader
from app.models.career import Career, CareerLite, RecommendedCareer
from app.models.interest import UserInterestInput

logger = logging.getLogger(__name__)

class RecommendationService:
    """
    Service for generating career recommendations.
    Uses Sentence BERT for initial candidate selection and an LLM for refinement.
    """

    def __init__(self):
        self.ollama_client = OllamaClient()
        self.sbert_model = SentenceTransformerLoader.get_model()
        self._load_career_data_and_embeddings()

    def get_career_lite_list(self) -> List[CareerLite]:
        return [
            CareerLite(
                career=c.career,
                job_title=c.job_title,
                tagline=c.tagline,
                field=c.field
            )for c in self.career_data_list
        ]
    

    def _load_career_data_and_embeddings(self):
        """Loads career data and their embeddings."""
        self.career_data_list: List[Career] = []
        try:
            if settings.CAREER_DATA_PATH.exists():
                with open(settings.CAREER_DATA_PATH, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)
                    self.career_data_list = [Career(**item) for item in raw_data]
                logger.info(f"Loaded {len(self.career_data_list)} careers from {settings.CAREER_DATA_PATH}")
            else:
                logger.error(f"Career data file not found: {settings.CAREER_DATA_PATH}")
                # Handle this case, maybe raise an error or operate with empty data
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {settings.CAREER_DATA_PATH}", exc_info=True)
        except Exception as e:
            logger.error(f"Error loading career data: {e}", exc_info=True)

        # Load embeddings (or ensure they are loaded by SentenceTransformerLoader)
        # The loader now takes career_data to potentially generate embeddings if missing (though not recommended for prod)
        self.career_embeddings, self.career_job_titles = SentenceTransformerLoader.get_career_embeddings(
            [item.model_dump() for item in self.career_data_list] # Pass raw dicts
        )

        if self.sbert_model is None:
            logger.error("SBERT model is not loaded. Recommendation quality will be affected.")
        if self.career_embeddings is None or self.career_job_titles is None:
            logger.error("Career embeddings or job titles not loaded. SBERT recommendations will not work.")
            # Fallback: could potentially use only LLM if SBERT fails, or return error.
            # For now, proceed and handle None checks later.

    def _get_sbert_recommendations(self, user_interests_text: str, top_n: int = 15) -> List[Tuple[Career, float]]:
        """
        Gets initial recommendations using Sentence BERT based on user interests.
        """
        if not self.sbert_model or self.career_embeddings is None or not self.career_data_list or self.career_job_titles is None:
            logger.warning("SBERT model, career data, or embeddings not available. Skipping SBERT recommendations.")
            return []

        try:
            query_embedding = self.sbert_model.encode(user_interests_text)
            
            # Perform semantic search
            # semantic_search returns a list of lists, one for each query. We have one query.
            # Each inner list contains dicts: {'corpus_id': int, 'score': float}
            hits = semantic_search(query_embedding, self.career_embeddings, top_k=top_n)
            
            sbert_recs: List[Tuple[Career, float]] = []
            if hits and hits[0]:
                for hit in hits[0]:
                    corpus_id = hit['corpus_id']
                    score = hit['score']
                    # Find the career data corresponding to the corpus_id
                    # This assumes career_embeddings were generated in the same order as career_data_list
                    if 0 <= corpus_id < len(self.career_data_list):
                        matched_career = self.career_data_list[corpus_id]
                        # Verify job title if necessary, though corpus_id should be reliable if data is consistent
                        # if matched_career.job_title == self.career_job_titles[corpus_id]:
                        sbert_recs.append((matched_career, score))
                        # else:
                        #     logger.warning(f"Mismatch in job title for corpus_id {corpus_id}. Expected {self.career_job_titles[corpus_id]}, got {matched_career.job_title}")
                    else:
                        logger.warning(f"Corpus ID {corpus_id} out of range for career_data_list.")
            
            logger.info(f"SBERT recommended {len(sbert_recs)} careers.")
            return sbert_recs

        except Exception as e:
            logger.error(f"Error during SBERT recommendation: {e}", exc_info=True)
            return []

    async def _get_llm_refined_recommendations(
        self, 
        user_interests_text: str, 
        sbert_candidates: List[Career], 
        num_final_recs: int = 5
    ) -> List[RecommendedCareer]:
        """
        Uses Ollama LLM to refine SBERT candidates or generate recommendations directly.
        """
        if not sbert_candidates:
            logger.warning("No SBERT candidates to refine. LLM might generate from scratch or fail.")
            # Potentially, could have a prompt for LLM to generate based on interests only.
            # For now, we expect SBERT candidates.
            # return [] # Or try to generate from scratch

        prompt_template = """
            You are an intelligent and helpful career guidance assistant.

            The user has expressed the following interests:
            "{user_interests}"

            Based on these interests, here is a list of job roles that were preliminarily matched using a semantic similarity model (SBERT):
            {candidate_jobs_formatted}

            Your task is to analyze these suggestions and return the top {num_final_recs} job roles that are the **most relevant and exciting** for the user.

            For each selected role, include:
            1. "job_title" - The exact title of the role.
            2. "career_field" - The broader category or domain (e.g., Data Science, Cybersecurity).
            3. "description" - A concise, informative overview of what this role does.
            4. "llm_justification" - A brief, **engaging explanation** (1–2 sentences) on why this job aligns with the user's interests. Use light metaphors or analogies if it helps make the connection clearer or more memorable.
            5. "required_skills" - A list of 3 to 5 important skills needed for this job.

            **Guidelines:**
            - Rank the roles in order of suitability (most to least).
            - Avoid generic or placeholder content.
            - Try to vary the types of careers unless the interests are hyper-focused.
            - If no candidate roles are suitable, suggest new ones based directly on the user's interests.
            - Keep the tone professional but friendly, and don’t be afraid to show a little creative flair.

            Respond **only** with a valid JSON list of objects in the following format:
            [
              {{
                "job_title": "Data Scientist",
                "career_field": "Data Science",
                "description": "Extracts insights from large datasets using statistical and machine learning techniques.",
                "llm_justification": "Since the user enjoys uncovering patterns and working with numbers, this role is like being a modern-day detective for data.",
                "required_skills": ["Python", "SQL", "Machine Learning", "Data Visualization", "Statistics"]
              }},
              ...
            ]
        
            Ensure the output is ONLY the JSON list, without any introductory text or explanations outside the JSON.
        """

        def format_candidate_jobs(candidates: List[Career]) -> str:
            job_lines = []
            for c in candidates:
                line = f"- {c.job_title} ({c.career}): {c.tagline or c.desc[:60] + '...'}"
                job_lines.append(line)
            return "\n".join(job_lines)
    
        candidate_jobs_formatted = format_candidate_jobs(sbert_candidates)
        if not candidate_jobs_formatted:
            candidate_jobs_formatted = "No specific candidates were pre-selected. Please generate suggestions based on interests."

        prompt = prompt_template.format(
            user_interests=user_interests_text,
            candidate_jobs_formatted=candidate_jobs_formatted,
            num_final_recs=num_final_recs
        )
        
        logger.info(f"Sending prompt to LLM for refining {len(sbert_candidates)} candidates.")
        logger.debug(f"LLM Prompt for recommendation: {prompt}") # Careful with logging large prompts

        llm_response_text = await self.ollama_client.get_text_response(prompt)

        if not llm_response_text:
            logger.error("LLM did not return a response for recommendation.")
            return []

        try:
            # The prompt asks for JSON, so we parse it.
            # Clean the response if it includes markdown code block syntax
            if llm_response_text.strip().startswith("```json"):
                llm_response_text = llm_response_text.strip()[7:]
                if llm_response_text.strip().endswith("```"):
                    llm_response_text = llm_response_text.strip()[:-3]
            
            llm_results_raw = json.loads(llm_response_text)
            
            refined_recs: List[RecommendedCareer] = []
            for item_raw in llm_results_raw:
                # Basic validation, Pydantic model will do more
                if all(k in item_raw for k in ["job_title", "career_field", "description", "llm_justification", "required_skills"]):
                    # Find original SBERT score if available (optional)
                    original_career = next((c for c in sbert_candidates if c.job_title == item_raw["job_title"]), None)
                    sbert_score = original_career.score if original_career and hasattr(original_career, 'score') else None

                    rec = RecommendedCareer(
                        job_title=item_raw["job_title"],
                        career_field=item_raw["career_field"],
                        description=item_raw["description"],
                        relevance_score=sbert_score, # Keep SBERT score if available
                        llm_justification=item_raw["llm_justification"],
                        required_skills=item_raw["required_skills"],
                        # interest_tags_matched could be populated by comparing user_interests_text with role's tags
                    )
                    refined_recs.append(rec)
                else:
                    logger.warning(f"LLM output item missing required keys: {item_raw}")

            logger.info(f"LLM refined/generated {len(refined_recs)} recommendations.")
            return refined_recs[:num_final_recs] # Ensure we don't exceed the requested number

        except json.JSONDecodeError:
            logger.error(f"Failed to parse JSON response from LLM: {llm_response_text}", exc_info=True)
            # Fallback: try to return SBERT results if LLM fails parsing
            # This is a simple fallback, could be more sophisticated
            return [
                RecommendedCareer(
                    job_title=c.job_title,
                    career_field=c.career,
                    description=c.desc,
                    relevance_score=c.score if hasattr(c, 'score') else None,
                    required_skills=c.skills[:5], # Take some skills
                    llm_justification="LLM refinement failed; this is a direct SBERT match."
                ) for c in sbert_candidates[:num_final_recs]
            ]
        except Exception as e:
            logger.error(f"Error processing LLM response: {e}", exc_info=True)
            return []


    async def get_recommendations(self, user_input: UserInterestInput, num_sbert_candidates: int = 15, num_final_recs: int = 5) -> List[RecommendedCareer]:
        """
        Main method to get career recommendations.
        """
        if not user_input.selected_tags:
            logger.warning("User provided no interest tags.")
            return []

        user_interests_text = ", ".join(user_input.selected_tags)
        logger.info(f"Generating recommendations for interests: {user_interests_text}")

        # 1. Get initial candidates from SBERT
        sbert_raw_recs = self._get_sbert_recommendations(user_interests_text, top_n=num_sbert_candidates)
        
        sbert_candidates: List[Career] = []
        for career, score in sbert_raw_recs:
            career_with_score = career.model_copy(update={'score': score}) # Add score to the model
            sbert_candidates.append(career_with_score)
        
        if not sbert_candidates and (not self.sbert_model or self.career_embeddings is None):
             logger.warning("SBERT is not functional, and no candidates were retrieved. LLM will try to generate from scratch.")
             # Proceed to LLM, it might still work if the prompt allows generation from scratch.
        elif not sbert_candidates:
            logger.info("SBERT returned no candidates for the given interests. LLM might generate from scratch.")


        # 2. Refine with LLM
        final_recommendations = await self._get_llm_refined_recommendations(
            user_interests_text, 
            sbert_candidates, 
            num_final_recs=num_final_recs
        )
        
        # If LLM fails or returns empty and SBERT had results, could return SBERT results as a fallback
        if not final_recommendations and sbert_candidates:
            logger.warning("LLM refinement failed or returned empty. Falling back to top SBERT candidates if any.")
            # Convert SBERT candidates to RecommendedCareer model
            fallback_recs = [
                RecommendedCareer(
                    job_title=c.job_title,
                    career_field=c.career,
                    description=c.desc,
                    relevance_score=c.score if hasattr(c, 'score') else None,
                    required_skills=c.skills[:5], # Top 5 skills
                    llm_justification="Direct SBERT match (LLM refinement fallback)."
                ) for c in sbert_candidates[:num_final_recs]
            ]
            return fallback_recs

        return final_recommendations

# Singleton instance or manage via dependency injection
recommendation_service_instance = RecommendationService()
