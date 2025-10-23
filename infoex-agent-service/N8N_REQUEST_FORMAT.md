# Expected Request Body from n8n

## POST /api/process-report

This is the exact format n8n should send to the Claude microservice:

```json
{
  "session_id": "28f2849a-d476-4186-a41e-cf116db481c8",
  "message": "Submit avalanche observation - size 3 at north aspect",
  "fixed_values": {
    "operation_id": "your-aurora-operation-uuid",
    "location_uuids": ["location-uuid-1", "location-uuid-2"],
    "zone_name": "Whistler Blackcomb",
    "date": "10/22/2025",
    "user_name": "Ben Johns",
    "user_id": "93576f96-fe5f-4e97-91e4-bd22560da051"
  }
}
```

## Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `session_id` | string | Yes | The conversation session ID from n8n |
| `message` | string | Yes | The current message/instruction for Claude |
| `fixed_values` | object | Yes | Context data that Claude needs |
| → `operation_id` | string | Yes | Aurora Backcountry operation UUID |
| → `location_uuids` | array | Yes | Array of location UUIDs |
| → `zone_name` | string | Yes | Zone name (e.g., "Whistler Blackcomb") |
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
4. **Date Format**: Must be MM/DD/YYYY (e.g., "10/22/2025")

## Two-Step Process

### Step 1: Process Report Response
Claude validates and responds:
```json
{
  "response": "Payload validated and ready for avalanche observation submission"
}
```

### Step 2: Submit to InfoEx
After Claude validates, call the submission endpoint:
```json
POST /api/submit-to-infoex
{
  "session_id": "28f2849a-d476-4186-a41e-cf116db481c8",
  "submission_types": ["avalanche_observation"]
}
```

### Submission Response
```json
{
  "success": true,
  "message": "Processed 1 submissions. All successful! Details: avalanche_observation: Submitted (UUID: 123e4567)",
  "submissions": [
    {
      "observation_type": "avalanche_observation",
      "success": true,
      "result": {"uuid": "123e4567-e89b-12d3-a456-426614174000"}
    }
  ]
}
```

## n8n Workflow

1. **HTTP Request 1**: Call `/api/process-report` with message
2. **If Node**: Check if response contains "ready for submission"
3. **HTTP Request 2**: If ready, call `/api/submit-to-infoex`
4. **Set Node**: Extract UUID from submission response
