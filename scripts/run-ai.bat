@echo off
rem Start the CareConnect AI microservice (FastAPI on http://127.0.0.1:5000).
rem Settings (HMS_AI_API_KEY) come from the environment or from
rem %USERPROFILE%\.careconnect\careconnect.env  (see scripts\setup-config.bat).
setlocal
set "SERVICE=%~dp0..\cvd-ai-service"

rem Pick a Python: project venv, then the original cvd-env, then PATH.
set "PY="
if exist "%SERVICE%\.venv\Scripts\python.exe" set "PY=%SERVICE%\.venv\Scripts\python.exe"
if not defined PY if exist "%USERPROFILE%\cvd-env\Scripts\python.exe" set "PY=%USERPROFILE%\cvd-env\Scripts\python.exe"
if not defined PY set "PY=python"

echo ========================================================
echo  CareConnect AI microservice
echo  Python: %PY%
echo  URL:    http://127.0.0.1:5000   (Ctrl+C to stop)
echo ========================================================

cd /d "%SERVICE%"
"%PY%" api_server.py
endlocal
