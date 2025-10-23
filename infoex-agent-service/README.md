# InfoEx Claude Agent Microservice

An intelligent middleware service that uses Claude (Anthropic) to convert conversational language into properly formatted InfoEx API payloads for Aurora Backcountry operations.

## Features

- 🤖 **Conversational Interface**: Natural language processing with Claude for data collection
- 📝 **Smart Payload Construction**: Builds InfoEx-compliant payloads incrementally
- 🔄 **Shared Context**: Uses same Redis as n8n for full conversation history
- ✅ **Real-time Validation**: Validates against live InfoEx constants
- 🚀 **Individual Endpoint Submission**: Reliable submission to InfoEx APIs
- 🔗 **n8n Integration**: Designed as a tool for n8n workflows
- 🧠 **Context-Aware**: Claude sees entire conversation from n8n, not just current message

## Quick Start

### Using Docker Compose (Recommended)

1. Clone the repository and navigate to the service directory:
```bash
cd infoex-agent-service
```

2. Copy the environment example file:
```bash
cp env.example .env
```

3. Edit `.env` with your credentials:
```env
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
ENVIRONMENT=staging
STAGING_API_KEY=your-staging-api-key
STAGING_OPERATION_UUID=your-staging-operation-uuid
# Or for production:
# ENVIRONMENT=production
# PRODUCTION_API_KEY=your-production-api-key
# PRODUCTION_OPERATION_UUID=your-production-operation-uuid
```

4. Start the services:
```bash
docker-compose up
```

The service will be available at `http://localhost:8000`

### Manual Installation

1. Install Python 3.11+

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Start Redis:
```bash
docker run -d -p 6379:6379 redis:7-alpine
```

5. Run the service:
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Process Report Message
```
POST /api/process-report
```

Process a conversational message to build InfoEx payloads.

**Request:**
```json
{
    "session_id": "your-session-id-here",
    "message": "I observed a size 2 storm slab avalanche today",
    "request_values": {
        "operation_id": "your-operation-uuid-here",
        "location_uuids": ["location-uuid-1", "location-uuid-2"],
        "zone_name": "Your Zone Name",
        "date": "MM/DD/YYYY"
    },
    "conversation_context": "Optional: Context from n8n user conversation"
}
```

**Response:**
```json
{
    "response": "I need a few more details about the avalanche. What aspect was it on, and what was the trigger?"
}
```

### Submit to InfoEx
```
POST /api/submit-to-infoex
```

Submit completed payloads to InfoEx API.

**Request:**
```json
{
    "session_id": "unique-session-id",
    "submission_types": ["avalanche_observation", "field_summary", "hazard_assessment"]
}
```

**Response:**
```json
{
    "success": true,
    "message": "Processed 3 submissions. All successful! Details: avalanche_observation: Submitted (UUID: 123e4567) | field_summary: Submitted (UUID: 234e5678) | hazard_assessment: Submitted (UUID: 345e6789)",
    "submissions": [...]
}
```

### Session Status
```
GET /api/session/{session_id}/status
```

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
    "last_updated": "2025-10-06T14:30:00Z",
    "conversation_length": 8
}
```

### Clear Session
```
DELETE /api/session/{session_id}/clear
```

Clear a session and start fresh.

### Health Check
```
GET /health
```

Check service health and dependencies.

### Get Locations
```
GET /api/locations
```

Get available InfoEx locations for the operation.

## n8n Integration

### HTTP Request Node Configuration

Configure your n8n HTTP Request node as follows:

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
        "value": "={{ $json.session_id }}"
      },
      {
        "name": "message",
        "value": "={{ $json.user_message }}"
      },
      {
        "name": "request_values",
        "value": {
          "operation_id": "{{ $env.INFOEX_OPERATION_ID }}",
          "location_uuids": "={{ $json.location_uuids }}",
          "zone_name": "={{ $json.zone_name }}",
          "date": "={{ $now.format('MM/dd/yyyy') }}"
        }
      }
    ]
  }
}
```

### Example n8n Workflow

1. **Webhook Trigger** → Receive message from Slack/Teams
2. **Set Fixed Values** → Map zone names, guide names, etc.
3. **HTTP Request** → Call `/api/process-report`
4. **Switch Node** → Check if more info needed or ready to submit
5. **Loop** → Continue conversation until ready
6. **HTTP Request** → Call `/api/submit-to-infoex`
7. **Notification** → Send success/failure message

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Your Anthropic API key | Required |
| `ENVIRONMENT` | Active environment (staging/production) | staging |
| `STAGING_API_KEY` | InfoEx staging API key | Required for staging |
| `STAGING_OPERATION_UUID` | InfoEx staging operation UUID | Required for staging |
| `PRODUCTION_API_KEY` | InfoEx production API key | Required for production |
| `PRODUCTION_OPERATION_UUID` | InfoEx production operation UUID | Required for production |
| `REDIS_URL` | Redis connection URL | redis://localhost:6379 |
| `REDIS_HOST` | Redis server host (if not using URL) | localhost |
| `REDIS_PORT` | Redis server port (if not using URL) | 6379 |
| `REDIS_PASSWORD` | Redis password (if set) | None |
| `REDIS_SESSION_PREFIX` | Prefix for Redis session keys (prevents n8n conflicts) | "claude" |
| `INFOEX_SUBMISSION_STATE` | Observation state: IN_REVIEW or SUBMITTED | IN_REVIEW |
| `SESSION_TTL_SECONDS` | Session timeout in seconds | 3600 |
| `CLAUDE_MODEL` | Claude model to use | claude-3-opus-20240229 |
| `LOG_LEVEL` | Logging level | INFO |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins (JSON array) | ["http://localhost:5678"] |

## Development

### Running Tests
```bash
pytest tests/ -v
```

### Code Formatting
```bash
black app/
flake8 app/
mypy app/
```

### Adding New Observation Types

1. Add the payload template to `data/aurora_templates/`
2. Update `InfoExConstants.get_required_fields()` in `app/agent/constants.py`
3. Add validators in `PayloadBuilder._build_validators()` in `app/services/payload.py`
4. Update the endpoint mapping in `InfoExClient.submit_observation()`

## Deployment

### Deploy to Render.com

1. Create a new Web Service
2. Connect your GitHub repository
3. Set environment variables
4. Deploy!

### Deploy to AWS/GCP/Azure

Use the provided `Dockerfile`:

```bash
docker build -t infoex-agent .
docker run -p 8000:8000 --env-file .env infoex-agent
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        n8n Workflow                              │
│                            ↓                                     │
│         HTTP POST /api/process-report                           │
└─────────────────────────────────────────────────────────────────┘
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              InfoEx Claude Agent Microservice                    │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    FastAPI Application                    │   │
│  │                 (Routes, Error Handling)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  Claude Agent Service                     │   │
│  │            (Anthropic API, System Prompts)               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 Redis Session Store                       │   │
│  │              (Conversation History, TTL)                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                            ↓                                     │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                InfoEx API Client                          │   │
│  │           (Individual Endpoint Submission)                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Troubleshooting

### Common Issues

1. **Session Not Found**
   - Sessions expire after 1 hour by default
   - Check Redis connection
   - Verify session_id format

2. **Validation Errors**
   - Check date format (MM/DD/YYYY)
   - Verify location UUIDs exist
   - Ensure required fields are provided

3. **Claude Not Responding**
   - Verify Anthropic API key
   - Check rate limits
   - Review conversation length

4. **InfoEx Submission Fails**
   - Verify API credentials
   - Check if using correct environment
   - Review validation errors in response

### Logging

The service uses structured JSON logging. To view logs:

```bash
docker-compose logs -f infoex-agent
```

Filter for specific events:
```bash
docker-compose logs infoex-agent | grep "submission_successful"
```

## License

Proprietary - Aurora Backcountry

## Support

For issues or questions, contact the Aurora Backcountry development team.
