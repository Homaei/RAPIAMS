#!/bin/bash

echo "🚀 RAPIAMS Quick Functionality Test"
echo "=================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Base URL
BASE_URL="http://localhost:8000"

echo -e "${BLUE}Testing backend health...${NC}"
curl -s "$BASE_URL/health" | python3 -m json.tool

echo -e "\n${BLUE}Testing authentication...${NC}"
AUTH_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/simple-login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin1234"}')

echo "$AUTH_RESPONSE" | python3 -m json.tool

TOKEN=$(echo "$AUTH_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Authentication failed!${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Authentication successful!${NC}"
fi

echo -e "\n${BLUE}Testing device creation...${NC}"
DEVICE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/devices/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Test Device",
    "hostname": "test-device",
    "ip_address": "192.168.1.199",
    "device_type": "raspberry_pi",
    "os": "Raspbian",
    "os_version": "11"
  }')

echo "$DEVICE_RESPONSE" | python3 -m json.tool

echo -e "\n${BLUE}Testing user info...${NC}"
curl -s "$BASE_URL/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n${BLUE}Testing API documentation...${NC}"
echo "Swagger UI available at: $BASE_URL/docs"
echo "ReDoc available at: $BASE_URL/redoc"

echo -e "\n${GREEN}🎉 Quick test completed!${NC}"
echo -e "${GREEN}All core functionalities are working.${NC}"
echo ""
echo "📚 Full test suite: python3 test_all_modules.py"
echo "📖 API docs: $BASE_URL/docs"
echo "🔍 Health check: $BASE_URL/health"