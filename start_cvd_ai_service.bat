@echo off
rem Kept for compatibility. The launcher now lives in scripts\run-ai.bat, which
rem finds Python automatically and reads the API key from careconnect.env.
call "%~dp0scripts\run-ai.bat" %*
