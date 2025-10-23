# Redis Session Key Configuration

## Current Setup

Since your n8n workflow uses just the session ID as the Redis key (no prefix), the Claude service is now configured to match this format.

## Configuration

In your `.env` file:

```env
# For no prefix (matches your n8n setup)
REDIS_SESSION_PREFIX=

# OR explicitly set to empty
# REDIS_SESSION_PREFIX=""
```

## How It Works

### Your n8n Workflow:
- Stores sessions with key: `abc-123-def-456`
- No prefix before the session ID

### Claude Service:
- With `REDIS_SESSION_PREFIX=` (empty)
- Uses key: `abc-123-def-456` (matches n8n exactly!)

### Example Flow:

1. **n8n stores conversation**:
   ```
   Redis Key: "550e8400-e29b-41d4-a716-446655440000"
   Value: {
     "messages": [...],
     "context": {...}
   }
   ```

2. **Claude reads same conversation**:
   ```python
   session_id = "550e8400-e29b-41d4-a716-446655440000"
   key = session_id  # No prefix added
   data = redis.get(key)  # Finds n8n's data!
   ```

## Other Options

If your Redis key format changes:

```env
# Just session ID (your current setup)
REDIS_SESSION_PREFIX=

# With "session:" prefix
REDIS_SESSION_PREFIX=session

# With "infoex:session:" prefix
REDIS_SESSION_PREFIX=infoex:session

# With custom prefix
REDIS_SESSION_PREFIX=aurora:chat
```

## Testing

To verify the configuration:

1. Check what keys n8n creates:
   ```bash
   redis-cli KEYS "*"
   ```

2. If you see keys like:
   - `abc-123-def-456` → Use `REDIS_SESSION_PREFIX=`
   - `session:abc-123` → Use `REDIS_SESSION_PREFIX=session`
   - `chat:abc-123` → Use `REDIS_SESSION_PREFIX=chat`

The Claude service will now correctly find and use the conversation history stored by n8n!
