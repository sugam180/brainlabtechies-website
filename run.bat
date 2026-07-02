@echo off
REM ---- Brainlab Techies launcher (Windows) ----
cd /d "%~dp0"
echo Installing dependencies (first run only)...
python -m pip install -r requirements.txt --quiet
echo Starting Brainlab Techies...
python app.py
pause
