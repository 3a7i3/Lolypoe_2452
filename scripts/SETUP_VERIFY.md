Setup And Verify Automation

Quick start
- From repository root:
  - powershell -ExecutionPolicy Bypass -File scripts/setup_and_verify_all.ps1
- Or double-click:
  - scripts/run_setup_verify.bat

What it does
1. Installs root requirements.
2. Installs crypto_quant_v16 requirements.
3. Installs legacy compatibility requirements for Python 3.14.
4. Runs global verification checks.

Logging
- Default log directory:
  - logs/setup
- Default behavior:
  - Creates a timestamped transcript log.
  - Keeps only the latest 20 logs.

Useful options
- Disable logging:
  - powershell -ExecutionPolicy Bypass -File scripts/setup_and_verify_all.ps1 -NoLog
- Custom log directory:
  - powershell -ExecutionPolicy Bypass -File scripts/setup_and_verify_all.ps1 -LogDir C:/Users/WINDOWS/crypto_ai_terminal/logs/custom
- Keep only latest 5 logs:
  - powershell -ExecutionPolicy Bypass -File scripts/setup_and_verify_all.ps1 -KeepLatestLogs 5

Notes
- This workspace currently runs on Python 3.14.
- Legacy strict pins are preserved in requirements-legacy files; default requirements now point to py314-compatible sets.
