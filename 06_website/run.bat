@echo off
cd /d "%~dp0"
"C:\Program Files\Python314\python.exe" -m uvicorn main:app --port 8000
pause
