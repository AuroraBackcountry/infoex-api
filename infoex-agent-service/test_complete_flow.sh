#!/bin/bash

# Test Complete InfoEx Submission Flow

echo "1. Processing report with Claude..."
PROCESS_RESPONSE=$(curl -s -X POST https://infoex-api.onrender.com/api/process-report \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-flow-123",
    "message": "Submit avalanche observation - size 3 storm slab at north aspect 2100m, natural trigger",
    "fixed_values": {
      "operation_id": "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c",
      "location_uuids": ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"],
      "zone_name": "Whistler Blackcomb",
      "date": "10/22/2025",
      "user_name": "Ben Johns",
      "user_id": "93576f96-fe5f-4e97-91e4-bd22560da051"
    }
  }')

echo "Claude Response:"
echo "$PROCESS_RESPONSE" | jq .

echo -e "\n2. Checking session status..."
STATUS_RESPONSE=$(curl -s https://infoex-api.onrender.com/api/session/test-flow-123/status)
echo "$STATUS_RESPONSE" | jq .

echo -e "\n3. Submitting to InfoEx..."
SUBMIT_RESPONSE=$(curl -s -X POST https://infoex-api.onrender.com/api/submit-to-infoex \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-flow-123",
    "submission_types": ["avalanche_observation"]
  }')

echo "Submission Response:"
echo "$SUBMIT_RESPONSE" | jq .
