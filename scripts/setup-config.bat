@echo off
rem One-time: create %USERPROFILE%\.careconnect\careconnect.env (DB credentials + AI key).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-config.ps1" %*
