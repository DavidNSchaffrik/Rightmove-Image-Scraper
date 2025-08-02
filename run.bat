@echo off
REM run_queue.bat: Processes links from a queue file and runs the Python script for each link.

REM Check if queue.txt exists
if not exist queue.txt (
    echo [ERROR] No queue.txt file found!
    pause
    exit /b 1
)

REM Loop through each line (URL) in queue.txt
for /f "usebackq delims=" %%a in ("queue.txt") do (
    echo [INFO] Processing URL: %%a
    python script.py "%%a"
    echo.
)

echo [INFO] All URLs processed.
pause
