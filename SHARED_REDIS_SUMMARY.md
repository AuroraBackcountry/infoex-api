# Shared Redis Configuration Summary

## What We've Configured

Your Claude microservice is now set up to use your external Redis instance, which provides a **huge advantage**: Claude can see the entire conversation history from n8n!

### Changes Made:

1. **Configurable Redis Session Prefix**
   - Added `REDIS_SESSION_PREFIX` environment variable
   - Default: `"infoex:session"` → keys like `"infoex:session:abc-123"`
   - Can change to match n8n's format (e.g., just `"session"`)

2. **External Redis Support**
   - Use your own Redis URL: `REDIS_URL=redis://your-instance:6379`
   - Don't use Render's Redis addon
   - Full SSL/TLS support with `rediss://` URLs

3. **Updated Documentation**
   - `env.example` - Shows external Redis configuration
   - `RENDER_ENV_VARS.md` - Notes about NOT using Render Redis
   - `SHARED_REDIS_ARCHITECTURE.md` - Visual flow diagram
   - `test_shared_redis.py` - Test script to verify setup

## How It Works

### Without Shared Redis (❌ Old Way):
```
User → n8n: "I saw a size 3 avalanche"
n8n → User: "Tell me more"
User → n8n: "North aspect at 2100m"
n8n → Claude: "Submit avalanche observation"
Claude → n8n: "What size? What aspect? What elevation?"  ← Redundant!
```

### With Shared Redis (✅ New Way):
```
User → n8n: "I saw a size 3 avalanche"
n8n → User: "Tell me more"
User → n8n: "North aspect at 2100m"
n8n → Claude: "Submit avalanche observation"
Claude: *reads full history from Redis*
Claude → InfoEx: *submits complete payload*  ← No questions needed!
```

## Configuration Steps

### 1. In Your `.env`:
```env
# Your external Redis
REDIS_URL=redis://username:password@your-redis-host.com:6379/0

# Match n8n's session key format
REDIS_SESSION_PREFIX=session  # or whatever n8n uses
```

### 2. In Render:
Set these environment variables:
- `REDIS_URL` - Your Redis connection string
- `REDIS_SESSION_PREFIX` - To match n8n's format
- Do NOT add Render's Redis addon

### 3. Test It:
Run the test script to verify shared context:
```bash
cd infoex-agent-service
python3 test_shared_redis.py
```

## Benefits

1. **No Information Loss** - Claude sees everything the user told n8n
2. **Faster Processing** - No redundant questions
3. **Better UX** - User doesn't repeat information
4. **Single Source of Truth** - One Redis, one conversation

## Next Steps

1. Check what session key format n8n uses in Redis
2. Set `REDIS_SESSION_PREFIX` to match
3. Deploy and test the shared context

This setup makes your Claude agent much more intelligent and context-aware!
