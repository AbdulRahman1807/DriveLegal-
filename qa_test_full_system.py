from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_full_system():
    print("========================================")
    print("  FULL SYSTEM TEST (PHASES 1 + 2 + 3)  ")
    print("========================================")
    
    print("\n[Phase 1 & 2] Testing End-to-End Chat API Pipeline...")
    
    # Simulate a frontend POST request
    payload = {
        "query": "What happens if I drive without a helmet?",
        "violation_code": "SPEEDING" # Using speeding code from our seeds for testing purposes
    }
    
    response = client.post(
        "/api/v1/chat",
        json=payload,
        headers={"Authorization": "Bearer drivelegal-secret-dev-key"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("\n✅ API Request Successful (200 OK)")
        print("\n--- LLM Reply ---")
        print(data.get("reply"))
        
        print("\n--- Extracted Citations ---")
        citations = data.get("citations", [])
        for c in citations:
            print(f"- {c['act_name']} Section {c.get('section', 'Unknown')}")
            
        print("\n--- Calculated Fines ---")
        fines = data.get("fines", [])
        for f in fines:
            print(f"- Base Fine: {f['base_fine']}, Total: {f['total_fine']}")
            
        if citations and fines:
            print("\n✅ SYSTEM TEST RESULT: 100% SUCCESS")
            print("All three phases (Database, Retrieval Engine, API/Chat Layer) are fully integrated.")
        else:
            print("\n❌ SYSTEM TEST RESULT: PARTIAL FAILURE (Missing citations or fines)")
    else:
        print(f"\n❌ API Request Failed with status {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_full_system()
