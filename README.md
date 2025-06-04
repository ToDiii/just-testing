# German Municipality Construction & Land Announcement Scraper

This Python script is designed to scrape announcements related to new construction areas, development plans, land sales, and similar topics from the websites of various German municipalities.

## Features

- Fetches and parses HTML from a list of predefined municipal websites.
- Identifies relevant links on these websites based on a list of keywords.
- Follows links to detail pages and extracts information such as:
    - Title of the announcement
    - Descriptive text snippet containing keywords
    - Publication date (if found)
    - URL of the original announcement
    - Source municipality
- Downloads and extracts text from linked PDF files, searching for similar information.
- Saves all extracted data into `extracted_data.json` (JSON format) and `extracted_data.csv` (CSV format).
- Includes basic error handling and polite scraping practices (configurable delay).

## Setup and Installation

1.  **Create a Project Directory:**
    If you haven't already, create a directory for this project. The script assumes it's located in a directory like `german_bau_scraper`.

2.  **Create a Virtual Environment (Recommended):**
    It's highly recommended to use a Python virtual environment to manage dependencies. Open your terminal or command prompt, navigate to the project directory, and run:
    ```bash
    python3 -m venv venv
    ```

3.  **Activate the Virtual Environment:**
    -   On macOS and Linux:
        ```bash
        source venv/bin/activate
        ```
    -   On Windows:
        ```bash
        .\venv\Scripts\activate
        ```

4.  **Install Dependencies:**
    The required Python packages are listed in `requirements.txt`. Install them using pip:
    ```bash
    pip install -r requirements.txt
    ```
    The `requirements.txt` file should contain:
    ```
    requests
    beautifulsoup4
    PyPDF2
    ```

## Running the Scraper

Once the setup is complete, you can run the scraper from within the project directory (where `scraper.py` is located):

```bash
python3 scraper.py

The script will print progress messages to the console, including which sites are being processed, links being followed, and data being extracted or saved.
Output Files

The scraper generates two output files in the same directory as scraper.py:

    extracted_data.json: A JSON file where each object represents an extracted announcement. This format is useful for programmatic access.
    extracted_data.csv: A CSV file with the same data, suitable for opening in spreadsheet software.

The fields for each extracted item are typically:

    title: The title of the announcement.
    description: A text snippet from the page/PDF containing relevant keywords.
    publication_date: The publication date, if found (format: YYYY-MM-DD). "Not found" otherwise.
    url: The direct URL to the announcement page or PDF document.
    source: The name of the municipality or administrative group.
    type: Whether the data came from an 'HTML Page' or 'PDF'.

Configuration and Customization

The main script scraper.py contains several areas you might want to customize:

    TARGET_SITES (Dictionary): Located at the beginning of the if __name__ == "__main__": block. This dictionary maps municipality names to their main website URLs. You can add, remove, or modify entries. For some sites, you might achieve better results by pointing the URL directly to their "Aktuelles" (News) or "Bekanntmachungen" (Announcements) page.

    KEYWORDS (List): A global list at the top of the script. Add or remove keywords (in lowercase) to tailor the search.

    MAX_HTML_LINKS_PER_SITE and MAX_PDF_LINKS_PER_SITE (Variables): In the if __name__ == "__main__": block. These limit how many relevant HTML detail pages or PDF links the scraper will process from each main site. Adjust these for broader or narrower scraping.

    POLITENESS_DELAY_SECONDS (Variable): In the if __name__ == "__main__": block. Sets a delay (in seconds) between HTTP requests to the same site's subpages. It's important to keep this at a reasonable value (e.g., 0.5-2 seconds) to avoid overloading servers.

Advanced Customization (Site-Specific Parsing)

Websites have diverse structures. While this scraper attempts generic extraction, you will likely need to customize the parsing logic for optimal results on each specific website. Key areas in scraper.py:

    extract_data_from_html_page function:
        title_selectors_try: A list of CSS selectors used to find the title. You may need to add or adjust these based on how titles are marked up on target sites (e.g., specific <h1> classes).
        main_content_selectors: A list of CSS selectors to identify the main content area of a page. This helps focus the search for relevant paragraphs and dates. Inspect target websites' HTML structure (using browser developer tools) to find appropriate selectors.
        Date Extraction Logic: The date parsing uses regular expressions and attempts to parse common formats. This is notoriously tricky and often requires site-specific patterns or adjustments to the date_patterns list or the parsing logic within this function.

    extract_data_from_pdf_text function:
        Title and date extraction from PDFs are also based on heuristics (e.g., first few lines for title, regex for dates). These might need refinement based on common PDF layouts from the target municipalities.

Important Considerations

    Website Structure Changes: Websites change their layout over time. If the scraper stops working for a particular site, you'll likely need to update its CSS selectors or parsing logic.
    Anti-Scraping Measures: Some websites may have measures to block or limit automated scraping. If you encounter issues (e.g., getting blocked), you might need to use more advanced techniques like rotating user agents, using proxies, or reducing crawl speed further. This script uses a default User-Agent.
    Robots.txt: While this script does not automatically parse robots.txt files, it's good practice to be aware of a website's scraping policies if you intend to scrape frequently or extensively.
    Error Handling: The script includes basic error handling for network requests and file operations. For production use, you might want to enhance this (e.g., more detailed logging, retry mechanisms).

Happy scraping! Remember to be respectful of the websites you are scraping.
Running with Docker

You can also build a Docker image and run the scraper in a container. This is useful for ensuring a consistent environment and managing dependencies easily.

1. Build the Docker Image:

Navigate to the project directory (the one containing Dockerfile, scraper.py, and requirements.txt) in your terminal and run:

docker build -t german-bau-scraper .

This will create a Docker image named german-bau-scraper based on the instructions in the Dockerfile.

2. Prepare an Output Directory on Your Host Machine:

Create a directory on your computer where you want the scraper's output files (extracted_data.json and extracted_data.csv) to be saved. For example:

mkdir output_data

3. Run the Docker Container:

Execute the following command to run the scraper. This command mounts the output_data directory you created into the /app directory within the container (which is the working directory where scraper.py runs and saves its files).

    For macOS/Linux (using $(pwd) for current directory):

    docker run --rm -v "$(pwd)/output_data:/app" german-bau-scraper

    (The --rm flag automatically removes the container when it exits.)

    For Windows (using %cd% for current directory with Command Prompt, or ${PWD} with PowerShell):
        Command Prompt:

        docker run --rm -v "%cd%\output_data:/app" german-bau-scraper

        PowerShell:

        docker run --rm -v "${PWD}/output_data:/app" german-bau-scraper

Explanation of the docker run command:

    --rm: Automatically removes the container filesystem when the container exits. This is good for cleanup for tasks that run and then stop.
    -v "$(pwd)/output_data:/app" (or Windows equivalent): This is the volume mount.
        $(pwd)/output_data (or %cd%\output_data or ${PWD}/output_data): Path to the directory on your host machine.
        :/app: Path inside the container where the host directory will be mounted. Since scraper.py saves files to its current directory (/app inside the container), the output files will appear in your output_data folder on your host.

After the container finishes running, you will find extracted_data.json and extracted_data.csv in the output_data directory on your host system.

## Running Tests

To run the unit tests, make sure `pytest` is installed and then execute:

```bash
pytest
```

All tests should pass and confirm that the scraper's helper functions work as expected.
