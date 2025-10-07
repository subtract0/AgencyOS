#!/bin/bash
# Test Trinity HTTP Server locally

echo "🧪 Testing Trinity HTTP Server..."
echo ""

# Test 1: Health Check
echo "1️⃣ Health Check (GET /)"
curl -s http://localhost:8765/ | python3 -m json.tool
echo ""

# Test 2: Status Check
echo "2️⃣ Status Check (GET /status)"
curl -s http://localhost:8765/status | python3 -m json.tool
echo ""

# Test 3: Audit Request (mock)
echo "3️⃣ Audit Request (POST /audit)"
echo "   Using Agency repo as test..."
curl -s -X POST http://localhost:8765/audit \
  -H "Content-Type: application/json" \
  -d '{
    "repo": "subtract0/Agency",
    "pr": 1,
    "sha": "abc123",
    "branch": "main"
  }' | python3 -m json.tool | head -50

echo ""
echo "✅ Tests complete!"
echo ""
echo "Next steps:"
echo "1. Start server: python scripts/trinity_http_server.py"
echo "2. Expose via ngrok: ngrok http 8765"
echo "3. Update GitHub Action webhook URL"
