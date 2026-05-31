# Run all components of Preventista Inteligente (backend, web panel, mobile app)
# ------------------------------------------------------------
# Usage:   .\run_all.ps1
#
# This script assumes you have:
#   • Python virtual environment in backend\venv
#   • Node/npm installed for the panel and mobile projects
#   • Expo CLI installed globally (npm i -g expo-cli) for the mobile app
# ------------------------------------------------------------

# Helper to start a process in a new PowerShell window
function Start-Component {
    param (
        [string]$Title,
        [string]$WorkingDir,
        [string]$Command
    )
    Write-Host "Starting $Title..."
    Start-Process powershell -ArgumentList "-NoLogo -NoProfile -WorkingDirectory `"$WorkingDir`" -Command `"$Command`"" -WindowStyle Normal
}

# 1️⃣ Backend (FastAPI)
$backendDir = Join-Path $PSScriptRoot "backend"
$activateCmd = "& `"$backendDir\venv\Scripts\Activate.ps1`"; uvicorn app.main:app --reload"
Start-Component -Title "Backend (FastAPI)" -WorkingDir $backendDir -Command $activateCmd

# 2️⃣ Web Panel (Vite + React)
$panelDir = Join-Path $PSScriptRoot "panel"
$panelCmd = "npm install; npm run dev"
Start-Component -Title "Web Panel" -WorkingDir $panelDir -Command $panelCmd

# 3️⃣ Mobile App (React Native / Expo)
$mobileDir = Join-Path $PSScriptRoot "mobile"
$mobileCmd = "npm install; npx expo start"
Start-Component -Title "Mobile App (Expo)" -WorkingDir $mobileDir -Command $mobileCmd

Write-Host "All components launched. Check the new windows for logs."
