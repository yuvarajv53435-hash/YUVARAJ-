from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Import your routes
from .routes import router


# --------------------------------------------------
# Project paths
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title="ComicCraft - AI Comic Story Creator",
    version="1.0.0",
)


# --------------------------------------------------
# Static files
# --------------------------------------------------

app.mount(
    "/static",
    StaticFiles(directory=str(STATIC_DIR)),
    name="static",
)


# --------------------------------------------------
# Routes
# --------------------------------------------------

app.include_router(router)


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
async def health_check():
    """
    Simple endpoint to check whether the API is running.
    """
    gemini_api_key = (
        __import__("os").getenv("GEMINI_API_KEY")
    )

    mode = "live" if gemini_api_key else "demo"

    return {
        "status": "ok",
        "mode": mode,
    }
