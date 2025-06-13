# backend/app/ml/sentence_transformer_loader.py

from sentence_transformers import SentenceTransformer
import numpy as np
import os
import pickle
import logging

logger = logging.getLogger(__name__)

MODEL_NAME = 'all-mpnet-base-v2' 
EMBEDDINGS_FILE_PATH = os.path.join(os.path.dirname(__file__), 'embeddings.pkl')
# IMPORTANT: This assumes 'embeddings.pkl' is present in the same directory (backend/app/ml/).
# You would typically generate this file offline using your `career_data.json` and the chosen SentenceTransformer model.
# For example, iterate through job descriptions in career_data.json, encode them, and save the resulting embeddings.

class SentenceTransformerLoader:
    """
    Handles loading the Sentence Transformer model and pre-computed embeddings.
    """
    _model = None
    _career_embeddings = None
    _career_job_titles = None # To map embeddings back to job titles

    @classmethod
    def get_model(cls):
        """
        Loads and returns the Sentence Transformer model.
        Caches the model in memory after the first load.
        """
        if cls._model is None:
            try:
                logger.info(f"Loading Sentence Transformer model: {MODEL_NAME}")
                cls._model = SentenceTransformer(MODEL_NAME)
                logger.info("Sentence Transformer model loaded successfully.")
            except Exception as e:
                logger.error(f"Error loading Sentence Transformer model: {e}", exc_info=True)
                # Fallback or raise error depending on desired behavior
                # For now, we'll allow it to be None and handle it in services
                cls._model = None
        return cls._model

    @classmethod
    def get_career_embeddings(cls, career_data: list):
        """
        Loads pre-computed career embeddings from a .pkl file.
        If the file doesn't exist, it attempts to generate and save them (placeholder).

        In a real application, embeddings.pkl should be pre-generated.
        This method also stores job titles corresponding to the embeddings.
        """
        if cls._career_embeddings is None or cls._career_job_titles is None:
            if not career_data:
                logger.warning("Career data is empty. Cannot load or generate embeddings.")
                return None, None

            try:
                if os.path.exists(EMBEDDINGS_FILE_PATH):
                    logger.info(f"Loading pre-computed embeddings from {EMBEDDINGS_FILE_PATH}")
                    with open(EMBEDDINGS_FILE_PATH, 'rb') as f:
                        data = pickle.load(f)
                        cls._career_embeddings = data['embeddings']
                        cls._career_job_titles = data['job_titles']
                    logger.info("Pre-computed embeddings loaded successfully.")
                else:
                    logger.warning(f"{EMBEDDINGS_FILE_PATH} not found. Attempting to generate (placeholder).")
                    # Placeholder: In a real scenario, you'd generate these if missing
                    # and if it's feasible at runtime, or more likely, ensure they are pre-generated.
                    # For this example, we'll just log a warning and return None.
                    # If you want to generate them on the fly (not recommended for large datasets at startup):
                    model = cls.get_model()
                    if model:
                        cls._career_job_titles = [item.get("job_title", "Unknown Job") for item in career_data]
                        # Combine relevant text fields for embedding, e.g., desc and interest_tags
                        texts_to_embed = [
                            item.get("desc", "") + " " + " ".join(item.get("interest_tags", []))
                            for item in career_data
                        ]
                        cls._career_embeddings = model.encode(texts_to_embed, convert_to_tensor=False)
                        with open(EMBEDDINGS_FILE_PATH, 'wb') as f:
                            pickle.dump({'job_titles': cls._career_job_titles, 'embeddings': cls._career_embeddings}, f)
                        logger.info(f"Generated and saved embeddings to {EMBEDDINGS_FILE_PATH}")
                    else:
                        logger.error("Cannot generate embeddings: Sentence Transformer model not loaded.")
                        return None, None
                    logger.error(f"Embeddings file {EMBEDDINGS_FILE_PATH} not found. This file needs to be pre-generated.")
                    cls._career_embeddings = None
                    cls._career_job_titles = None


            except Exception as e:
                logger.error(f"Error loading or processing career embeddings: {e}", exc_info=True)
                cls._career_embeddings = None
                cls._career_job_titles = None
        
        return cls._career_embeddings, cls._career_job_titles

# Example of how you might generate embeddings.pkl offline (not part of the runtime app):
def generate_embeddings_offline(career_data_path, output_path):
    import json
    model = SentenceTransformer(MODEL_NAME)
    with open(career_data_path, 'r') as f:
        careers = json.load(f)
    
    job_titles = []
    texts_to_embed = []
    for career in careers:
        job_titles.append(career.get("job_title", "Unknown Job"))
        # Using description and interest tags for embedding
        text = career.get("desc", "")
        if career.get("interest_tags"):
            text += " " + " ".join(career["interest_tags"])
        texts_to_embed.append(text)
            
    embeddings = model.encode(texts_to_embed, show_progress_bar=True, convert_to_tensor=False)
    
    with open(output_path, 'wb') as f_out:
        pickle.dump({'job_titles': job_titles, 'embeddings': embeddings}, f_out)
    print(f"Embeddings saved to {output_path}")

# if __name__ == '__main__':
#     # This would be run separately, not as part of the FastAPI app startup.
#     # Ensure career_data.json is in the correct relative path or provide absolute path.
#     # current_dir = os.path.dirname(os.path.abspath(__file__))
#     # career_data_file = os.path.join(current_dir, '..', 'data', 'career_data.json')
#     # embeddings_output_file = os.path.join(current_dir, 'embeddings.pkl')
#     # generate_embeddings_offline(career_data_file, embeddings_output_file)

#     # To test loading (assuming embeddings.pkl exists and career_data.json is loaded elsewhere)
#     # model = SentenceTransformerLoader.get_model()
#     # embeddings, titles = SentenceTransformerLoader.get_career_embeddings(career_data_loaded_elsewhere)
#     # if model and embeddings is not None:
#     #     print("Model and embeddings loaded.")
#     # else:
#     #     print("Failed to load model or embeddings.")
#     pass
