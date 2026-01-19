
import requests
import sys

BASE_URL = "http://localhost:8001"

def test_notifications():
    print("Testing Notification System...")

    # 1. Create a webhook configuration
    print("\n1. Creating Webhook Configuration...")
    webhook_url = "https://httpbin.org/post"  # Use httpbin to verify POST requests
    config_data = {
        "type": "webhook",
        "recipient": webhook_url,
        "enabled": True
    }
    response = requests.post(f"{BASE_URL}/api/notifications/config", json=config_data)
    if response.status_code == 200:
        config_id = response.json()["id"]
        print(f"   Success! Created config ID: {config_id}")
    else:
        print(f"   Failed: {response.text}")
        return

    # 2. Trigger a scrape (simulated or real)
    # Since triggering a real scrape might take time and depends on finding NEW results,
    # we can try to manually invoke the notification logic if we had a way, 
    # but for end-to-end testing, we should probably just verify the config exists 
    # and maybe try to hit the scrape endpoint if we know it will find something new.
    # Alternatively, we can unit test the 'send_notifications' function directly in a separate script.
    
    print("\n2. Verifying Config Exists...")
    response = requests.get(f"{BASE_URL}/api/notifications/config")
    configs = response.json()
    found = any(c["id"] == config_id for c in configs)
    if found:
        print("   Success! Config found in list.")
    else:
        print("   Failed! Config not found.")

    # 3. Clean up
    print("\n3. Deleting Configuration...")
    response = requests.delete(f"{BASE_URL}/api/notifications/config/{config_id}")
    if response.status_code == 200:
        print("   Success! Config deleted.")
    else:
        print(f"   Failed: {response.text}")

if __name__ == "__main__":
    test_notifications()
