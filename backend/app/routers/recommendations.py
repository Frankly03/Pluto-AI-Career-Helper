# backend/app/routers/recommendations.py

from fastapi import APIRouter, HTTPException, Body, Depends
from typing import List, Dict
from app.utils.logger import logger

from app.services.recommendation_service import recommendation_service_instance, RecommendationService
from app.services.interest_service import interest_service_instance, InterestService
from app.models.interest import UserInterestInput, ProcessedInterests
from app.models.career import RecommendedCareer



router = APIRouter()

# Dependency for services (example, can be more sophisticated)
def get_recommendation_service():
    return recommendation_service_instance

def get_interest_service():
    return interest_service_instance


@router.post("/recommend", response_model=List[RecommendedCareer])
async def get_career_recommendations(
    user_input: UserInterestInput = Body(...),
    rec_service: RecommendationService = Depends(get_recommendation_service)
):
    """
    Endpoint to get career recommendations based on user interests.
    Receives a list of selected interest tags.
    """
    if not user_input.selected_tags:
        raise HTTPException(status_code=400, detail="No interest tags provided.")
    
    try:
        recommendations = await rec_service.get_recommendations(user_input)
        if not recommendations:
            # This could mean no matches, or an issue upstream.
            # The service layer should log specifics.
            # Return empty list, or a specific message if preferred.
            return [] 
        return recommendations
    except Exception as e:
        # Log the full exception details in a real app
        logger.error(f"Error in recommendation endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while generating recommendations: {str(e)}")


@router.get("/interests", response_model=ProcessedInterests)
async def get_all_interests(
    int_service: InterestService = Depends(get_interest_service)
):
    """
    Endpoint to retrieve all available interest tags, grouped by field.
    This is used to populate the interest selector on the frontend.
    """
    try:
        tags_by_field = int_service.get_all_interest_tags()
        if not tags_by_field:
             raise HTTPException(status_code=404, detail="No interest tags found or loaded.")
        return ProcessedInterests(interests_by_field=tags_by_field)
    except Exception as e:
        logger.error(f"Error in interests endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching interest tags: {str(e)}")

@router.get("/interests/flat", response_model=List[str])
async def get_flat_list_of_all_interests(
    int_service: InterestService = Depends(get_interest_service)
):
    """
    Endpoint to retrieve a flat list of all unique interest tags.
    Can be used for autocomplete or validation.
    """
    try:
        flat_tags = int_service.get_flat_list_of_tags()
        if not flat_tags:
            raise HTTPException(status_code=404, detail="No interest tags found or loaded.")
        return flat_tags
    except Exception as e:
        logger.error(f"Error in flat interests endpoint: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"An error occurred while fetching flat list of interest tags: {str(e)}")
