from fastapi import HTTPException, status
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIError(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        logger.error(f"API Error: {detail}")

def validate_date_format(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def handle_db_error(e: Exception, operation: str):
    logger.error(f"Database error during {operation}: {str(e)}")
    raise APIError(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Database error during {operation}"
    )
