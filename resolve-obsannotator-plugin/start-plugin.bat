@echo off
echo Starting ObsAnnotator Plugin...
echo.

echo Starting Python server...
start "ObsAnnotator Python Server" cmd /k "cd python-server && python server.py"

echo Waiting for server to start...
timeout /t 3 /nobreak > nul

echo Starting Electron app...
start "ObsAnnotator Plugin" cmd /k "npm start"

echo.
echo Plugin started! Check the windows that opened.
echo Close both windows when done.
pause
