#!/usr/bin/env bash
set -euo pipefail

# Root folder (where this script + python files + datasets/ live)
ROOT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
DATASETS_DIR="$ROOT_DIR/datasets"
BACKUP_DIR="$ROOT_DIR/backup"

# Create backup folder if not exists
mkdir -p "$BACKUP_DIR"

echo "=== Running CKAN Upload Pipeline ==="
echo "Datasets folder: $DATASETS_DIR"
echo "Backup folder:   $BACKUP_DIR"
echo

# Loop through each dataset folder
for dataset_path in "$DATASETS_DIR"/*/; do
    dataset=$(basename "$dataset_path")
    echo ">>> Processing dataset: $dataset"

    # Create dataset-specific backup folder
    mkdir -p "$BACKUP_DIR/$dataset"

    # Loop through each CSV (resource) in this dataset
    for csvfile in "$dataset_path"/*.csv; do
        resource=$(basename "$csvfile" .csv)
        echo "   → Resource: $resource"

        # Update config.py (overwrite DATASET_ID and RESOURCE_NAME)
        tmp_config=$(mktemp)
        awk -v ds="$dataset" -v rn="$resource" '
            /^DATASET_ID/ {$0="DATASET_ID  = \"" ds "\""}
            /^RESOURCE_NAME/ {$0="RESOURCE_NAME = \"" rn "\""}
            {print}
        ' "$ROOT_DIR/config.py" > "$tmp_config"
        mv "$tmp_config" "$ROOT_DIR/config.py"

        # Step 1: Download existing resource (backup)
        python3 "$ROOT_DIR/1_download.py" || true  # allow fail if resource doesn't exist
        if [ -f "${resource}_existing.csv" ]; then
            mv "${resource}_existing.csv" "$BACKUP_DIR/$dataset/${resource}_existing.csv"
            echo "      ✓ Backup saved to backup/$dataset/${resource}_existing.csv"
        else
            echo "      ⚠ No existing resource found (new resource will be created)"
        fi

        # Step 2: Merge new + existing
        cp "$csvfile" "$ROOT_DIR/${resource}.csv"   # copy new file to expected name
        python3 "$ROOT_DIR/2_merge.py"

        # Step 3: Delete old resource (optional, but included for safety)
        python3 "$ROOT_DIR/3_delete.py" || true

        # Step 4: Upload merged resource
        python3 "$ROOT_DIR/4_upload.py"

        # Step 5: Create/refresh DataTables view
        python3 "$ROOT_DIR/5_createView.py"

        # Clean up working files
        rm -f "$ROOT_DIR/${resource}.csv" "$ROOT_DIR/${resource}_merged.csv"
    done
    echo
done

echo "=== Pipeline Complete! ==="
