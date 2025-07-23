"""
Singleton Services Module

This module provides singleton instances of heavy services to prevent
multiple initialization and improve performance. Services are initialized
once and reused across requests.
"""

import logging
import threading
from typing import Optional

logger = logging.getLogger(__name__)

# Thread lock for singleton initialization
_services_lock = threading.Lock()

# Singleton instances
_tokenization_service: Optional["TokenizationService"] = None
_similarity_service: Optional["SimilarityDetectionService"] = None
_submission_fetcher: Optional["SubmissionFetcher"] = None


def get_tokenization_service() -> "TokenizationService":
    """
    Get singleton instance of TokenizationService.
    Thread-safe lazy initialization.
    """
    global _tokenization_service
    
    if _tokenization_service is None:
        with _services_lock:
            # Double-check locking pattern
            if _tokenization_service is None:
                logger.info("Initializing singleton TokenizationService...")
                from app.domains.tokenization.tokenization_service import TokenizationService
                _tokenization_service = TokenizationService()
                logger.info("TokenizationService singleton initialized successfully")
    
    return _tokenization_service


def get_similarity_service() -> "SimilarityDetectionService":
    """
    Get singleton instance of SimilarityDetectionService.
    Thread-safe lazy initialization.
    """
    global _similarity_service
    
    if _similarity_service is None:
        with _services_lock:
            # Double-check locking pattern
            if _similarity_service is None:
                logger.info("Initializing singleton SimilarityDetectionService...")
                from app.domains.detection.similarity_detection_service import SimilarityDetectionService
                _similarity_service = SimilarityDetectionService()
                logger.info("SimilarityDetectionService singleton initialized successfully")
    
    return _similarity_service


def get_submission_fetcher() -> "SubmissionFetcher":
    """
    Get singleton instance of SubmissionFetcher.
    Thread-safe lazy initialization.
    """
    global _submission_fetcher
    
    if _submission_fetcher is None:
        with _services_lock:
            # Double-check locking pattern
            if _submission_fetcher is None:
                logger.info("Initializing singleton SubmissionFetcher...")
                from app.domains.repositories.submission_fetcher import SubmissionFetcher
                _submission_fetcher = SubmissionFetcher()
                logger.info("SubmissionFetcher singleton initialized successfully")
    
    return _submission_fetcher


def get_visualization_service(tokenization_service: Optional["TokenizationService"] = None) -> "VisualizationService":
    """
    Get instance of VisualizationService.
    Uses provided tokenization_service or gets singleton instance.
    Note: VisualizationService is not a singleton because it depends on TokenizationService.
    """
    if tokenization_service is None:
        tokenization_service = get_tokenization_service()
    
    from app.domains.detection.visualization import VisualizationService
    return VisualizationService(tokenization_service)


def init_services():
    """
    Initialize all singleton services during application startup.
    This can be called during application lifespan to warm up services.
    """
    logger.info("Warming up singleton services...")
    get_tokenization_service()
    get_similarity_service() 
    get_submission_fetcher()
    logger.info("All singleton services warmed up successfully")


def cleanup_services():
    """
    Cleanup services during application shutdown.
    """
    global _tokenization_service, _similarity_service, _submission_fetcher
    
    logger.info("Cleaning up singleton services...")
    
    # Reset singleton references
    _tokenization_service = None
    _similarity_service = None
    _submission_fetcher = None
    
    logger.info("Singleton services cleaned up") 