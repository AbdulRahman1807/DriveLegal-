from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api():
    print("--- API LAYER TEST ---")
    
    print("1. Testing /api/v1/health...")
    response = client.get("/api/v1/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
    
    if response.status_code == 200:
        print("\nAPI HEALTH STATUS: SUCCESS")
    else:
        print("\nAPI HEALTH STATUS: FAILED")

if __name__ == "__main__":
    test_api()
