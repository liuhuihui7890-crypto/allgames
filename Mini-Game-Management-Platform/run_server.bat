@echo off
echo Starting Mini-Game Platform on port 8099...
cd /d "%~dp0"
uvicorn main:app --reload --host 0.0.0.0 --port 8099
pause
