#!/bin/bash
# Script to run tests with Firestore emulator

echo "Starting Firestore emulator for tests..."

# Set environment variables
export FRESH_USE_FIRESTORE=true
export FIRESTORE_EMULATOR_HOST=localhost:8080
export GOOGLE_CLOUD_PROJECT=agency-test
export GOOGLE_APPLICATION_CREDENTIALS="gothic-point-390410-firebase-adminsdk-fbsvc-505b6b6075.json"

# Start the emulator in the background
firebase emulators:start --only firestore --project agency-test &
EMULATOR_PID=$!

# Wait for emulator to start
echo "Waiting for Firestore emulator to start..."
for i in {1..30}; do
    if curl -s http://localhost:8080 > /dev/null; then
        echo "Firestore emulator started successfully"
        break
    fi
    if [ $i -eq 30 ]; then
        echo "Failed to start Firestore emulator"
        kill $EMULATOR_PID 2>/dev/null
        exit 1
    fi
    sleep 1
done

# Run tests
echo "Running tests with Firestore integration..."
python -m pytest tests/ -v --tb=short

# Capture test exit code
TEST_EXIT_CODE=$?

# Kill the emulator
echo "Stopping Firestore emulator..."
kill $EMULATOR_PID 2>/dev/null
wait $EMULATOR_PID 2>/dev/null

# Exit with the test exit code
exit $TEST_EXIT_CODE