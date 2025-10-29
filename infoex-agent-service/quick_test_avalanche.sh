#!/bin/bash
# Quick test script to check if InfoEx API accepts arrays

# Load environment variables
source .env 2>/dev/null || true

# Use staging by default
BASE_URL="${STAGING_URL:-https://staging-can.infoex.ca/safe-server}"
API_KEY="${STAGING_API_KEY}"
OPERATION_UUID="${OPERATION_UUID}"
LOCATION_UUID="${TEST_LOCATION_UUID:-fe206d0d-c886-47c3-8ac6-b85d6b3c45c9}"

if [ -z "$API_KEY" ]; then
    echo "❌ Error: STAGING_API_KEY not set"
    echo "Please set it in .env or export it"
    exit 1
fi

echo "🏔️  InfoEx Avalanche Observation Array Test"
echo "🔧 Testing against: $BASE_URL"
echo ""

# Get today's date in MM/DD/YYYY format
TODAY=$(date +%m/%d/%Y)

# Test 1: Single observation
echo "🧪 TEST 1: Single Avalanche Observation"
echo "========================================"

SINGLE_PAYLOAD=$(cat <<EOF
{
  "obDate": "$TODAY",
  "obTime": "10:00",
  "num": "1",
  "trigger": "Sa",
  "character": "STORM_SLAB",
  "size": "2",
  "locationUUIDs": ["$LOCATION_UUID"],
  "operationUUID": "$OPERATION_UUID",
  "state": "IN_REVIEW",
  "comments": "Test single observation"
}
EOF
)

echo "Sending single observation..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  "$BASE_URL/observation/avalanche" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Operation: $OPERATION_UUID" \
  -d "$SINGLE_PAYLOAD")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "Response status: $HTTP_STATUS"
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Single observation: SUCCESS"
    echo "Response: $(echo $BODY | head -c 200)..."
else
    echo "❌ Single observation: FAILED"
    echo "Response: $(echo $BODY | head -c 300)..."
fi

echo ""

# Test 2: Array of observations
echo "🧪 TEST 2: Array of Avalanche Observations"
echo "=========================================="

ARRAY_PAYLOAD=$(cat <<EOF
[
  {
    "obDate": "$TODAY",
    "obTime": "09:00",
    "num": "1",
    "trigger": "Na",
    "character": "STORM_SLAB",
    "size": "2.5",
    "locationUUIDs": ["$LOCATION_UUID"],
    "operationUUID": "$OPERATION_UUID",
    "state": "IN_REVIEW",
    "comments": "Natural avalanche - first in array"
  },
  {
    "obDate": "$TODAY",
    "obTime": "11:00",
    "num": "1",
    "trigger": "Sa",
    "character": "WIND_SLAB",
    "size": "2",
    "locationUUIDs": ["$LOCATION_UUID"],
    "operationUUID": "$OPERATION_UUID",
    "state": "IN_REVIEW",
    "comments": "Skier triggered - second in array"
  }
]
EOF
)

echo "Sending array of 2 observations..."
RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" -X POST \
  "$BASE_URL/observation/avalanche" \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -H "Operation: $OPERATION_UUID" \
  -d "$ARRAY_PAYLOAD")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS:" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_STATUS:/d')

echo "Response status: $HTTP_STATUS"
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Array submission: SUCCESS"
    echo "Response: $(echo $BODY | head -c 200)..."
else
    echo "❌ Array submission: FAILED"
    echo "Response: $(echo $BODY | head -c 300)..."
fi

echo ""
echo "📊 SUMMARY"
echo "=========="
echo "Based on these tests, InfoEx API:"
if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ ACCEPTS arrays of avalanche observations"
    echo "→ Recommendation: Store array in single JSONB field"
else
    echo "❌ REQUIRES individual avalanche submissions"
    echo "→ Recommendation: Either multiple rows OR array->multiple API calls"
fi
