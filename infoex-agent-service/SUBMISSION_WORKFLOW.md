# InfoEx Submission Workflow

## Current Two-Step Process

The service currently requires TWO API calls:

### Step 1: Process with Claude
```bash
curl -X POST https://infoex-api.onrender.com/api/process-report \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "message": "Submit avalanche observation - size 3 storm slab at north aspect 2100m",
    "inherited_values": {...}
  }'
```

**Response**: Claude validates and says "Payload validated and ready for avalanche observation submission"

### Step 2: Check What's Ready
```bash
curl https://infoex-api.onrender.com/api/session/test-123/status
```

**Response**: Shows which payloads are ready:
```json
{
  "payloads_ready": ["avalanche_observation"],
  "missing_data": {}
}
```

### Step 3: Submit to InfoEx
```bash
curl -X POST https://infoex-api.onrender.com/api/submit-to-infoex \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-123",
    "submission_types": ["avalanche_observation"]
  }'
```

**Response**: Actual submission results with UUIDs

## Why Two Steps?

1. **Safety**: Allows review before submission
2. **Flexibility**: Can prepare multiple observations before submitting
3. **Error Handling**: Can fix issues before attempting submission

## For n8n Integration

Your n8n workflow should:
1. Call `/api/process-report` with the message
2. Parse Claude's response for "ready for submission"
3. If ready, call `/api/submit-to-infoex`
4. Handle the submission response

## Submission Trigger

Submissions are triggered manually after validation:
- All submissions use `state: "IN_REVIEW"` by default
- This keeps reports in draft mode for review in InfoEx UI
- Future enhancement: Allow `state: "SUBMITTED"` for final submissions
