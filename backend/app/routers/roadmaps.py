# backend/app/routers/roadmaps.py

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any

from app.services.roadmap_service import roadmap_service_instance, RoadmapService

router = APIRouter()

# Dependency for roadmap service
def get_roadmap_service():
    return roadmap_service_instance

@router.get("/", response_model=List[Dict[str, str]])
async def list_roadmaps(
    service: RoadmapService = Depends(get_roadmap_service)
):
    """
    Lists all available career roadmaps.
    Returns a list of objects, each with "title" and "slug".
    """
    try:
        available_roadmaps = service.list_available_roadmaps()
        return available_roadmaps
    except Exception as e:
        # logger.error(f"Error listing roadmaps: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list roadmaps: {str(e)}")


@router.get("/{slug}", response_model=Dict[str, Any]) # Or a more specific Pydantic model for Roadmap
async def get_roadmap_details(
    slug: str,
    service: RoadmapService = Depends(get_roadmap_service)
):
    """
    Retrieves the detailed content of a specific career roadmap by its slug.
    """
    try:
        roadmap_data = service.get_roadmap_by_slug(slug)
        if roadmap_data is None:
            raise HTTPException(status_code=404, detail=f"Roadmap with slug '{slug}' not found.")
        return roadmap_data
    except HTTPException:
        raise # Re-raise HTTPException if it's already one (like 404)
    except Exception as e:
        # logger.error(f"Error fetching roadmap '{slug}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve roadmap '{slug}': {str(e)}")

