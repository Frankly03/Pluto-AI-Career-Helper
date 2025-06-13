# backend/app/services/interest_service.py

import json
import logging
from typing import Dict, List, Set
from pathlib import Path
from collections import defaultdict, Counter

from app.core.config import settings
from app.models.career import Career # For type hinting if processing from raw career data

logger = logging.getLogger(__name__)

class InterestService:
    """
    Service for handling interest tags.
    It can load processed interest tags or generate them from career data.
    """
    _processed_interests: Dict[str, List[str]] = {}
    _all_tags_flat_list: List[str] = [] # For quick validation or suggestions

    def __init__(self, 
                 career_data_path: Path = settings.CAREER_DATA_PATH,
                 processed_tags_path: Path = settings.PROCESSED_INTEREST_TAGS_PATH):
        self.career_data_path = career_data_path
        self.processed_tags_path = processed_tags_path
        self._load_or_process_interests()

    def _load_or_process_interests(self):
        """
        Tries to load pre-processed interest tags. If not found,
        it processes them from the raw career_data.json.
        """
        try:
            if self.processed_tags_path.exists():
                logger.info(f"Loading processed interest tags from {self.processed_tags_path}")
                with open(self.processed_tags_path, 'r') as f:
                    InterestService._processed_interests = json.load(f)
                self._populate_flat_list()
                logger.info("Processed interest tags loaded successfully.")
            elif self.career_data_path.exists():
                logger.info(f"{self.processed_tags_path} not found. Processing interests from {self.career_data_path}.")
                with open(self.career_data_path, 'r', encoding="utf-8") as f:
                    raw_career_data = json.load(f)
                
                InterestService._processed_interests = self._process_tags_from_career_data(raw_career_data)
                self._populate_flat_list()
                # Optionally save the processed tags for future use
                try:
                    with open(self.processed_tags_path, 'w') as f_out:
                        json.dump(InterestService._processed_interests, f_out, indent=2)
                    logger.info(f"Processed interest tags saved to {self.processed_tags_path}")
                except IOError as e:
                    logger.error(f"Error saving processed interest tags: {e}", exc_info=True)
            else:
                logger.error(f"Neither processed interest tags file nor career data file found. Cannot initialize interests.")
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from interest/career data file: {e}", exc_info=True)
            InterestService._processed_interests = {} # Reset on error
        except Exception as e:
            logger.error(f"An unexpected error occurred during interest loading/processing: {e}", exc_info=True)
            InterestService._processed_interests = {} # Reset on error


    def _process_tags_from_career_data(self, career_data_list: List[Dict]) -> Dict[str, List[str]]:
        """
        Processes career data to extract and group interest tags by 'field'.
        """
        field_tag_counter: Dict[str, Counter] = defaultdict(Counter)
        global_counter: Counter = Counter()

        for career_item_dict in career_data_list:
            career_item = Career(**career_item_dict)
            item_fields = career_item.field if career_item.field else ["General"]
            item_tags = career_item.interest_tags

            global_counter.update(item_tags)

            for field_name in item_fields:
                field_tag_counter[field_name].update(item_tags)
            
        if "General" not in field_tag_counter:
            field_tag_counter["General"] = global_counter
        else:
            field_tag_counter["General"].update(global_counter)
        
        self.global_tag_counter = global_counter
        
        processed_tags: Dict[str, List[str]] = {
            field: [tag for tag, _ in field_tag_counter[field].most_common()]
            for field in field_tag_counter
        }
        return processed_tags
    
    def _populate_flat_list(self):
        """Populates a flat list of all unique tags from _processed_interests."""
        if InterestService._processed_interests and hasattr(self, "_global_tag_counter"):
            sorted_tags = [tag for tag, _ in self._global_tag_counter.most_common()]
            InterestService._all_tags_flat_list = sorted_tags


    def get_all_interest_tags(self) -> Dict[str, List[str]]:
        """
        Returns all processed interest tags, grouped by field.
        """
        if not InterestService._processed_interests:
            # Attempt to reload/reprocess if empty, could indicate an initial load issue
            logger.warning("Processed interests is empty, attempting to reload/reprocess.")
            self._load_or_process_interests()
        return InterestService._processed_interests
    
    def get_flat_list_of_tags(self) -> List[str]:
        """
        Returns a flat list of all unique available interest tags.
        """
        if not InterestService._all_tags_flat_list and InterestService._processed_interests:
            self._populate_flat_list()
        return InterestService._all_tags_flat_list

# Initialize a singleton instance or manage via dependency injection
interest_service_instance = InterestService()

# To access the service:
# from app.services.interest_service import interest_service_instance
# tags = interest_service_instance.get_all_interest_tags()
