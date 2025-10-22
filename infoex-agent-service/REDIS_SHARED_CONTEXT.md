# Shared Redis Configuration for n8n + Claude Integration

## Benefits of Using Your Own Redis

By using your own Redis instance (instead of Render's addon), you get:

1. **Shared Conversation History**
   - n8n stores conversation in Redis
   - Claude microservice reads the same history
   - Full context from the beginning of the chat

2. **Seamless Handoff**
   - User talks to n8n agent
   - n8n decides to call Claude
   - Claude sees entire conversation, not just current message

3. **Unified Session Management**
   - Same session IDs across both services
   - No need to duplicate conversation data
   - Single source of truth

## Configuration for External Redis

### In Your `.env` File:
```env
# Your external Redis instance
REDIS_URL=redis://username:password@your-redis-host.com:6379/0

# Or if using Redis Cloud/AWS ElastiCache with SSL:
REDIS_URL=rediss://username:password@your-redis-host.com:6380/0
```

### For Render Deployment:

Set only this environment variable:
```
REDIS_URL=redis://username:password@your-redis-host.com:6379/0
```

Do NOT add Render's Redis addon.

## How It Works

### 1. n8n Stores Conversation
```json
{
  "session_id": "abc-123",
  "messages": [
    {"role": "user", "content": "I saw an avalanche today"},
    {"role": "assistant", "content": "Tell me more about it"},
    {"role": "user", "content": "Size 3 on north aspect"}
  ]
}
```

### 2. n8n Calls Claude Service
```json
{
  "session_id": "abc-123",  // Same session!
  "message": "Submit this as avalanche observation",
  "fixed_values": {...}
}
```

### 3. Claude Reads Full History
Claude retrieves the entire conversation from Redis:
- Sees "Size 3 on north aspect" from earlier
- Understands context without re-asking
- Builds complete payload immediately

## Session Key Format

Make sure both n8n and Claude use the same key format:
- n8n might use: `session:abc-123`
- Claude uses: `infoex:session:abc-123`

You may need to adjust the `_get_session_key()` method in `session.py`:

```python
def _get_session_key(self, session_id: str) -> str:
    # Match n8n's key format
    return f"session:{session_id}"  # or whatever n8n uses
```

## Testing Shared Context

1. Start conversation in n8n
2. Check Redis for session data:
   ```bash
   redis-cli
   > KEYS session:*
   > GET session:abc-123
   ```

3. Call Claude service with same session_id
4. Verify Claude sees full history

## Security Notes

- Use SSL/TLS for Redis connections (rediss://)
- Set strong passwords
- Consider using Redis ACLs for fine-grained permissions
- Ensure both services are in same VPC if possible

## Example n8n → Claude Flow

```mermaid
graph LR
    A[User] -->|"I saw avalanche"| B[n8n Agent]
    B -->|Stores in Redis| C[(Redis)]
    B -->|"Tell me more"| A
    A -->|"Size 3, north"| B
    B -->|Updates Redis| C
    B -->|Calls with session_id| D[Claude Service]
    D -->|Reads full history| C
    D -->|Builds complete payload| E[InfoEx API]
```

This shared Redis approach makes Claude much more effective because it has the complete conversational context!
