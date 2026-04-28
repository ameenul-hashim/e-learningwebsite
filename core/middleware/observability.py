import uuid
import logging

class RequestIDMiddleware:
    """
    Adds a unique request ID to each request for tracing in logs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get('X-Request-ID', str(uuid.uuid4()))
        request.request_id = request_id
        
        response = self.get_response(request)
        response['X-Request-ID'] = request_id
        return response

class RequestIDFilter(logging.Filter):
    """
    Filter to inject request_id into logging records safely.
    """
    def filter(self, record):
        # Default to N/A if not found
        record.request_id = getattr(record, 'request_id', 'N/A')
        return True
