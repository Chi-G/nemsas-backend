import requests
import json

BASE_URL = "https://emt-proxy-6arxm.ondigitalocean.app/api/v1"

def try_login():
    url = f"{BASE_URL}/Account/login"
    payload = {"email": "ahmednu@datharm.com", "password": "@Password01"}
    print(f"Trying real login POST {url}...")
    resp = requests.post(url, json=payload)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("SUCCESS!")
        print(json.dumps(resp.json(), indent=2))
        return resp.json()
    else:
        print(resp.text)
    return None

token_info = try_login()
if token_info:
    with open("auth_token.json", "w") as f:
        json.dump(token_info, f)
