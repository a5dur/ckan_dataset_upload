#!/usr/bin/env python3
import requests, sys
from config import CKAN_URL, CKAN_API_KEY, DATASET_ID, RESOURCE_NAME

def norm(x: str) -> str:
    return (x or "").strip().lower().replace("_", " ")

def get_res_id(s, dataset_id, resource_name):
    r = s.get(f"{CKAN_URL}/api/3/action/package_show", params={"id": dataset_id}, timeout=30)
    r.raise_for_status()
    js = r.json()
    if not js.get("success"):
        return None
    target = norm(resource_name)
    # exact normalized match first
    for res in js["result"].get("resources", []):
        if norm(res.get("name", "")) == target:
            return res["id"]
    # fallback: prefix match after normalization
    for res in js["result"].get("resources", []):
        if norm(res.get("name", "")).startswith(target):
            return res["id"]
    return None

def main():
    if not CKAN_API_KEY:
        print("✗ Missing CKAN_API_KEY")
        sys.exit(1)

    s = requests.Session()
    s.headers.update({"Authorization": CKAN_API_KEY})

    res_id = get_res_id(s, DATASET_ID, RESOURCE_NAME)
    if not res_id:
        print("✗ Resource not found")
        sys.exit(1)

    # Create DataTables view
    view_url = f"{CKAN_URL}/api/3/action/resource_view_create"
    data = {
        "resource_id": res_id,
        "title": f"{RESOURCE_NAME} Data Table",
        "view_type": "datatables_view"
    }
    r = s.post(view_url, json=data, timeout=60)
    if r.status_code == 200 and r.json().get("success"):
        print(f"✓ View created for {RESOURCE_NAME}")
    else:
        print(f"✗ View creation failed: HTTP {r.status_code}")
        print(r.text)
        sys.exit(1)

if __name__ == "__main__":
    main()

