@echo off
rem Double-click launcher for Windows; runs run_app.ps1 without changing the execution policy.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"
pause
