# Single Endpoint - Process and Submit in One Call

## Complete Submission (Default)

```bash
curl -X POST https://infoex-api.onrender.com/api/process-report \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-auto-submit",
    "message": "Submit avalanche observation - size 3 storm slab at north aspect 2100m, natural trigger",
    "fixed_values": {
      "operation_id": "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c",
      "location_uuids": ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"],
      "zone_name": "Whistler Blackcomb",
      "date": "10/22/2025",
      "user_name": "Ben Johns",
      "user_id": "93576f96-fe5f-4e97-91e4-bd22560da051"
    }
  }'
```

**Expected Response:**
```json
{
  "response": "Payload validated and ready for avalanche observation submission\n\nAuto-submission results:\navalanche_observation: Submitted (UUID: 123e4567-e89b-12d3-a456-426614174000)"
}
```

## Validation Only (No Submission)

```bash
curl -X POST https://infoex-api.onrender.com/api/process-report \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-validate-only",
    "message": "Check this avalanche observation - size 3 storm slab",
    "auto_submit": false,
    "fixed_values": {
      "operation_id": "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c",
      "location_uuids": ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"],
      "zone_name": "Whistler Blackcomb",
      "date": "10/22/2025",
      "user_name": "Ben Johns",
      "user_id": "93576f96-fe5f-4e97-91e4-bd22560da051"
    }
  }'
```

**Expected Response:**
```json
{
  "response": "Payload validated and ready for avalanche observation submission"
}
```

## Key Points

1. **`auto_submit` defaults to `true`** - You don't need to include it for automatic submission
2. **One call does everything** - Validates AND submits
3. **UUID in response** - The InfoEx UUID is included in the response text
4. **Set `auto_submit: false`** - Only if you want to validate without submitting

## For n8n

Just use ONE HTTP Request node with `auto_submit: true` (or omit it) and parse the UUID from the response!
