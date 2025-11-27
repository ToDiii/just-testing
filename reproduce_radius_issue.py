
import sys
import os
import math

# Add the current directory to the path so we can import the webapp modules
sys.path.append(os.getcwd())

from webapp.utils import haversine_distance

def test_haversine():
    print("Testing haversine_distance...")
    # Berlin (approx)
    lat1, lon1 = 52.5200, 13.4050
    # Potsdam (approx)
    lat2, lon2 = 52.3969, 13.0590
    
    # Expected distance is roughly 27 km
    dist = haversine_distance(lat1, lon1, lat2, lon2)
    print(f"Distance between Berlin and Potsdam: {dist:.2f} km")
    
    if 25 < dist < 30:
        print("PASS: Haversine calculation seems correct.")
    else:
        print("FAIL: Haversine calculation seems off.")

def test_radius_logic():
    print("\nTesting radius logic...")
    # Center: Berlin
    center_lat, center_lon = 52.5200, 13.4050
    radius_km = 30
    
    targets = [
        {"name": "Potsdam", "lat": 52.3969, "lon": 13.0590, "should_match": True}, # ~27km
        {"name": "Hamburg", "lat": 53.5511, "lon": 9.9937, "should_match": False}, # ~250km
        {"name": "CloseBy", "lat": 52.5300, "lon": 13.4100, "should_match": True}, # ~1km
    ]
    
    for t in targets:
        dist = haversine_distance(center_lat, center_lon, t["lat"], t["lon"])
        matches = dist <= radius_km
        print(f"Target: {t['name']}, Dist: {dist:.2f} km, Matches: {matches}, Expected: {t['should_match']}")
        
        if matches != t["should_match"]:
            print(f"FAIL: Logic error for {t['name']}")
        else:
            print(f"PASS: Logic correct for {t['name']}")

if __name__ == "__main__":
    test_haversine()
    test_radius_logic()
