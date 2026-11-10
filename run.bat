@echo off
rem ===========================================================================
rem  CareConnect HMS - run everything with one command.
rem  Builds the web app, deploys it to Tomcat and starts Tomcat; the web app
rem  starts the AI service itself. Ctrl+C stops everything.
rem  Options: run.bat -NoStart   run.bat -TomcatHome "C:\path\to\tomcat"
rem ===========================================================================
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\run-web.ps1" %*
