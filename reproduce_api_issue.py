
import sys
import os
from fastapi.testclient import TestClient
from webapp.main import app

# Add the current directory to the path
sys.path.append(os.getcwd())

client = TestClient(app)

def test_api_radius_type():
    print("Testing API with integer radius...")
    response = client.get("/api/targets/search-by-radius?lat=48.35&lon=12.13&radius=20")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("PASS: Integer radius works.")
    else:
        print(f"FAIL: Integer radius failed: {response.text}")

    print("\nTesting API with float radius...")
    response = client.get("/api/targets/search-by-radius?lat=48.35&lon=12.13&radius=20.5")
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("PASS: Float radius works (coerced or accepted).")
    else:
        print(f"FAIL: Float radius failed: {response.text}")

if __name__ == "__main__":
    test_api_radius_type()
