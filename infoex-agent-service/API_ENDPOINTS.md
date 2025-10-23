# InfoEx Claude Agent Service - API Endpoints

## Complete List of Endpoints

### 1. **Root Endpoint**
- **GET** `/`
- **Description**: Service information and available endpoints
- **Response**: 
  ```json
  {
    "service": "InfoEx Claude Agent",
    "version": "0.1.0",
    "status": "running",
    "environment": "staging",
    "endpoints": {...}
  }
  ```

### 2. **Process Report** (Main Claude Endpoint)
- **POST** `/api/process-report`
- **Description**: Send data to Claude for parsing, validation, and formatting
- **Request Body**:
  ```json
  {
    "session_id": "unique-session-id",
    "message": "Submit avalanche observation size 3 at Glacier Bowl...",
    "request_values": {
      "operation_id": "your-operation-uuid-here",
      "location_uuids": ["location-uuid-1", "location-uuid-2"],
      "zone_name": "Your Zone Name",
      "date": "MM/DD/YYYY"
    },
    "submission_state": "IN_REVIEW"  // Optional: "IN_REVIEW" or "SUBMITTED"
  }
  ```
- **Response**: Plain text response from Claude
- **Purpose**: This is where n8n sends observation data for Claude to process

### 3. **Submit to InfoEx**
- **POST** `/api/submit-to-infoex`
- **Description**: Submit validated payloads to InfoEx API
- **Request Body**:
  ```json
  {
    "session_id": "unique-session-id",
    "submission_types": ["avalanche_observation", "field_summary"],
    "submission_state": "IN_REVIEW"  // Optional: "IN_REVIEW" or "SUBMITTED"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Processed 2 submissions. All successful!",
    "submissions": [
      {
        "observation_type": "avalanche_observation",
        "success": true,
        "result": {"uuid": "12345-67890"}
      }
    ]
  }
  ```

### 4. **Session Status**
- **GET** `/api/session/{session_id}/status`
- **Description**: Check current session status and readiness
- **Response**:
  ```json
  {
    "session_id": "unique-session-id",
    "status": "active",
    "payloads_ready": ["avalanche_observation"],
    "missing_data": {
      "field_summary": ["obEndTime", "weatherSummary"]
    },
    "last_updated": "2025-10-22T10:30:00Z",
    "conversation_length": 5
  }
  ```

### 5. **Clear Session**
- **DELETE** `/api/session/{session_id}/clear`
- **Description**: Clear a session and start fresh
- **Response**:
  ```json
  {
    "message": "Session cleared successfully."
  }
  ```

### 6. **Health Check**
- **GET** `/health`
- **Description**: Service health status
- **Response**:
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-10-22T10:30:00Z",
    "checks": {
      "redis": true,
      "claude": true,
      "infoex": true
    },
    "version": "0.1.0"
  }
  ```

### 7. **Get InfoEx Locations**
- **GET** `/api/locations`
- **Description**: Get available InfoEx locations
- **Response**:
  ```json
  {
    "locations": [
      {
        "uuid": "location-uuid",
        "name": "Glacier Bowl",
        "zone": "Your Zone Name"
      }
    ],
    "count": 15
  }
  ```

### 8. **API Documentation**
- **GET** `/docs`
- **Description**: Interactive API documentation (Swagger/OpenAPI)
- **Access**: Via browser for interactive testing

## InfoEx Observation Types Handled

The service processes these observation types through Claude:

1. **avalanche_observation** → `/observation/avalanche`
2. **avalanche_summary** → `/observation/avalancheSummary`
3. **field_summary** → `/observation/fieldSummary`
4. **hazard_assessment** → `/observation/hazardAssessment`
5. **pwl_persistent_weak_layer** → `/observation/pwl`
6. **snowpack_summary** → `/observation/snowpackSummary`
7. **snowProfile_observation** → `/observation/snowProfile`
8. **terrain_observation** → `/observation/terrainUse`

## Typical Flow

1. **n8n → `/api/process-report`**: Send observation data to Claude
2. **Claude processes and validates the data**
3. **n8n → `/api/session/{id}/status`**: Check if payloads are ready
4. **n8n → `/api/submit-to-infoex`**: Submit to InfoEx when ready
5. **Response includes InfoEx UUIDs for successful submissions**

## Authentication

- **API Key**: Set via environment variable
- **Headers**: Standard HTTP headers accepted
- **CORS**: Configured for allowed origins

## Error Responses

All errors follow this format:
```json
{
  "error": "Error type",
  "detail": "Specific error message",
  "code": "ERROR_CODE"
}
```

Common status codes:
- `200`: Success
- `404`: Session or resource not found
- `422`: Validation error
- `429`: Rate limit exceeded
- `500`: Internal server error
