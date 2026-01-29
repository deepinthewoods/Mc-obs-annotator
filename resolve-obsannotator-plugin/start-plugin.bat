@echo off
echo Starting ObsAnnotator Plugin...
echo.

echo Starting Python server...
start "ObsAnnotator Python Server" /b cmd /c "cd python-server && venv\Scripts\activate && python server.py"
set PYTHON_PID=

echo Waiting for server to start...
timeout /t 3 /nobreak > nul

echo Starting Electron app...
echo (Close this window or press Ctrl+C to stop all processes)
echo.

call npm start

echo.
echo Electron app closed. Shutting down Python server...

REM Kill any remaining python server processes started from this directory
taskkill /f /fi "WINDOWTITLE eq ObsAnnotator Python Server" >nul 2>&1

echo All processes stopped.
