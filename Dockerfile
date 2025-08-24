FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create a startup script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Function to start FastAPI backend\n\
start_backend() {\n\
    echo "Starting FastAPI backend server..."\n\
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 &\n\
    BACKEND_PID=$!\n\
    echo "Backend started with PID: $BACKEND_PID"\n\
}\n\
\n\
# Function to start Streamlit frontend\n\
start_frontend() {\n\
    echo "Waiting for backend to start..."\n\
    sleep 5\n\
    \n\
    # Wait for backend to be ready\n\
    echo "Checking backend health..."\n\
    for i in {1..30}; do\n\
        if curl -f http://localhost:8000/health >/dev/null 2>&1; then\n\
            echo "Backend is ready!"\n\
            break\n\
        fi\n\
        echo "Waiting for backend... ($i/30)"\n\
        sleep 2\n\
    done\n\
    \n\
    echo "Starting Streamlit frontend..."\n\
    streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true &\n\
    FRONTEND_PID=$!\n\
    echo "Frontend started with PID: $FRONTEND_PID"\n\
}\n\
\n\
# Function to handle shutdown\n\
cleanup() {\n\
    echo "Shutting down services..."\n\
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null\n\
    exit 0\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Start services based on mode\n\
case "${START_MODE:-both}" in\n\
    "backend")\n\
        echo "Starting in backend-only mode..."\n\
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1\n\
        ;;\n\
    "frontend")\n\
        echo "Starting in frontend-only mode..."\n\
        streamlit run streamlit_app.py --server.port 7860 --server.address 0.0.0.0 --server.headless true\n\
        ;;\n\
    "both"|*)\n\
        echo "Starting in full-stack mode..."\n\
        start_backend\n\
        start_frontend\n\
        \n\
        # Keep the container running\n\
        echo "Both services started. Monitoring..."\n\
        while true; do\n\
            # Check if both processes are still running\n\
            if ! kill -0 $BACKEND_PID 2>/dev/null; then\n\
                echo "Backend process died. Restarting..."\n\
                start_backend\n\
            fi\n\
            \n\
            if ! kill -0 $FRONTEND_PID 2>/dev/null; then\n\
                echo "Frontend process died. Restarting..."\n\
                start_frontend\n\
            fi\n\
            \n\
            sleep 10\n\
        done\n\
        ;;\n\
esac' > /app/start.sh && chmod +x /app/start.sh

# Expose ports for both services
EXPOSE 7860 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default entrypoint
ENTRYPOINT ["/app/start.sh"]
