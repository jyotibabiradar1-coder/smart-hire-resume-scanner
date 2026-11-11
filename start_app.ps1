# Launch script for SmartHire Platform
Set-Location -Path $PSScriptRoot

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "   Starting SmartHire - Talent Acquisition Platform" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# Detect Python version
$pyCmd = "python"
try {
    $ver = & py -3.13 --version 2>$null
    if ($LASTEXITCODE -eq 0) {
        $pyCmd = "py -3.13"
    }
} catch {}

Write-Host "Using Python Runtime: $pyCmd" -ForegroundColor Yellow

# Ensure database is configured
Write-Host "Initializing SmartHire database..." -ForegroundColor Gray
Invoke-Expression "$pyCmd fix_db.py" | Out-Null

# Open browser
Start-Process "http://localhost:8501"

# Run Streamlit
Write-Host "SmartHire running at http://localhost:8501" -ForegroundColor Green
Invoke-Expression "$pyCmd -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0"
