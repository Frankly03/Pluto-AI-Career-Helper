# backend/app/main.py

import logging
import sys
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import recommendations, roadmaps, resume_matcher
from app.utils.logger import logger
# Import services to ensure they are initialized if they have startup logic (like loading data)
from app.services import interest_service, recommendation_service, roadmap_service, resume_service 
from app.ml import sentence_transformer_loader # Ensure model loader is imported

# --- Logging Configuration ---
# Basic logging setup
logging.basicConfig(
    level=logging.INFO, # Adjust level as needed (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout) # Log to stdout
        # You can add FileHandler here if you want to log to a file
        # logging.FileHandler("app.log"), 
    ]
)
logger = logging.getLogger(__name__)

# --- FastAPI Application Initialization ---
app = FastAPI(
    title=settings.APP_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- CORS Middleware Configuration ---
# Set up CORS (Cross-Origin Resource Sharing)
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin).strip() for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"], # Allows all methods
        allow_headers=["*"], # Allows all headers
    )
else:
    # If no origins are specified, you might want to log a warning or have a default restrictive policy
    logger.warning("CORS_ORIGINS not set. CORS middleware not configured with specific origins.")


# --- Event Handlers (Startup/Shutdown) ---
@app.on_event("startup")
async def startup_event():
    """
    Actions to perform on application startup.
    - Initialize SBERT model and embeddings
    - Load data for services
    """
    logger.info("Application startup sequence initiated...")
    
    # Initialize SBERT model (it's class-based, so get_model call will load it)
    logger.info("Attempting to load Sentence Transformer model...")
    sbert_model = sentence_transformer_loader.SentenceTransformerLoader.get_model()
    if sbert_model:
        logger.info("Sentence Transformer model loaded successfully via loader.")
    else:
        logger.error("Failed to load Sentence Transformer model via loader during startup!")

    # Services are typically initialized when their modules are imported or when their instances are created.
    # For example, recommendation_service_instance = RecommendationService() will trigger its __init__.
    # We can explicitly call methods here if needed, but the current structure loads data on service instantiation.
    
    # Example: Ensure career data and embeddings are loaded by RecommendationService
    # This is now part of RecommendationService.__init__
    # recommendation_service.recommendation_service_instance._load_career_data_and_embeddings()

    # Ensure interest tags are loaded
    # This is part of InterestService.__init__
    # interest_service.interest_service_instance._load_or_process_interests()

    logger.info("Data loading for services (triggered by their initialization):")
    logger.info(f"- Interest Service: {'Loaded' if interest_service.interest_service_instance._processed_interests else 'Load Issue'}")
    logger.info(f"- Recommendation Service (Careers): {len(recommendation_service.recommendation_service_instance.career_data_list) if recommendation_service.recommendation_service_instance.career_data_list else 'Load Issue'}")
    logger.info(f"- Recommendation Service (Embeddings): {'Loaded' if recommendation_service.recommendation_service_instance.career_embeddings is not None else 'Load Issue'}")
    logger.info(f"- Roadmap Service: Initialized (loads on demand or lists at startup)")
    logger.info(f"- Resume Service (Prebuilt JDs): {len(resume_service.resume_service_instance.prebuilt_jds) if resume_service.resume_service_instance.prebuilt_jds else 'Load Issue'}")

    logger.info("Application startup complete.")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Actions to perform on application shutdown.
    """
    logger.info("Application shutdown sequence initiated...")
    # Add any cleanup tasks here, e.g., closing database connections if you add them later
    logger.info("Application shutdown complete.")


# --- API Routers Inclusion ---
# Include routers from the /routers directory
app.include_router(recommendations.router, prefix=settings.API_V1_STR + "/recommendations", tags=["Recommendations & Interests"])
app.include_router(roadmaps.router, prefix=settings.API_V1_STR + "/roadmaps", tags=["Career Roadmaps"])
app.include_router(resume_matcher.router, prefix=settings.API_V1_STR + "/matcher", tags=["Resume Matcher"])


# --- Root Endpoint ---
@app.get("/", tags=["Root"])
async def read_root():
    """
    Root endpoint providing a welcome message and basic API info.
    """
    return {
        "message": f"Welcome to the {settings.APP_NAME}",
        "documentation_url": "/docs",
        "re_doc_url": "/redoc",
        "ollama_base_url_configured": settings.OLLAMA_BASE_URL,
        "ollama_model_configured": settings.OLLAMA_MODEL
    }

# --- Health Check Endpoint ---
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Simple health check endpoint.
    """
    # Could add checks for DB connection, Ollama reachability, etc.
    return {"status": "ok"}

# To run the app (e.g., using uvicorn):
# uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
