# Use a single stage build for simplicity and to support development mode
FROM python:3.11-slim

# Install system dependencies, including curl to fetch Node.js
RUN apt-get update && apt-get install -y \
    curl \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev && \
    rm -rf /var/lib/apt/lists/*

# Install Node.js v18
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy all source files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Node.js dependencies and build frontend
RUN npm install --legacy-peer-deps
RUN npm run build

# Set environment variable for the API key and Python Path
ENV API_KEY ""
ENV PYTHONPATH "${PYTHONPATH}:/app"

EXPOSE 8000

CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
