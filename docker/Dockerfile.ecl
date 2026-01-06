# ECL API Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir fastapi uvicorn pandas numpy scikit-learn joblib

# Copy source code
COPY perda_esperada/ ./perda_esperada/
COPY prinad/ ./prinad/
COPY shared/ ./shared/

# Copy models
COPY prinad/modelo/ /app/modelo/

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8002/health || exit 1

# Start the application
CMD ["python", "-m", "uvicorn", "perda_esperada.src.api:app", "--host", "0.0.0.0", "--port", "8002"]
