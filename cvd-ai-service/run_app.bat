@echo off
cd /d "%~dp0"
echo ========================================================
echo  Launching Retinal Fundus Multi-Task Assessment App
echo ========================================================
echo.

REM Check for active or local virtual environments
if exist "..\cvd-env\Scripts\python.exe" (
    echo Using python from ..\cvd-env\Scripts\python.exe
    "..\cvd-env\Scripts\python.exe" app.py
    goto :end
)

if exist "venv\Scripts\python.exe" (
    echo Using python from venv\Scripts\python.exe
    "venv\Scripts\python.exe" app.py
    goto :end
)

REM Fallback to system python
echo Using system python...
python app.py

:end
pause
