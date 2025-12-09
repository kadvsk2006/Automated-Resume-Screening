@echo off
echo Starting Resume Ranker AI...
echo Opening Browser...
timeout /t 3 >nul
start http://localhost:8000
python run.py
pause

