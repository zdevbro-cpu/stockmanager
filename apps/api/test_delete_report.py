import requests

# Test listing reports first
resp = requests.get("http://localhost:8000/reports")
reports = resp.json()
print(f"Total reports: {len(reports)}")

if reports:
    last_id = reports[0]['id']
    print(f"Attempting to delete report ID: {last_id}")
    del_resp = requests.delete(f"http://localhost:8000/reports/{last_id}")
    print(f"Delete Status: {del_resp.status_code}")
    print(f"Delete Response: {del_resp.text}")
else:
    print("No reports to delete.")
