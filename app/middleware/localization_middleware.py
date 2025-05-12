from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.localization import LocalizationManager
import re

class LocalizationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle localization in FastAPI application.
    This middleware detects the user's preferred language from:
    1. URL path parameter (e.g., /en/users)
    2. Query parameter (e.g., ?lang=en)
    3. Accept-Language header
    4. Cookie
    5. Default language from settings
    """
    
    def __init__(self, app, localization_manager: LocalizationManager):
        super().__init__(app)
        self.localization_manager = localization_manager
        self.language_pattern = re.compile(r'^/([a-z]{2})(?:/|$)')
    
    async def dispatch(self, request: Request, call_next):
        # Initialize language to default
        language = self.localization_manager.default_language
        
        # Check URL path parameter (e.g., /en/users)
        path_match = self.language_pattern.match(request.url.path)
        if path_match:
            lang_code = path_match.group(1)
            if self.localization_manager.is_supported_language(lang_code):
                language = lang_code
                # Remove language code from path for further processing
                request.scope["path"] = request.url.path[3:]
        
        # Check query parameter (e.g., ?lang=en)
        query_lang = request.query_params.get("lang")
        if query_lang and self.localization_manager.is_supported_language(query_lang):
            language = query_lang
        
        # Check Accept-Language header
        accept_language = request.headers.get("Accept-Language")
        if accept_language and not path_match and not query_lang:
            # Parse the Accept-Language header (e.g., "en-US,en;q=0.9,fr;q=0.8")
            for lang_item in accept_language.split(','):
                lang_code = lang_item.split(';')[0].split('-')[0].lower()
                if self.localization_manager.is_supported_language(lang_code):
                    language = lang_code
                    break
        
        # Check cookie
        cookie_lang = request.cookies.get("preferred_language")
        if cookie_lang and self.localization_manager.is_supported_language(cookie_lang):
            language = cookie_lang
        
        # Set the detected language in request state for use in endpoints
        request.state.language = language
        
        # Call next middleware/endpoint
        response = await call_next(request)
        
        # Optionally set language cookie in response
        if "preferred_language" not in request.cookies or request.cookies.get("preferred_language") != language:
            response.set_cookie(key="preferred_language", value=language, max_age=86400 * 30)  # 30 days
        
        return response