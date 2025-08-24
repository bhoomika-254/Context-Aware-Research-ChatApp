# Use Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies (if needed for Streamlit/fastapi/etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose both ports
# 7860 -> Streamlit frontend (required by Hugging Face)
# 8000 -> FastAPI backend
EXPOSE 7860 8000

# Start both services: FastAPI on 8000, Streamlit on 7860
CMD uvicorn backend.main:app --host 0.0.0.0 --port 8000 & \
    streamlit run streamlit_app.py --server.port 7860 --server.address 0.0.0.0 --server.headless true
