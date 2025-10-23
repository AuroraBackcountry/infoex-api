# Environment Variables for Render Deployment

## Required Environment Variables

Set these in your Render service's Environment settings:

### 1. **Claude API Key** (Required)
```
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
```

### 2. **Environment Selection** (Required)
```
ENVIRONMENT=staging
```
or
```
ENVIRONMENT=production
```

### 3. **Operation UUID** (Required - same for both environments)
```
OPERATION_UUID=your-aurora-operation-uuid
```

### 4. **InfoEx API Keys** (Required based on ENVIRONMENT)

#### For Staging:
```
STAGING_API_KEY=your-staging-api-key
```

#### For Production:
```
PRODUCTION_API_KEY=your-production-api-key
```

### 5. **CORS Origins** (Required)
```
CORS_ALLOWED_ORIGINS=["https://your-n8n-instance.com"]
```
Note: This should be a JSON array string

### 6. **Redis** (Your External Instance)
Since you're using your own Redis for shared context with n8n:
```
REDIS_URL=redis://username:password@your-redis-host.com:6379/0
```
Note: Do NOT add Render's Redis addon - use your existing Redis instance

### 7. **Redis Session Prefix** (Optional)
Only set this if n8n uses a prefix before session IDs:
```
REDIS_SESSION_PREFIX=session
```
- If n8n uses just "abc-123", don't set this variable
- If n8n uses "session:abc-123", set to "session"
- Default is no prefix (direct session ID)

## Optional Environment Variables

### Submission State
```
INFOEX_SUBMISSION_STATE=IN_REVIEW
```
- `IN_REVIEW` (default) - Draft mode, safe for testing
- `SUBMITTED` - Final submission, use for production

### Logging
```
LOG_LEVEL=INFO
```

### Session Management
```
SESSION_TTL_SECONDS=3600
MAX_CONVERSATION_LENGTH=50
```

### Claude Model Settings
```
CLAUDE_MODEL=claude-3-opus-20240229
CLAUDE_MAX_TOKENS=1024
CLAUDE_TEMPERATURE=0.3
```

## Render-Specific Notes

1. **PORT**: Render automatically sets this. The service will use it automatically.

2. **Redis**: If using Render's Redis addon:
   - It will automatically set `REDIS_URL`
   - No need to set individual Redis variables

3. **Build Command**:
   ```
   pip install -r requirements.txt
   ```

4. **Start Command**:
   ```
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

## Example Complete Setup for Staging

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxxxxxxxxxx
ENVIRONMENT=staging
OPERATION_UUID=uuid-1234-5678-aurora
STAGING_API_KEY=abcd1234-staging-key
REDIS_URL=redis://user:pass@my-redis.com:6379
CORS_ALLOWED_ORIGINS=["https://n8n.mydomain.com"]
LOG_LEVEL=INFO
```

## Verification

After deployment, check the health endpoint:
```
https://your-service.onrender.com/health
```

This should return:
```json
{
  "status": "healthy",
  "checks": {
    "redis": true,
    "claude": true,
    "infoex": true
  }
}
```
