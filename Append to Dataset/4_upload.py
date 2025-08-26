#!/usr/bin/env python3
import os, sys, requests
from config import CKAN_URL, CKAN_API_KEY, DATASET_ID, RESOURCE_NAME, MERGED_FILE

def norm(x: str) -> str:
    # normalize for comparisons: lowercase, underscores/spaces equivalent
    return (x or "").strip().lower().replace("_", " ")

def log_fail(prefix, resp: requests.Response):
    try:
        print(f"✗ {prefix}: HTTP {resp.status_code} {resp.reason}")
        print(resp.text[:2000])
    except Exception as e:
        print(f"✗ {prefix}: {e}")

def test_ckan_connection() -> bool:
    url = f"{CKAN_URL}/api/3/action/site_read"
    try:
        r = requests.get(url, timeout=20)
        if r.status_code == 200:
            try:
                if r.json().get("success"):
                    print("✓ CKAN reachable")
                    return True
            except Exception:
                pass
        log_fail("Connection test failed", r)
        return False
    except Exception as e:
        print(f"✗ Connection error: {e}")
        return False

def get_existing_resource(dataset_id: str, resource_name: str):
    url = f"{CKAN_URL}/api/3/action/package_show"
    hdr = {"Authorization": CKAN_API_KEY} if CKAN_API_KEY else {}
    r = requests.get(url, params={"id": dataset_id}, headers=hdr, timeout=30)
    if r.status_code != 200 or not r.json().get("success"):
        log_fail("package_show", r)
        return None
    target = norm(resource_name)
    # exact normalized match
    for res in r.json()["result"].get("resources", []):
        if norm(res.get("name", "")) == target:
            return res
    # fallback: prefix match
    for res in r.json()["result"].get("resources", []):
        if norm(res.get("name", "")).startswith(target):
            return res
    return None

def update_resource(csv_path: str, res_id: str) -> bool:
    url = f"{CKAN_URL}/api/3/action/resource_update"
    hdr = {"Authorization": CKAN_API_KEY}
    with open(csv_path, "rb") as f:
        r = requests.post(
            url,
            data={"id": res_id},
            headers=hdr,
            files={"upload": (os.path.basename(csv_path), f, "text/csv")},
            timeout=180
        )
    if r.status_code == 200 and r.json().get("success"):
        print(f"✓ Resource updated: {res_id}")
        return True
    log_fail("resource_update", r)
    return False

def create_resource(csv_path: str, dataset_id: str, resource_name: str) -> bool:
    url = f"{CKAN_URL}/api/3/action/resource_create"
    hdr = {"Authorization": CKAN_API_KEY}
    with open(csv_path, "rb") as f:
        r = requests.post(
            url,
            data={"package_id": dataset_id, "name": resource_name, "format": "CSV"},
            headers=hdr,
            files={"upload": (os.path.basename(csv_path), f, "text/csv")},
            timeout=180
        )
    if r.status_code == 200 and r.json().get("success"):
        print(f"✓ Resource created: {r.json()['result']['id']}")
        return True
    log_fail("resource_create", r)
    return False

def main():
    csv_file = sys.argv[1] if len(sys.argv) > 1 else MERGED_FILE
    print("=== CKAN CSV UPLOADER ===")
    print(f"Dataset: {DATASET_ID}")
    print(f"Resource: {RESOURCE_NAME}")
    print(f"File: {csv_file}\n")

    if not os.path.exists(csv_file):
        print(f"✗ File not found: {csv_file}")
        return False

    ok = test_ckan_connection()
    if not ok:
        print("⚠ Ping test failed; continuing anyway…")

    if not CKAN_API_KEY:
        print("✗ CKAN_API_KEY not set in environment.")
        return False

    existing = get_existing_resource(DATASET_ID, RESOURCE_NAME)
    if existing:
        return update_resource(csv_file, existing["id"])
    else:
        return create_resource(csv_file, DATASET_ID, RESOURCE_NAME)

if __name__ == "__main__":
    sys.exit(0 if main() else 1)
