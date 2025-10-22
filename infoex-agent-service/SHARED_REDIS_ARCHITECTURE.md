# Shared Redis Architecture

## How n8n and Claude Share Context

```
┌─────────────────────────────────────────────────────────────┐
│                      User Conversation                       │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                        n8n Agent                             │
│                                                              │
│  1. "I saw a size 3 avalanche"                             │
│  2. "It was on north aspect at 2100m"                      │
│  3. "Natural trigger, storm slab"                          │
│                                                              │
│  Stores full conversation in Redis:                         │
│  Key: session:abc-123                                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
                     Decides to submit
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Claude Microservice                       │
│                                                              │
│  Receives: "Submit avalanche observation"                   │
│  Session ID: abc-123                                        │
│                                                              │
│  Reads from Redis: session:abc-123                          │
│  Sees ENTIRE conversation history!                          │
│                                                              │
│  Builds complete payload without asking questions           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                       InfoEx API                             │
│                                                              │
│  Receives properly formatted avalanche observation          │
└─────────────────────────────────────────────────────────────┘
```

## Key Benefits

### 1. **No Context Loss**
- User provides details to n8n over multiple messages
- Claude sees everything when called
- No need to repeat information

### 2. **Intelligent Processing**
- Claude understands "submit avalanche observation"
- Looks back at conversation for size, aspect, trigger
- Builds complete payload immediately

### 3. **Single Source of Truth**
- One Redis instance
- One session ID
- One conversation history

## Configuration Example

### n8n Configuration
```javascript
// n8n stores sessions with key format:
redis.set("session:abc-123", conversationHistory)
```

### Claude Service Configuration
```env
# Match n8n's key format
REDIS_SESSION_PREFIX=session

# Use same Redis instance
REDIS_URL=redis://your-redis-instance.com:6379
```

### Result
Both services read/write to the same session keys!

## Example Session Data

What's stored in Redis:
```json
{
  "session_id": "abc-123",
  "conversation_history": [
    {
      "role": "user",
      "content": "I observed a size 3 avalanche today"
    },
    {
      "role": "assistant", 
      "content": "Can you tell me more about the avalanche? What aspect was it on?"
    },
    {
      "role": "user",
      "content": "North aspect at 2100m, it was a natural release, storm slab"
    },
    {
      "role": "assistant",
      "content": "Got it. Any other avalanches observed or just this one?"
    },
    {
      "role": "user",
      "content": "Just this one. Can you submit it to InfoEx?"
    }
  ],
  "metadata": {
    "location": "Glacier Bowl",
    "date": "10/22/2025",
    "guide": "John Doe"
  }
}
```

When Claude reads this, it has everything needed to create:
- Size: 3
- Aspect: ["N"]
- Elevation: 2100
- Trigger: "Na" (natural)
- Character: "SS" (storm slab)

No additional questions needed!
