from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware
from app.database import Database, get_db  # Ensure get_db is imported here
from app.dependencies import get_settings
from app.routers import user_routes, language_routes, timezone_routes
from app.utils.api_description import getDescription
from app.utils.i18n import get_translator, translate_api_message, DEFAULT_LANGUAGE
from fastapi_babel import Babel, BabelConfigs  # Fixed import
import os

# Initialize the FastAPI app
app = FastAPI(
    title="User Management",
    description=getDescription(),
    version="0.0.1",
    contact={
        "name": "API Support",
        "url": "http://www.example.com/support",
        "email": "support@example.com",
    },
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
)

# Set Babel configuration
app.BABEL_DEFAULT_LOCALE = DEFAULT_LANGUAGE  # Use your existing DEFAULT_LANGUAGE variable
app.BABEL_TRANSLATION_DIRECTORY = "locales"  # Specify your translations directory
app.BABEL_DOMAIN = "messages"  # Define the BABEL_DOMAIN for translations

# Initialize Babel for localization
babel = Babel(app)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware for localization - this handles setting up translation context
@app.middleware("http")
async def add_locale_to_request(request: Request, call_next):
    language = request.headers.get('Accept-Language', DEFAULT_LANGUAGE)
    translator = get_translator(language)
    request.state.gettext = translator
    response = await call_next(request)
    return response

@app.on_event("startup")
async def startup_event():
    settings = get_settings()
    Database.initialize(settings.database_url, settings.debug)

# Exception handler - you can implement custom exception handling if needed
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"message": f"Something went wrong: {str(exc)}"},
    )

# Include routers
from app.routers.user_routes import user_router  
app.include_router(user_routes.user_router)
app.include_router(language_routes.router)
app.include_router(timezone_routes.router)
