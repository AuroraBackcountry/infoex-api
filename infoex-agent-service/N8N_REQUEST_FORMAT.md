# Expected Request Body from n8n

## POST /api/process-report

This is the exact format n8n should send to the Claude microservice:

```json
{
  "session_id": "28f2849a-d476-4186-a41e-cf116db481c8",
  "message": "Submit avalanche observation - size 3 at north aspect",
  "request_values": {
    "operation_id": "your-aurora-operation-uuid",
    "location_uuids": ["location-uuid-1", "location-uuid-2"],
    "zone_name": "Your Zone Name",
    "date": "MM/DD/YYYY",
    "user_name": "Guide Name",
    "user_id": "guide-user-uuid"
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | The conversation session ID from n8n |
| `message` | string | Yes | The current message/instruction for Claude |
| `request_values` | object | Yes | Request-specific data for this submission |
| → `operation_id` | string | Yes | Aurora Backcountry operation UUID |
| → `location_uuids` | array | Yes | Array of location UUIDs |
| → `zone_name` | string | Yes | Zone name (e.g., "Your Zone Name") |
| → `date` | string | Yes | Report date in MM/DD/YYYY format |
| → `user_name` | string | No | Name of the user submitting |
| → `user_id` | string | No | UUID of the user |

## Example n8n HTTP Request Node Configuration

```javascript
{
  "method": "POST",
  "url": "https://your-service.onrender.com/api/process-report",
  "sendHeaders": true,
  "headerParameters": {
    "parameters": [
      {
        "name": "Content-Type",
        "value": "application/json"
      }
    ]
  },
  "sendBody": true,
  "bodyType": "json",
  "jsonBody": {
    "session_id": "={{ $json.session_id }}",
    "message": "={{ $json.message }}",
    "fixed_values": {
      "operation_id": "={{ $env.OPERATION_UUID }}",
      "location_uuids": "={{ $json.location_uuids }}",
      "zone_name": "={{ $json.zone_name }}",
      "date": "={{ $now.format('MM/dd/yyyy') }}",
      "user_name": "={{ $json.user_name }}",
      "user_id": "={{ $json.user_id }}"
    }
  }
}
```

## Notes

1. **Session ID**: This should match what's in your Redis database
2. **User Info**: Claude will include the user name in submissions
3. **No Redis Lookup Needed**: By passing all data in the request, Claude doesn't need to guess Redis structure
4. **Date Format**: Must be MM/DD/YYYY

## Single-Step Process (Default)

With `auto_submit: true` (default), the service validates AND submits in one call:

### Request:
```json
{
  "session_id": "your-session-id-here",
  "message": "Submit avalanche observation - size 3 at north aspect",
  "auto_submit": true,  // Optional, defaults to true
  "request_values": {
    "operation_id": "your-aurora-operation-uuid",
    "location_uuids": ["location-uuid-1"],
    "zone_name": "Your Zone Name",
    "date": "MM/DD/YYYY",
    "user_name": "Guide Name",
    "user_id": "guide-user-uuid"
  }
}
```

### Response (with auto-submission):
```json
{
  "response": "Payload validated and ready for avalanche observation submission\n\nAuto-submission results:\navalanche_observation: Submitted (UUID: 123e4567-e89b-12d3-a456)"
}
```

## Validation-Only Mode

To validate without submitting, set `auto_submit: false`:

```json
{
  "session_id": "test-123",
  "message": "Check this avalanche observation...",
  "auto_submit": false,
  "request_values": {...}
}
```

## n8n Workflow (Simplified!)

Just ONE HTTP Request node:
1. **HTTP Request**: Call `/api/process-report` with message
2. **Parse Response**: Extract UUID from submission results
3. **Done!**
