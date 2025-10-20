# Stage 1: Build the Svelte frontend
FROM node:18-slim as builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps

COPY . .

RUN npm run build

# Stage 2: Build the Python backend
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py ./
COPY scraper_lib ./scraper_lib
COPY webapp ./webapp
COPY seed_db.py ./
COPY import_data.py ./
COPY find_urls.py ./
COPY --from=builder /app/dist ./dist

# Set environment variable for the API key and Python Path
ENV API_KEY ""
ENV PYTHONPATH "${PYTHONPATH}:/app"

EXPOSE 8000

CMD ["uvicorn", "webapp.main:app", "--host", "0.0.0.0", "--port", "8000"]
