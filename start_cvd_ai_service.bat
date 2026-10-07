@echo off

echo ========================================================
echo Starting CareConnect CVD AI Diagnostic Microservice...
echo Python Environment: C:\Users\vinay\cvd-env
echo Port: 5000
echo ========================================================

"C:\Users\vinay\cvd-env\Scripts\python.exe" "%~dp0cvd-ai-service\api_server.py"

pause
