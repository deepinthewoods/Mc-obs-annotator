#!/bin/bash
echo "Starting ObsAnnotator Plugin..."
echo ""

echo "Starting Python server..."
cd python-server
python3 server.py &
PYTHON_PID=$!
cd ..

echo "Waiting for server to start..."
sleep 3

echo "Starting Electron app..."
npm start &
ELECTRON_PID=$!

echo ""
echo "Plugin started!"
echo "Python server PID: $PYTHON_PID"
echo "Electron app PID: $ELECTRON_PID"
echo ""
echo "Press Ctrl+C to stop both processes"

# Wait for Ctrl+C
trap "kill $PYTHON_PID $ELECTRON_PID; exit" INT
wait
