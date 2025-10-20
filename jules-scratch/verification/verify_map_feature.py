from playwright.sync_api import sync_playwright

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # Go to the frontend development server URL
        page.goto("http://localhost:5173")

        # Wait for the map container and at least one marker to be visible
        map_container = page.locator(".leaflet-container")
        map_container.wait_for(state="visible", timeout=15000)

        # Markers are img tags with class leaflet-marker-icon
        first_marker = page.locator("img.leaflet-marker-icon").first
        first_marker.wait_for(state="visible", timeout=15000)

        # Take a screenshot to verify the map and markers are displayed
        page.screenshot(path="jules-scratch/verification/map_fix_verification.png")

        browser.close()

if __name__ == "__main__":
    run()
