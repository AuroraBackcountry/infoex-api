# Redis Session Management

## Overview

The Aurora InfoEx system uses Redis for lightweight session state management during report creation. Each component maintains its own session data independently.

## Session Structure

### n8n Dialogue Agent Sessions

**Key Format**: `session-{uuid}`

**Contents**:
```json
{
  "session_id": "abc-123",
  "user_id": "user-uuid",
  "created_at": "2025-10-28T10:00:00Z",
  "current_capsule": "field_summary",
  "completed_capsules": ["initial_data_collection"],
  "dialogue_state": {
    "awaiting_response": true,
    "last_question": "field_summary"
  }
}
```

**TTL**: 24 hours (configurable)

### Claude Microservice Sessions

The Claude microservice maintains its own error handling context for API retries:

**Key Format**: `claude-retry-{session_id}-{capsule_type}`

**Contents**:
```json
{
  "attempts": 2,
  "last_error": "Missing required field: tempHigh",
  "modifications": {
    "tempHigh": "Inferred from narrative: -2"
  },
  "original_payload": {...},
  "current_payload": {...}
}
```

**TTL**: 1 hour (only needed during active submission)

## Data Flow

```
1. User starts report → n8n creates session in Redis
2. Responses stored → Postgres (persistent) + Redis (temporary state)
3. Submission triggered → Claude reads from Postgres (not Redis)
4. API errors → Claude creates retry context in Redis
5. Success → Claude cleans up retry context
```

## Key Principles

1. **No Shared Context**: Each service maintains its own Redis namespace
2. **Postgres as Source**: All report data stored in Postgres
3. **Redis for State**: Only temporary state and retry logic
4. **Simple Keys**: No complex prefixing schemes

## Implementation Details

### n8n Session Management
```javascript
// Create session
await redis.set(`session-${sessionId}`, JSON.stringify({
  session_id: sessionId,
  user_id: userId,
  created_at: new Date().toISOString(),
  current_capsule: 'initial_data_collection'
}), 'EX', 86400); // 24 hour TTL

// Update session
const session = JSON.parse(await redis.get(`session-${sessionId}`));
session.current_capsule = 'field_summary';
await redis.set(`session-${sessionId}`, JSON.stringify(session), 'EX', 86400);
```

### Claude Retry Management
```python
# Store retry context
retry_key = f"claude-retry-{session_id}-{capsule_type}"
redis.setex(retry_key, 3600, json.dumps({
    "attempts": 1,
    "last_error": str(error),
    "original_payload": payload,
    "current_payload": payload
}))

# Retrieve for retry
retry_data = redis.get(retry_key)
if retry_data:
    context = json.loads(retry_data)
    # Modify payload based on error
    # Increment attempts
    # Retry submission
```

## Benefits of This Approach

1. **Clear Separation**: No confusion about shared data
2. **Reliable Source**: Postgres holds all report data
3. **Simple Debugging**: Each service's Redis data is independent
4. **Flexible Scaling**: Services can scale independently

## What This Replaces

This approach replaces the previous "shared Redis context" concept where:
- ❌ n8n and Claude tried to share session data
- ❌ Complex key prefixing schemes
- ❌ Confusion about data ownership

Now:
- ✅ Each service owns its Redis namespace
- ✅ Postgres is the single source of truth
- ✅ Redis only for temporary state

## Error Handling Strategy

When InfoEx returns an error, Claude:

1. **Parses Error**: Extract field-specific issues
2. **Creates Context**: Store in Redis with error details
3. **Modifies Payload**: Attempt to fix based on error
4. **Retries**: Up to 3 attempts with modifications
5. **Reports**: Return detailed status to caller

Example retry context:
```json
{
  "attempts": 2,
  "errors": [
    {
      "field": "windSpeed",
      "error": "Invalid enum value",
      "attempted_fix": "Converted 'moderate' to 'M'"
    }
  ],
  "success": false
}
```

---

*This simplified Redis approach ensures clean separation of concerns while maintaining the ability to handle complex retry scenarios.*
