#!/bin/bash
# Kill any existing server on port 5174
lsof -ti :5174 2>/dev/null | xargs kill 2>/dev/null
sleep 1

# Start vite
cd /Users/taot/Desktop/Smart-healthcar-system/frontend/patient_uniapp
npx vite --port 5174 --host 127.0.0.1 &
VITE_PID=$!
sleep 3

echo "Dev server running on http://127.0.0.1:5174"
echo "VITE_PID=$VITE_PID"
