# Aurora InfoEx Reporting - Capsule Architecture

## Overview

The Aurora InfoEx reporting system uses a **capsule-based architecture** that breaks down complex avalanche reports into manageable, self-contained questions. Each capsule represents one section of the report and can be processed independently.

## System Components

### 1. Dialogue Agent (n8n)
- **Purpose**: Guide users through report creation
- **Method**: Static prompt + dynamic question capsules
- **Storage**: Postgres for responses, Redis for session state
- **Output**: Completed capsule payloads in database

### 2. Markdown Generator Tool
- **Purpose**: Create human-readable report from completed capsules
- **Trigger**: Called when all required capsules are complete
- **Output**: Formatted markdown report

### 3. Claude Microservice (Render)
- **Purpose**: Validate and submit payloads to InfoEx API
- **Method**: Retrieve JSON from Postgres, validate, submit
- **Features**: Error handling, retry logic, response tracking
- **Output**: InfoEx submission confirmations

## Capsule Structure

Each capsule is a self-contained unit with:

```json
{
  "capsule_type": "field_summary",
  "question": "Please provide your field observations for today...",
  "payload": {
    // Field definitions with types, validation, and inheritance
  },
  "completion_status": {
    "is_complete": false,
    "required_missing": [],
    "ideal_missing": []
  }
}
```

## Capsule Types

1. **initial_data_collection** - Universal fields (date, guides, zone)
2. **field_summary** - Weather and snow observations  
3. **avalanche_observation** - Individual avalanche details
4. **avalanche_summary** - Overall avalanche activity
5. **hazard_assessment** - Ratings and avalanche problems
6. **snowpack_summary** - Snowpack structure narrative
7. **snowProfile_observation** - Detailed snow profiles
8. **terrain_observation** - Terrain choices and strategy
9. **pwl_persistent_weak_layer** - Seasonal PWL tracking

## Data Flow

```
User Input → Dialogue Agent → Capsule Completion → Postgres Storage
                                                         ↓
                                              Markdown Generation
                                                         ↓
                                              Report Display
                                                         ↓
                                              [Trigger Submission]
                                                         ↓
                                              Claude Microservice
                                                         ↓
                                              InfoEx API
```

## Fixed Values and Inheritance

### Fixed Values (Auto-populated)
- `operationUUID` - Organization identifier
- `locationUUIDs` - Zone identifiers
- `state` - Submission state (default: "IN_REVIEW")
- `createUserUUID` - User identifier

### Inherited Values
Fields marked with `"inherited": true` are populated from previous capsules:
```json
"obDate": {
  "value": "{{inherited.obDate}}",
  "inherited": true
}
```

## Date Format Standards

- **Internal Storage**: ISO format `yyyy-MM-dd`
- **User Display**: ISO format `yyyy-MM-dd`
- **InfoEx API**: `MM/DD/YYYY` (converted at submission)

## Postgres Storage Schema

```sql
CREATE TABLE report_capsules (
  id UUID PRIMARY KEY,
  session_id TEXT NOT NULL,
  report_date DATE NOT NULL,
  
  -- Capsule payloads (JSONB)
  initial_data JSONB,
  field_summary JSONB,
  avalanche_observation JSONB,
  avalanche_summary JSONB,
  hazard_assessment JSONB,
  snowpack_summary JSONB,
  snowProfile_observation JSONB,
  terrain_observation JSONB,
  pwl JSONB,
  
  -- Metadata
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  submission_state TEXT DEFAULT 'IN_REVIEW',
  submitted_at TIMESTAMP,
  infoex_responses JSONB
);
```

## Session Management

- **Redis Key**: Simple session ID (e.g., `session-123`)
- **TTL**: Configurable (default 24 hours)
- **Content**: Current capsule state, user responses

## InfoEx Submission Process

1. **Trigger**: Manual trigger after report review
2. **Retrieval**: Claude pulls JSON from Postgres
3. **Validation**: Check required fields, formats
4. **Conversion**: Date format conversion (ISO → MM/DD/YYYY)
5. **Submission**: Individual endpoint calls to InfoEx
6. **Response**: Store results in Postgres

## Submission States

- **IN_REVIEW**: Draft state, not public (default)
- **SUBMITTED**: Final state, publicly visible

## Error Handling

The Claude microservice handles API errors by:
1. Parsing error response
2. Attempting field corrections
3. Retrying submission (up to 3 times)
4. Logging detailed error information
5. Returning actionable feedback

## Benefits of Capsule Architecture

1. **Modular**: Each section independently processable
2. **Flexible**: Skip irrelevant sections
3. **Resumable**: Continue interrupted reports
4. **Trackable**: Clear completion status
5. **Testable**: Validate each capsule separately

## InfoEx API Endpoints Used

- `/observation/fieldSummary` - Field observations with weather
- `/observation/avalancheSummary` - Avalanche activity overview  
- `/observation/avalanche` - Individual avalanche details
- `/observation/hazardAssessment` - Ratings and problems
- `/observation/snowpackAssessment` - Snowpack narrative
- `/observation/snowpack` - Detailed snow profiles
- `/observation/terrain` - Terrain observations
- `/pwl` - Persistent weak layers

Note: Aurora does NOT use `/observation/weather` (for automated stations).

---

*This capsule-based architecture provides a clean separation of concerns between data collection, report generation, and API submission.*
