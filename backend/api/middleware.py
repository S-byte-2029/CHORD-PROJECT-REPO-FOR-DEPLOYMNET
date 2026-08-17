import re
from django.http import HttpResponse
from django.conf import settings

class CorsMiddleware:
    """
    Production-grade CORS middleware that supports:
    - Wildcard Netlify preview deploys (e.g. https://deploy-preview-12--chord.netlify.app)
    - Production domains configured via CORS_ALLOWED_ORIGINS
    - Development environments (localhost, 127.0.0.1)
    - Full preflight OPTIONS handling and credential support
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.netlify_pattern = re.compile(r'^https://[a-zA-Z0-9_\-]+\.netlify\.app$')
        self.railway_pattern = re.compile(r'^https://[a-zA-Z0-9_\-]+\.(?:up\.)?railway\.app$')

    def is_origin_allowed(self, origin: str) -> bool:
        if not origin:
            return False
        
        # Check allow all flag
        if getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', True):
            return True
        
        # Exact match check
        allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        if origin in allowed_origins or '*' in allowed_origins:
            return True
        
        # Regex match for Netlify preview branches and Railway
        if self.netlify_pattern.match(origin) or self.railway_pattern.match(origin):
            return True
        
        # Local development origins
        if origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:'):
            return True

        return False

    def __call__(self, request):
        origin = request.headers.get('Origin', '')

        if request.method == "OPTIONS":
            response = HttpResponse(status=200)
        else:
            response = self.get_response(request)

        if self.is_origin_allowed(origin):
            response["Access-Control-Allow-Origin"] = origin
            response["Access-Control-Allow-Credentials"] = "true"
        elif getattr(settings, 'CORS_ALLOW_ALL_ORIGINS', True):
            response["Access-Control-Allow-Origin"] = "*"
        else:
            # Fallback allowed origin if any configured
            allowed_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
            if allowed_origins:
                response["Access-Control-Allow-Origin"] = allowed_origins[0]

        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With, X-CSRFToken, "
            "Accept, Origin, X-User-Email, Cache-Control"
        )
        response["Access-Control-Expose-Headers"] = "Content-Length, Content-Type, Authorization"
        response["Access-Control-Max-Age"] = "86400"
        return response
