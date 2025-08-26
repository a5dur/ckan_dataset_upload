# config.py
import os
from dotenv import load_dotenv
load_dotenv()  

CKAN_URL    = "https://data.dathere.com"
DATASET_ID  = "counties_social"

# Change this when switching tables (e.g., 'education', 'veteran', ...)
RESOURCE_NAME = "householdlanguage"

EXISTING_FILE = f"{RESOURCE_NAME}_existing.csv"
NEW_FILE      = f"{RESOURCE_NAME}.csv"
MERGED_FILE   = f"{RESOURCE_NAME}_merged.csv"

CKAN_API_KEY = os.getenv("CKAN_API_KEY", "")


