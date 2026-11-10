@echo off
rem Build, deploy and start the CareConnect web application. Arguments are passed through.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-web.ps1" %*
