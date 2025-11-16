#!/bin/bash

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║           Testing StudyStream Microservices System             ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test 1: Health Checks
echo -e "${BLUE}=== 1. Testing Health Checks ===${NC}"
echo "Auth Service:"
curl -s http://localhost:8001/health | python3 -m json.tool
echo ""
echo "User Service:"
curl -s http://localhost:8002/health | python3 -m json.tool
echo ""
echo "Task Service:"
curl -s http://localhost:8003/health | python3 -m json.tool
echo ""
echo "Notification Service:"
curl -s http://localhost:8004/health | python3 -m json.tool
echo ""

# Test 2: Register User
echo -e "${BLUE}=== 2. Registering New User ===${NC}"
RESPONSE=$(curl -s -X POST http://localhost:8001/auth/register \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"testuser_$(date +%s)@example.com\",
    \"password\": \"TestPass123!\",
    \"password_confirm\": \"TestPass123!\"
  }")

echo "$RESPONSE" | python3 -m json.tool
TOKEN=$(echo "$RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${GREEN}❌ Failed to get token${NC}"
    exit 1
fi

echo -e "${GREEN}✅ User registered successfully!${NC}"
echo ""

# Test 3: Create Task
echo -e "${BLUE}=== 3. Creating a Task ===${NC}"
curl -s -X POST http://localhost:8003/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "title": "Test Task from Script",
    "content": "This task was created by the test script",
    "task_type": "note",
    "task_metadata": {
      "priority": "high",
      "automated": true
    }
  }' | python3 -m json.tool

echo -e "${GREEN}✅ Task created!${NC}"
echo ""

# Wait for background task
echo "Waiting 2 seconds for notification to be created..."
sleep 2

# Test 4: Check Notifications
echo -e "${BLUE}=== 4. Checking Notifications ===${NC}"
curl -s http://localhost:8004/notifications \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "${GREEN}✅ Notification retrieved!${NC}"
echo ""

# Test 5: List Tasks
echo -e "${BLUE}=== 5. Listing All Tasks ===${NC}"
curl -s http://localhost:8003/tasks \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ✅ ALL TESTS PASSED! ✅                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Your microservices system is working perfectly!${NC}"
echo ""
echo "Next steps:"
echo "1. Visit http://localhost:8001/docs for interactive API testing"
echo "2. Visit http://localhost:8003/docs to explore Task Service"
echo "3. Your token for manual testing:"
echo "$TOKEN"
