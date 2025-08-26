#!/usr/bin/env python3
import sys, pandas as pd
from config import EXISTING_FILE, NEW_FILE, MERGED_FILE

def main():
    existing_path = sys.argv[1] if len(sys.argv) > 1 else EXISTING_FILE
    new_path      = sys.argv[2] if len(sys.argv) > 2 else NEW_FILE
    merged_path   = sys.argv[3] if len(sys.argv) > 3 else MERGED_FILE

    df_exist = pd.read_csv(existing_path) if os.path.exists(existing_path) else pd.DataFrame()
    df_new   = pd.read_csv(new_path)

    if df_exist.empty:
        df = df_new
    else:
        df = pd.concat([df_new, df_exist], ignore_index=True)
        if "geoid" in df.columns and "year" in df.columns:
            before = len(df)
            df = df.drop_duplicates(subset=["geoid", "year"], keep="first")
            print(f"· Deduped {before - len(df)} rows on ['geoid','year']")

    df.to_csv(merged_path, index=False)
    print(f"✓ Merged saved → {merged_path}")

if __name__ == "__main__":
    import os
    main()
