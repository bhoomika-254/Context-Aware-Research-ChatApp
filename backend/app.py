"""
Entry point for Hugging Face Spaces deployment.
"""
import uvicorn
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, '/app')

# Import the FastAPI app from the app package
from app.main import app as fastapi_app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))  # Hugging Face uses port 7860
    uvicorn.run(
        fastapi_app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )