# InfoEx Claude Agent Microservice Architecture

## Overview

This microservice acts as an intelligent middleware between n8n workflows and the InfoEx API. It uses Claude (Anthropic) to translate casual conversation into properly formatted InfoEx API payloads, handling validation and incremental data collection.

## Key Features

- **Conversational Interface**: Natural language processing for InfoEx data collection
- **Session Management**: Redis-backed conversation history compatible with n8n
- **Intelligent Validation**: Validates against live InfoEx constants
- **Progressive Payload Building**: Constructs payloads incrementally as information is provided
- **Plain Text Responses**: Designed for agent-to-agent communication

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        n8n Workflow                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Fixed Values:                                           │   │
│  │  - operation_id: "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c" │   │
│  │  - location_uuids: ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"]│
│  │  - zone_name: "Whistler Blackcomb"                      │   │
│  │  - date: "10/06/2025"                                   │   │
│  │  - guide_names: ["John Smith", "Jane Doe"]              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│         HTTP POST /api/process-report                           │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              InfoEx Claude Agent Microservice                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    API Layer (FastAPI)                    │   │
│  │  - /api/process-report (main conversation endpoint)      │   │
│  │  - /api/submit-to-infoex (final submission trigger)      │   │
│  │  - /api/session/{id}/status (check session status)       │   │
│  │  - /api/session/{id}/clear (reset conversation)          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Claude Agent Service                     │   │
│  │  - Direct Anthropic API integration                      │   │
│  │  - System prompt with InfoEx expertise                   │   │
│  │  - Access to InfoEx constants for validation             │   │
│  │  - AURORA_IDEAL payload construction                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Redis Session Store                       │   │
│  │  - Conversation history (TTL: 1 hour)                    │   │
│  │  - Partial payload construction state                    │   │
│  │  - Session metadata and progress tracking                │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                InfoEx API Client                          │   │
│  │  - Individual endpoint submissions                       │   │
│  │  - Environment-based configuration (staging/prod)        │   │
│  │  - Error handling and retry logic                        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## API Endpoints

### POST /api/process-report
Main conversation endpoint for processing messages and building payloads.

**Request:**
```json
{
    "session_id": "unique-session-id",
    "message": "I observed a size 2 storm slab avalanche today",
    "fixed_values": {
        "operation_id": "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c",
        "location_uuids": ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"],
        "zone_name": "Whistler Blackcomb",
        "date": "10/06/2025",
        "guide_names": ["John Smith", "Jane Doe"]
    }
}
```

**Response (Plain Text):**
```
I need a few more details about the avalanche. What aspect was it on, and what was the trigger?
```

### POST /api/submit-to-infoex
Triggers submission of completed payloads to InfoEx API.

**Request:**
```json
{
    "session_id": "unique-session-id",
    "submission_types": ["avalanche_observation", "field_summary", "hazard_assessment"]
}
```

**Response:**
```
Successfully submitted 3 observations to InfoEx:
- Avalanche observation: UUID 123e4567-e89b-12d3-a456-426614174000
- Field summary: UUID 234e5678-e89b-12d3-a456-426614174001
- Hazard assessment: UUID 345e6789-e89b-12d3-a456-426614174002
```

### GET /api/session/{session_id}/status
Check the current status of a session.

**Response:**
```json
{
    "session_id": "unique-session-id",
    "status": "active",
    "payloads_ready": ["avalanche_observation", "field_summary"],
    "missing_data": {
        "hazard_assessment": ["hazard ratings for each elevation band"]
    },
    "last_updated": "2025-10-06T14:30:00Z"
}
```

### DELETE /api/session/{session_id}/clear
Clear a session and start fresh.

**Response:**
```
Session cleared successfully.
```

## Implementation Details

### Project Structure
```
infoex-agent-service/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app
│   ├── config.py            # Environment configuration
│   ├── models.py            # Pydantic models
│   ├── agent/
│   │   ├── __init__.py
│   │   ├── claude_agent.py  # Claude integration
│   │   ├── prompts.py       # System prompts
│   │   └── constants.py     # InfoEx constants loader
│   ├── services/
│   │   ├── __init__.py
│   │   ├── session.py       # Redis session management
│   │   ├── payload.py       # Payload construction
│   │   └── infoex.py        # InfoEx API client
│   └── api/
│       ├── __init__.py
│       └── routes.py        # API endpoints
├── data/
│   ├── infoex_constants.json
│   └── aurora_templates/    # AURORA_IDEAL payloads
├── tests/
│   ├── __init__.py
│   ├── test_agent.py
│   ├── test_session.py
│   └── test_infoex.py
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── README.md
```

### Claude Agent Configuration

```python
SYSTEM_PROMPT = """You are an InfoEx API submission specialist for Aurora Backcountry.
Your role is to help build accurate payloads for InfoEx API submissions.

You have access to:
- InfoEx constants for validation (loaded from data/infoex_constants.json)
- AURORA_IDEAL payload templates for each observation type
- Date format: MM/DD/YYYY (month/day/year)
- Valid zones and operation information from fixed_values

When collecting information:
1. Ask for missing required fields based on AURORA_IDEAL templates
2. Validate against InfoEx constants
3. Use OGRS terminology translations
4. Build payloads incrementally
5. Track what's been collected in the session

Available observation types you can prepare:
- field_summary (daily operational report)
- avalanche_summary (avalanche activity overview)
- avalanche_observation (individual avalanche details)
- hazard_assessment (hazard ratings and problems)
- snowpack_summary (general snowpack conditions)
- snowProfile_observation (detailed snow profiles)
- terrain_observation (terrain and ATES ratings)
- pwl_persistent_weak_layer (seasonal tracking)

Aurora-specific constraints:
- No explosives or control work
- Focus on backcountry guiding operations
- Use AURORA_IDEAL payload structure

Respond conversationally to gather all needed information.
When you have enough data, confirm what will be submitted."""
```

### Session Management

Sessions are stored in Redis with the following structure:

```python
{
    "session_id": "unique-session-id",
    "created_at": "2025-10-06T14:00:00Z",
    "last_updated": "2025-10-06T14:30:00Z",
    "fixed_values": {
        "operation_id": "...",
        "location_uuids": [...],
        "zone_name": "...",
        "date": "10/06/2025",
        "guide_names": [...]
    },
    "conversation_history": [
        {"role": "user", "content": "I observed a size 2 storm slab..."},
        {"role": "assistant", "content": "I need a few more details..."}
    ],
    "payloads": {
        "avalanche_observation": {
            "obDate": "10/06/2025",
            "character": "STORM_SLAB",
            "sizeMin": 2,
            "sizeMax": 2,
            "_status": "incomplete",
            "_missing": ["trigger", "aspectFrom", "aspectTo"]
        }
    }
}
```

### Environment Configuration

```env
# Anthropic API
ANTHROPIC_API_KEY=sk-ant-api03-...

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=optional_password

# InfoEx API Configuration
INFOEX_ENVIRONMENT=staging  # or production
INFOEX_STAGING_URL=https://staging-can.infoex.ca/safe-server
INFOEX_PRODUCTION_URL=https://can.infoex.ca/safe-server
INFOEX_API_KEY=your_api_key_here
INFOEX_OPERATION_UUID=your_operation_uuid_here

# Service Configuration
SERVICE_PORT=8000
SERVICE_HOST=0.0.0.0
LOG_LEVEL=INFO
SESSION_TTL_SECONDS=3600  # 1 hour
```

## Conversation Flow Examples

### Example 1: Avalanche Observation

**User**: "We had some avalanche activity today"

**Claude**: "I'll help you document the avalanche activity. Can you tell me:
- How many avalanches did you observe?
- What type were they (storm slab, wind slab, etc.)?
- What size were they?"

**User**: "We saw 2 storm slabs, both size 2"

**Claude**: "Got it - 2 storm slab avalanches, both size 2. For each avalanche, I need to know:
- What aspect were they on?
- What triggered them?
- What elevation range?"

**User**: "Both on north aspects between 1800-2000m, skier triggered"

**Claude**: "Perfect! I have enough information for the avalanche observations. Would you also like to submit:
- A field summary for the day?
- A hazard assessment?
- Any other observations?"

### Example 2: Field Summary

**User**: "Let me give you our field summary"

**Claude**: "I'll help you create a field summary. Please provide:
- Start and end times of your day
- Temperature (high/low)
- Wind conditions
- Snow depths (HS and HN24)
- General conditions and comments"

**User**: "Started at 8:30, ended at 15:45. Temps ranged from -5 to -2. Light winds from the west, HS was 180cm with 15cm new. Great skiing conditions above 1500m."

**Claude**: "Excellent field summary! I have all the required information. The report will include:
- Time: 08:30 - 15:45
- Temps: -5°C to -2°C
- Wind: L from W
- Snow: HS 180cm, HN24 15cm
- Comments: Great skiing conditions above 1500m

Would you like to add any other observations?"

## Error Handling

### API Errors
```python
try:
    response = await infoex_client.submit(payload)
except InfoExAPIError as e:
    if e.status_code == 400:
        return f"Validation error: {e.detail}"
    elif e.status_code == 401:
        return "Authentication error - please check API credentials"
    else:
        return f"API error: {e.message}"
```

### Session Errors
```python
try:
    session = await session_manager.get(session_id)
except SessionNotFoundError:
    return "Session expired or not found. Please start a new conversation."
except RedisConnectionError:
    return "Temporary service issue. Please try again."
```

## Integration with n8n

### n8n HTTP Request Node Configuration

```json
{
  "method": "POST",
  "url": "https://your-service.com/api/process-report",
  "authentication": "none",
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
  "bodyParameters": {
    "parameters": [
      {
        "name": "session_id",
        "value": "={{ $node['Generate_Session_ID'].json.session_id }}"
      },
      {
        "name": "message",
        "value": "={{ $node['User_Message'].json.message }}"
      },
      {
        "name": "fixed_values",
        "value": {
          "operation_id": "{{ $env.INFOEX_OPERATION_ID }}",
          "location_uuids": "={{ $node['Zone_Mapping'].json.location_uuids }}",
          "zone_name": "={{ $node['Zone_Selection'].json.zone }}",
          "date": "={{ $now.format('MM/dd/yyyy') }}",
          "guide_names": "={{ $node['Guide_Names'].json.guides }}"
        }
      }
    ]
  }
}
```

### n8n Workflow Pattern

1. **Initialize Session** → Generate unique session ID
2. **Collect Fixed Values** → Zone mapping, guide names, date
3. **Conversation Loop** → Send messages to microservice
4. **Check Status** → Verify payloads are ready
5. **Trigger Submission** → Call submit endpoint
6. **Handle Response** → Log success/errors

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  infoex-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - REDIS_HOST=redis
      - REDIS_PORT=6379
    depends_on:
      - redis
    volumes:
      - ./data:/app/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Render.com Deployment

1. Create new Web Service
2. Connect GitHub repository
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables from `.env.example`
6. Add Redis instance and connect

## Monitoring and Logging

### Health Check Endpoint

```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "redis": await check_redis_connection(),
        "anthropic": await check_anthropic_connection(),
        "infoex": await check_infoex_connection(),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Structured Logging

```python
import structlog

logger = structlog.get_logger()

logger.info("processing_request", 
    session_id=session_id,
    message_length=len(message),
    fixed_values=fixed_values.keys()
)
```

## Security Considerations

1. **No API Keys in Requests**: All credentials stored in environment variables
2. **Session Isolation**: Each session has its own Redis namespace
3. **Input Validation**: All inputs validated with Pydantic models
4. **Rate Limiting**: Optional rate limiting per session
5. **HTTPS Only**: Enforce TLS in production

## Future Enhancements

1. **Batch Processing**: Submit multiple reports in one session
2. **Template Management**: UI for managing AURORA_IDEAL templates
3. **Webhook Support**: Async submission with callbacks
4. **Multi-Language**: Support for French observations
5. **Voice Input**: Transcription support for field recordings

---

*This microservice bridges the gap between conversational data collection and structured API requirements, making InfoEx submissions more accessible and error-free.*
