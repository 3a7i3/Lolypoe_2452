$ErrorActionPreference = 'Continue'

Write-Host "[INFO] Stopping V30 suite processes..."

Get-CimInstance Win32_Process |
    Where-Object {
        ($_.Name -match '^python(\.exe)?$') -and (
            $_.CommandLine -match 'quant_dashboard_v26\.py' -or
            $_.CommandLine -match 'binance_alert_app\.py' -or
            $_.CommandLine -match 'launch_v30_full\.py'
        )
    } |
    ForEach-Object {
        Write-Host "[INFO] Stopping PID=$($_.ProcessId) :: $($_.CommandLine)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Write-Host "[OK] Stop command completed."
