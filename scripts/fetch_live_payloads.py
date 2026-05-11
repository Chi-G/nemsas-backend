import requests
import json

# Load the previously saved token
with open("auth_token.json", "r") as f:
    auth_data = json.load(f)

TOKEN = auth_data["data"]["token"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/json"
}
BASE_URL = "https://emt-proxy-6arxm.ondigitalocean.app"

endpoints = {
    "incidents": "/api/v1/Incidents/get",
    "claims_ambulance": "/api/v1/Claims/getAllAmbulance",
    "claims_etc": "/api/v1/Claims/getAllETC",
    "run_sheets": "/api/v1/Runsheets/runSheetByManagers",
    "monitoring": "/api/v1/MonitoringAndEvaluation"
}

results = {}

for name, path in endpoints.items():
    url = BASE_URL + path
    print(f"Fetching {name} from {url}...")
    try:
        # Some endpoints might require pagination params, lets try default first.
        resp = requests.get(url, headers=HEADERS, timeout=10)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            # We only need a sample structure if it is a massive list
            if isinstance(data, dict) and "data" in data and isinstance(data["data"], list) and len(data["data"]) > 0:
                 print(f"Got {len(data['data'])} records. Storing sample...")
                 # Store just the first 1 record as fully representative structure
                 results[name] = data["data"][:1] 
            else:
                 results[name] = data
        else:
            print(f"Error Response: {resp.text[:200]}")
            results[name] = {"ERROR": resp.status_code, "MSG": resp.text[:500]}
    except Exception as e:
         print(f"Exception occurred: {e}")
         results[name] = {"EXCEPTION": str(e)}

with open("captured_payloads.json", "w") as f:
    json.dump(results, f, indent=2)

print("\nSUCCESS: Written captured payloads to captured_payloads.json")
