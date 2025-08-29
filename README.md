# Municipality Scraper

This project scrapes announcements from German municipalities and provides a modern web interface to view the results and manage scraping targets.

## Architecture

The project consists of two main parts:

1.  **Backend**: A [FastAPI](https://fastapi.tiangolo.com/) application that provides a REST API for managing scraping targets and results. It uses SQLAlchemy to interact with a SQLite database. The backend is located in the `webapp/` directory.
2.  **Frontend**: A modern, reactive web application built with [Svelte](https://svelte.dev/) and styled with [Tailwind CSS](https://tailwindcss.com/). The frontend communicates with the backend's API to display data and trigger actions. The frontend code is located in the `src/` directory.

The application is designed to be run with Docker, which simplifies setup and ensures a consistent environment.

## Features

-   **Web Scraper**: A powerful scraper (`scraper.py`) that can:
    -   Fetch and parse HTML from a list of municipal websites.
    -   Identify relevant links based on keywords.
    -   Extract information from detail pages and PDF files.
    -   Use OCR to extract text from scanned PDFs.
-   **Modern UI**: A Svelte-based user interface that allows you to:
    -   View and filter scraped results.
    -   Add and manage target websites for scraping.
    -   Trigger new scraping jobs.
-   **REST API**: A FastAPI backend that exposes endpoints for managing the scraper.
-   **Dockerized**: The entire application can be built and run as a Docker container.

## Development Setup

To run the application in a development environment, you need to run the backend and frontend separately.

### Backend Setup

1.  **Create a Virtual Environment**:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

2.  **Install Python Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the Backend Server**:
    ```bash
    uvicorn webapp.main:app --reload
    ```
    The backend will be available at `http://127.0.0.1:8000`.

### Frontend Setup

1.  **Install Node.js Dependencies**:
    ```bash
    npm install
    ```

2.  **Run the Frontend Development Server**:
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173`. API requests will be automatically proxied to the backend at `http://127.0.0.1:8000`.

## Running with Docker (Production)

The easiest way to run the application is with Docker.

1.  **Build the Docker Image**:
    ```bash
    docker build -t german-bau-scraper .
    ```

2.  **Run the Docker Container**:
    Run the container and expose port `8000` to access the web interface. Mount a local directory to persist the database.

    ```bash
    docker run --rm -p 8000:8000 -v "$(pwd)/output_data:/app/webapp" -e API_KEY="your-secret-api-key" german-bau-scraper
    ```
    *   The `-v` flag mounts the `output_data` directory on your host to the `/app/webapp` directory in the container, where the `webapp.db` SQLite file is stored.
    *   The `-e` flag sets the `API_KEY` environment variable. Make sure to use a strong, secret key.

    You can now access the application at `http://localhost:8000`.

## Running Tests

To run the unit tests for the scraper, make sure `pytest` is installed and then execute:

```bash
python3 -m pytest
```

This will run the tests in `tests/test_scraper.py` and ensure that the core scraping logic is working correctly.
