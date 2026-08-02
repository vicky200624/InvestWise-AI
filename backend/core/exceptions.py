"""
Custom DRF exception handler for consistent, production-safe error responses.
"""

import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger('investwise')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that returns consistent error structure:
    {"error": "...", "detail": "...", "code": status_code}

    Also ensures sensitive details are hidden in production.
    """
    response = exception_handler(exc, context)

    if response is None:
        # Unhandled exception - log for diagnostics
        view = context.get('view', None)
        view_name = view.__class__.__name__ if view else 'Unknown'
        logger.error(
            "Unhandled exception in %s: %s: %s",
            view_name,
            exc.__class__.__name__,
            str(exc),
            exc_info=True,
        )
        return Response(
            {
                'error': 'INTERNAL_SERVER_ERROR',
                'detail': 'An unexpected error occurred. Please try again later.',
                'code': status.HTTP_500_INTERNAL_SERVER_ERROR,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Build a structured error response
    data = response.data
    if isinstance(data, dict):
        # DRF validation errors -> flatten list of details
        detail = data
        error = data.get('detail', None)
        code = response.status_code
        if not error:
            # Extract first error message
            for field, messages in data.items():
                if isinstance(messages, (list, tuple)) and messages:
                    error = f"{field}: {messages[0]}"
                    break
                elif isinstance(messages, str):
                    error = messages
                    break
            if not error:
                error = 'Invalid request.'
    else:
        error = str(data)
        detail = None
        code = response.status_code

    return Response(
        {
            'error': error,
            'detail': detail,
            'code': response.status_code,
        },
        status=response.status_code,
    )
