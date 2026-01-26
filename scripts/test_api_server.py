import requests
import sys

try:
    print("Checking GET http://localhost:8010/health ...")
    resp = requests.get("http://localhost:8010/health", timeout=5)
    print(f"Status: {resp.status_code}")
    print(f"Content: {resp.text}")
except Exception as e:
    print(f"Health check failed: {e}")
    sys.exit(1)

# Now try to trigger a report (mocking what frontend does)
# We need a company ID. 5589 (Hanwha Aerospace)
print("Testing Report Creation API...")
try:
    payload = {
        "company_id": 5589,
        "template": "investment_memo_vc_v1"
    }
    # Need auth header? Frontend says 'Bearer dev-token'
    headers = {"Authorization": "Bearer dev-token"}
    resp = requests.post("http://localhost:8010/reports", json=payload, headers=headers, timeout=10)
    print(f"Create Report Status: {resp.status_code}")
    print(f"Create Report Response: {resp.text}")
except Exception as e:
    print(f"Create Report request failed: {e}")
