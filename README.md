# Municipality Scraper

This project scrapes announcements from German municipalities and provides a modern web interface to view the results and manage scraping targets.

## Architecture

The project consists of three main parts:

1.  **Backend**: A [FastAPI](https://fastapi.tiangolo.com/) application in `webapp/` that provides a REST API for managing scraping targets, keywords, and results. It uses SQLAlchemy to interact with a SQLite database and can trigger scraping jobs as background tasks.
2.  **Frontend**: A modern, reactive web application in `src/` built with [Svelte](https://svelte.dev/) and styled with [Tailwind CSS](https://tailwindcss.com/). The frontend communicates with the backend's API to display data and trigger actions.
3.  **Scraper Library**: A refactored scraping logic located in the `scraper_lib/` directory. This library handles the heavy lifting of fetching, parsing, and extracting data. It is invoked by the FastAPI backend.

The application is designed to be run with Docker, which simplifies setup and ensures a consistent environment.

## Proxmox LXC Installation (Recommended for Production)

For a dedicated, lightweight production environment, you can install the application in a Proxmox LXC container using the provided installation script.

1.  **Create an LXC Container**:
    *   Use a modern Debian or Ubuntu template (e.g., Debian 12 or Ubuntu 24.04).
    *   **Recommended Resources**: 2 CPU Cores, 4GB RAM, 32GB Storage.

2.  **Run the Installer**:
    *   Start the container and open its console.
    *   Execute the following command to download and run the installation script:
        ```bash
        bash -c "$(wget -qLO - https://raw.githubusercontent.com/ToDiii/just-testing/main/install.sh)"
        ```

3.  **Access the Application**:
    *   Once the script finishes, it will display the IP address of the container.
    *   You can access the web interface at `http://<CONTAINER_IP>:8000`.

## Development Setup

The recommended way to run the application for both development and production is using Docker Compose. A manual setup is also possible for advanced use cases.

### Running with Docker Compose (Recommended)

This project includes two Docker Compose files:
-   `docker-compose.yml`: For a production-like environment. It builds the frontend and serves it via the FastAPI backend.
-   `docker-compose.dev.yml`: For development. It enables live-reloading for both the backend and frontend.

**1. Production-like Environment:**

This method is ideal for testing the final build or for a simple deployment.

```bash
# Build and start the container in the background
docker-compose up --build -d

# Populate the database with a small test set
docker-compose exec app python3 seed_db.py

# Or populate with the full dataset (takes a long time)
# docker-compose exec app python3 import_data.py
```
The application will be available at `http://localhost:8000`.

To stop the container, run:
```bash
docker-compose down
```

**2. Development Environment (with Live-Reload):**

This method is ideal for active development, as code changes will be reflected instantly without rebuilding the container.

```bash
# Build and start the containers
docker-compose -f docker-compose.dev.yml up --build

# In a separate terminal, populate the database
docker-compose -f docker-compose.dev.yml exec app python3 seed_db.py
```
-   The **Backend API** will be available at `http://localhost:8000`.
-   The **Frontend Dev Server** will be available at `http://localhost:5173`.

To stop the development server, press `Ctrl+C` in the terminal where it is running, or run:
```bash
docker-compose -f docker-compose.dev.yml down
```

### Manual Development Setup

This method is useful if you want to run the frontend and backend as separate, local processes without Docker.

### 1. Database Setup

You have two options for populating the database with municipality data.

**Option A: Full Import (For Production / Full-Scale Testing)**

To populate the database with a comprehensive list of over 10,000 German municipalities and their associated postal codes, run the main import script. This script combines data from two different public datasets to create a complete record for each municipality.

```bash
python3 import_data.py
```
This process is idempotent (it won't create duplicates) but may take some time. For a quick test of the import logic, you can use the `--limit` flag:

```bash
# Import the first 100 records to test the process
python3 import_data.py --limit 100
```

**Option B: Seeding a Small Test Set (For Quick, Repeatable Tests)**

If you only need a small, guaranteed set of known municipalities for testing, run the seed script.

```bash
python3 seed_db.py
```
This script ensures 6 specific Bavarian municipalities are present in the database with their real URLs and postal codes, creating or updating them as needed. This is the fastest way to get a usable test environment.

### 2. Finding Official URLs (Optional, Long-Running)

After populating the database via the full import, most municipalities will have placeholder URLs. To find their real websites, you can run the URL finder script:

```bash
python3 find_urls.py
```
This script uses Google Search to find the official URL for each entry. **Warning:** This process is extremely slow (many hours). To test the script's functionality, use the `--limit` flag:

```bash
# Process the first 5 municipalities with placeholder URLs
python3 find_urls.py --limit 5
```

### 3. Backend & Frontend Setup

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

4.  **Install Node.js Dependencies** (in a separate terminal):
    ```bash
    npm install
    ```

5.  **Create Environment File**:
    Create a `.env` file in the project root and set the API key:
    ```env
    VITE_API_KEY=dev
    ```

6.  **Run the Frontend Development Server**:
    ```bash
    npm run dev
    ```
    The frontend will be available at `http://localhost:5173`.

## Running Tests

To run the unit tests for the scraper library, make sure `pytest` is installed and then execute:

```bash
python3 -m pytest
```
This will run the tests in `tests/test_scraper.py` and ensure the core scraping logic is working correctly.