from fastapi import Request, status
from fastapi.responses import JSONResponse
import sentry_sdk
from .logger import setup_logger

logger = setup_logger(__name__)

async def validation_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "body": exc.body
        }
    )

async def database_exception_handler(request: Request, exc):
    logger.error(f"Database error: {str(exc)}")
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Database error occurred"}
    )

async def general_exception_handler(request: Request, exc):
    logger.error(f"Unexpected error: {str(exc)}")
    sentry_sdk.capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"}
    )
