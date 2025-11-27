
import sys
import os
from fastapi.testclient import TestClient
from webapp.main import app

# Add the current directory to the path
sys.path.append(os.getcwd())

client = TestClient(app)

def test_radius_search_with_real_data():
    print("Testing radius search with real database data...")
    
    # Center point near the existing targets (around Taufkirchen)
    # Taufkirchen is at: 48.349, 12.13
    lat, lon = 48.35, 12.13
    
    # Test with different radii
    test_cases = [
        {"radius": 5, "expected_min": 0, "expected_max": 3},
        {"radius": 20, "expected_min": 3, "expected_max": 6},
        {"radius": 50, "expected_min": 6, "expected_max": 6},
        {"radius": 20.5, "expected_min": 3, "expected_max": 6},  # Test float
    ]
    
    for test in test_cases:
        response = client.get(
            f"/api/targets/search-by-radius?lat={lat}&lon={lon}&radius={test['radius']}"
        )
        
        if response.status_code == 200:
            results = response.json()
            count = len(results)
            print(f"Radius: {test['radius']} km -> Found {count} targets")
            
            if test['expected_min'] <= count <= test['expected_max']:
                print(f"  ✓ PASS: Count is within expected range [{test['expected_min']}-{test['expected_max']}]")
            else:
                print(f"  ✗ FAIL: Expected {test['expected_min']}-{test['expected_max']}, got {count}")
            
            # Print target names
            for r in results:
                print(f"    - {r['name']}")
        else:
            print(f"  ✗ FAIL: API returned status {response.status_code}")
            print(f"    Error: {response.text}")

if __name__ == "__main__":
    test_radius_search_with_real_data()
