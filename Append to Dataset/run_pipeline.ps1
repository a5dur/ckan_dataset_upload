# run_pipeline.ps1
# PowerShell automation for CKAN upload pipeline
# Loops through datasets/<dataset>/<resource>.csv

$RootDir   = Split-Path -Parent $MyInvocation.MyCommand.Path
$Datasets  = Join-Path $RootDir "datasets"
$BackupDir = Join-Path $RootDir "backup"

Write-Host "=== Running CKAN Upload Pipeline ==="
Write-Host "Datasets folder: $Datasets"
Write-Host "Backup folder:   $BackupDir"
Write-Host ""

# Create backup folder if missing
if (!(Test-Path $BackupDir)) {
    New-Item -ItemType Directory -Path $BackupDir | Out-Null
}

# Loop through dataset folders
Get-ChildItem -Path $Datasets -Directory | ForEach-Object {
    $dataset = $_.Name
    Write-Host ">>> Processing dataset: $dataset"

    # Ensure dataset backup folder exists
    $DatasetBackup = Join-Path $BackupDir $dataset
    if (!(Test-Path $DatasetBackup)) {
        New-Item -ItemType Directory -Path $DatasetBackup | Out-Null
    }

    # Loop through each CSV resource in dataset
    Get-ChildItem -Path $_.FullName -Filter *.csv | ForEach-Object {
        $resource = $_.BaseName
        Write-Host "   → Resource: $resource"

        # Update config.py (replace DATASET_ID and RESOURCE_NAME)
        $ConfigPath = Join-Path $RootDir "config.py"
        (Get-Content $ConfigPath) |
            ForEach-Object {
                if ($_ -match "^DATASET_ID") { "DATASET_ID  = `"$dataset`"" }
                elseif ($_ -match "^RESOURCE_NAME") { "RESOURCE_NAME = `"$resource`"" }
                else { $_ }
            } | Set-Content $ConfigPath

        # Step 1: Download existing resource (backup)
        try {
            python "$RootDir\1_download.py"
        } catch { Write-Host "      WARNING: Download failed (maybe resource doesn't exist)" }

        $ExistingFile = Join-Path $RootDir ($resource + "_existing.csv")
        if (Test-Path $ExistingFile) {
            Move-Item $ExistingFile (Join-Path $DatasetBackup ($resource + "_existing.csv")) -Force
            Write-Host "      SUCCESS: Backup saved: backup\$dataset\$resource`_existing.csv"
        } else {
            Write-Host "      WARNING: No existing resource found (will create new)"
        }

        # Step 2: Merge
        Copy-Item $_.FullName (Join-Path $RootDir ($resource + ".csv")) -Force
        python "$RootDir\2_merge.py"

        # Step 3: Delete old resource
        # try {
        #     python "$RootDir\3_delete.py"
        # } catch { Write-Host "      WARNING: Delete failed (maybe resource didn't exist)" }

        # Step 4: Upload merged resource
        python "$RootDir\4_upload.py"

        # Step 5: Create/refresh DataTables view
        python "$RootDir\5_createView.py"

        # Cleanup
        Remove-Item (Join-Path $RootDir ($resource + ".csv")) -ErrorAction SilentlyContinue
        Remove-Item (Join-Path $RootDir ($resource + "_merged.csv")) -ErrorAction SilentlyContinue
    } # <- This closing brace was missing

    Write-Host ""
} # <- This closing brace was missing

Write-Host "=== Pipeline Complete! ==="
