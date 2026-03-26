import logging
from rest_framework.views import exception_handler
from ..utils.responses import api_error

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Global exception handler for DRF views.
    Catches both DRF exceptions and standard Python exceptions.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)

    # If response exists, it's a known DRF exception (like a bad Serializer payload)
    if response is not None:
        return api_error(
            message="Validation Failed",
            errors=response.data,
            status_code=response.status_code
        )

    # Unhandled Python exceptions (e.g., ValueError, Database errors)
    logger.error(f"Unhandled exception in {context['view'].__class__.__name__}: {exc}", exc_info=True)

    # We explicitly raise ValueErrors in our DTOs when data is bad
    if isinstance(exc, ValueError):
        return api_error(message=str(exc), status_code=400)

    # Generic fallback for 500 errors so the user never sees a raw HTML traceback
    return api_error(message="Internal Server Error. Please try again later.", status_code=500)
