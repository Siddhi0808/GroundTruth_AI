# Same Python version as the dev venv and CI (the pinned requirements need Python >= 3.12)
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies for PDF parsing and OCR fallback
RUN apt-get update && apt-get install -y --no-install-recommends \
    poppler-utils \
    tesseract-ocr \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies. The extra index provides CPU-only PyTorch wheels (e.g. torch 2.13.0+cpu),
# which satisfy the torch==2.13.0 pin without pulling several GB of CUDA libraries into the image.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI server
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
