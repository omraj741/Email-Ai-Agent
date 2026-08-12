@echo off
setlocal
cd /d "%~dp0"
set TASK_NAME=Personal Email AI Agent
set RUNNER=%~dp0run_agent.bat
schtasks /Create /TN "%TASK_NAME% 08 AM" /TR "\"%RUNNER%\"" /SC DAILY /ST 08:00 /F
schtasks /Create /TN "%TASK_NAME% 02 PM" /TR "\"%RUNNER%\"" /SC DAILY /ST 14:00 /F
schtasks /Create /TN "%TASK_NAME% 08 PM" /TR "\"%RUNNER%\"" /SC DAILY /ST 20:00 /F
echo Created daily Task Scheduler jobs for 08:00, 14:00, and 20:00.
endlocal
