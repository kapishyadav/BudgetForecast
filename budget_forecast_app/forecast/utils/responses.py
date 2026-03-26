from rest_framework.response import Response

def api_response(data=None, message=None, status_code=200):
    """Unified success response formatter."""
    payload = {"status": "success"}
    if message:
        payload["message"] = message
    if data is not None:
        payload["data"] = data
    return Response(payload, status=status_code)

def api_error(message="An error occurred", errors=None, status_code=400):
    """Unified error response formatter."""
    payload = {"status": "error", "message": message}
    if errors:
        payload["errors"] = errors
    return Response(payload, status=status_code)
