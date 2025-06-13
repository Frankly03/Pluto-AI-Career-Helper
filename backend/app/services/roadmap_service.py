# backend/app/services/roadmap_service.py

import json
import logging
from typing import Optional, Dict, Any, List
from pathlib import Path

from app.core.config import settings
from app.utils.logger import logger

logger = logging.getLogger(__name__)

class RoadmapService:
    """
    Service for loading and providing career roadmaps.
    Roadmaps are stored as individual JSON files in the `roadmaps_data` directory.
    """
    def __init__(self, roadmaps_dir: Path = settings.ROADMAPS_DATA_DIR):
        self.roadmaps_dir = roadmaps_dir
        if not self.roadmaps_dir.exists() or not self.roadmaps_dir.is_dir():
            logger.warning(f"Roadmaps directory not found or is not a directory: {self.roadmaps_dir}")
            # You might want to create it or handle this more gracefully
            # self.roadmaps_dir.mkdir(parents=True, exist_ok=True)

    def get_roadmap_by_slug(self, slug: str) -> Optional[Dict[str, Any]]:
        """
        Loads a specific roadmap JSON file based on its slug.
        The slug is expected to be the filename without the .json extension.
        """
        roadmap_file_path = self.roadmaps_dir / f"{slug.lower().replace(' ', '-')}_roadmap.json"
        
        if not roadmap_file_path.exists():
            logger.warning(f"Roadmap file not found for slug '{slug}' at {roadmap_file_path}")
            return None
        
        try:
            with open(roadmap_file_path, 'r', encoding='utf-8') as f:
                roadmap_data = json.load(f)
            logger.info(f"Roadmap '{slug}' loaded successfully from {roadmap_file_path}")
            return roadmap_data
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON for roadmap '{slug}' from {roadmap_file_path}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error loading roadmap '{slug}': {e}", exc_info=True)
            return None

    def list_available_roadmaps(self) -> List[Dict[str, str]]:
        """
        Lists available roadmaps by scanning the roadmaps directory.
        Returns a list of {"title": "Roadmap Title", "slug": "roadmap-slug"}
        """
        available_roadmaps = []
        if not self.roadmaps_dir.exists() or not self.roadmaps_dir.is_dir():
            logger.warning(f"Cannot list roadmaps, directory not found: {self.roadmaps_dir}")
            return []
            
        for roadmap_file in self.roadmaps_dir.glob("*_roadmap.json"):
            try:
                with open(roadmap_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    title = data.get("title", roadmap_file.stem.replace('_roadmap', '').replace('-', ' ').title())
                    slug = data.get("slug", roadmap_file.stem.replace('_roadmap', ''))
                    available_roadmaps.append({"title": title, "slug": slug})
            except Exception as e:
                logger.error(f"Error reading or parsing roadmap file {roadmap_file.name}: {e}", exc_info=True)
        
        logger.info(f"Found {len(available_roadmaps)} available roadmaps.")
        return sorted(available_roadmaps, key=lambda x: x['title'])


# Singleton instance or manage via dependency injection
roadmap_service_instance = RoadmapService()
