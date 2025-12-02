from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, Callable, Awaitable
import os
import logging

from .routes import courses
from .core.config import get_data_file_path
from .core.exceptions import LMSException
from .core.error_tracking import get_error_tracker, ErrorTracker
from .core.notifications import get_notification_service, NotificationService

logger: logging.Logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def create_app() -> FastAPI:
    """Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    app: FastAPI = FastAPI(title="LMS Exercise (JSON-backed)")
    
    # Initialize error tracker and notifications at startup
    error_tracker: ErrorTracker = get_error_tracker()
    notification_service: NotificationService = get_notification_service()

    @app.on_event("startup")
    def startup() -> None:
        """Initialize application on startup."""
        data_path: str = get_data_file_path()
        dirp: str = os.path.dirname(data_path)
        if not os.path.exists(dirp):
            os.makedirs(dirp, exist_ok=True)
        logger.info(f"Application started. Data path: {data_path}")

    @app.on_event("shutdown")
    def shutdown() -> None:
        """Log application shutdown."""
        error_stats: Dict[str, Any] = error_tracker.get_error_stats()
        if error_tracker.is_critical_failure():
            logger.warning(f"Shutdown with critical failures: {error_stats}")
        else:
            logger.info(f"Application shutdown. Error stats: {error_stats}")

    # Global exception handler for LMS exceptions
    @app.exception_handler(LMSException)
    async def lms_exception_handler(
        request: Request,
        exc: LMSException
    ) -> JSONResponse:
        """Handle custom LMS exceptions.
        
        Args:
            request: HTTP request object
            exc: LMSException instance
            
        Returns:
            JSONResponse with appropriate status code
        """
        status_code: int = 500
        if exc.error_code == "COURSE_NOT_FOUND":
            status_code = 404
        elif exc.error_code == "VALIDATION_ERROR":
            status_code = 422
        elif exc.error_code in ["FILE_LOCK_ERROR", "DATA_PERSISTENCE_ERROR"]:
            status_code = 503  # Service unavailable

        # Notify on critical errors
        if status_code >= 500:
            notification_service.notify_error(
                error_type=exc.__class__.__name__,
                message=exc.message,
                error_code=exc.error_code,
                details=exc.details,
                severity="CRITICAL",
            )

        return JSONResponse(status_code=status_code, content=exc.to_dict())

    # Global exception handler for unexpected exceptions
    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request,
        exc: Exception
    ) -> JSONResponse:
        """Handle unexpected exceptions.
        
        Args:
            request: HTTP request object
            exc: Exception instance
            
        Returns:
            JSONResponse with 500 status
        """
        error_record: Dict[str, Any] = error_tracker.log_error(
            "UnhandledException",
            f"Unexpected error: {str(exc)}",
            "UNHANDLED_EXCEPTION",
            {"endpoint": str(request.url)},
            exc,
        )

        # Notify critical failure
        notification_service.notify_error(
            error_type="UnhandledException",
            message=error_record["message"],
            error_code=error_record["error_code"],
            details=error_record["details"],
            severity="CRITICAL",
        )

        return JSONResponse(
            status_code=500,
            content={
                "message": "Internal server error",
                "error_code": "INTERNAL_ERROR",
                "details": {"request_url": str(request.url)},
            },
        )

    app.include_router(courses.router)

    @app.get("/health")
    def health() -> Dict[str, Any]:
        """Health check endpoint with error statistics.
        
        Returns:
            Dict containing status and error statistics
        """
        error_stats: Dict[str, Any] = error_tracker.get_error_stats()
        status: str = "healthy"
        if error_tracker.is_critical_failure():
            status = "degraded"

        return {
            "status": status,
            "errors": error_stats,
            "alerts": notification_service.get_recent_alerts(limit=3),
        }

    @app.get("/errors")
    def get_errors() -> Dict[str, Any]:
        """Endpoint to retrieve error statistics and recent alerts.
        
        Returns:
            Dict containing error statistics and recent alerts
        """
        return {
            "stats": error_tracker.get_error_stats(),
            "recent_alerts": notification_service.get_recent_alerts(limit=10),
        }

    return app


app: FastAPI = create_app()
