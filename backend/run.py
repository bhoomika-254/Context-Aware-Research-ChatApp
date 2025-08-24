"""
Entry point for Hugging Face Spaces deployment.
"""
import uvicorn
import os
from app.main import app

if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))  # Hugging Face uses port 7860
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        workers=1,
        log_level="info"
    )