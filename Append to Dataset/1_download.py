#!/usr/bin/env python3
import sys, requests, os
from config import CKAN_URL, DATASET_ID, RESOURCE_NAME, EXISTING_FILE

def main():
    output_file = sys.argv[1] if len(sys.argv) > 1 else EXISTING_FILE
    package_show_url = f"{CKAN_URL}/api/3/action/package_show"

    r = requests.get(package_show_url, params={"id": DATASET_ID}, timeout=30)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        print("✗ API error:", data.get("error"))
        sys.exit(1)

    res_id, res_url = None, None
    for res in data["result"]["resources"]:
        if res.get("name", "").startswith(RESOURCE_NAME):
            res_id, res_url = res["id"], res["url"]
            break

    if not res_url:
        print(f"✗ Resource {RESOURCE_NAME} not found in dataset {DATASET_ID}")
        sys.exit(1)

    print(f"✓ Downloading resource {RESOURCE_NAME} → {output_file}")
    resp = requests.get(res_url, timeout=120)
    resp.raise_for_status()
    with open(output_file, "wb") as f:
        f.write(resp.content)

if __name__ == "__main__":
    main()
