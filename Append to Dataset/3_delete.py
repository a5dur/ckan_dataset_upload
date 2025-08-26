#!/usr/bin/env python3
import sys, requests
from config import CKAN_URL, CKAN_API_KEY, DATASET_ID, RESOURCE_NAME

def get_res_id(session):
    r = session.get(f"{CKAN_URL}/api/3/action/package_show", params={"id": DATASET_ID}, timeout=30)
    r.raise_for_status()
    js = r.json()
    if not js.get("success"): return None
    for res in js["result"]["resources"]:
        if res.get("name","").startswith(RESOURCE_NAME):
            return res["id"]
    return None

def main():
    if not CKAN_API_KEY:
        print("✗ CKAN_API_KEY missing")
        sys.exit(1)

    s = requests.Session()
    s.headers.update({"Authorization": CKAN_API_KEY})
    res_id = get_res_id(s)
    if not res_id:
        print("✗ Resource not found")
        sys.exit(1)

    r = s.post(f"{CKAN_URL}/api/3/action/resource_delete", json={"id": res_id}, timeout=30)
    if r.status_code == 200 and r.json().get("success"):
        print(f"✓ Deleted resource {res_id}")
    else:
        print("✗ Delete failed:", r.text)
        sys.exit(1)

if __name__ == "__main__":
    main()
