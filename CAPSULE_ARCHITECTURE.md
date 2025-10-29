# Aurora InfoEx Reporting - Capsule Architecture

## 🎯 **Overview**

The Aurora InfoEx reporting system uses a **capsule-based architecture** that breaks down complex avalanche reports into manageable, self-contained questions. Each capsule represents one section of the report and can be processed independently.

## 🏗️ **System Components**

### **1. Dialogue Agent (n8n)**
- **Purpose**: Guide users through report creation using capsule questions
- **Method**: Static prompt + dynamic question capsules from database
- **Storage**: Postgres for responses, Redis for session state
- **Output**: Completed capsule payloads in database

### **2. Markdown Generator Tool**
- **Purpose**: Create human-readable report from completed capsules
- **Trigger**: Called when all required capsules are complete
- **Method**: Converts JSON data to OGRS-compliant markdown
- **Output**: Formatted markdown report

### **3. Claude Microservice (Render)**
- **Purpose**: Validate and submit payloads to InfoEx API
- **Method**: Retrieve JSON from Postgres, validate, submit
- **Features**: Error handling, retry logic, response tracking
- **Output**: InfoEx submission confirmations

## 📋 **Capsule Structure**

Each capsule is a self-contained unit with:

```json
{
  "capsule_type": "field_summary",
  "question": "Please provide your field observations for today...",
  "payload": {
    "obDate": {
      "type": "string",
      "value": "{{inherited.report_date}}",
      "format": "MM/DD/YYYY",
      "required": true,
      "inherited": true
    },
    "tempHigh": {
      "type": "number",
      "value": null,
      "required": true,
      "validation": {
        "min": -50,
        "max": 50
      }
    }
  },
  "completion_status": {
    "is_complete": false,
    "missing_required_fields": [],
    "missing_ideal_fields": []
  }
}
```

## 🔄 **Capsule Types & Sequence**

### **Optimal Workflow Sequence**
1. **initial_data_collection** - Universal fields (date, guides, zone)
2. **field_summary** - Weather and snow observations  
3. **avalanche_observation** - Individual avalanche details
4. **avalanche_summary** - Overall avalanche activity
5. **snowpack_summary** - Snowpack structure narrative
6. **hazard_assessment** - Ratings and avalanche problems
7. **terrain_observation** - Terrain choices and strategy
8. **report_review** - Data validation and approval
9. **markdown_generation** - Human-readable report creation
10. **infoex_submission** - Final API submission

### **Additional Capsules**
- **snowProfile_observation** - Detailed snow profiles
- **pwl_persistent_weak_layer** - Seasonal PWL tracking

## 🔄 **Data Flow Architecture**

```
User Message → Parse Intent → Update Current Capsule → Check Completion → 
If Complete: Trigger Inheritance → Get Next Capsule → Present Next Question
If Incomplete: Ask Follow-up Questions
```

### **Complete Workflow**
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

## 🔗 **Separation of Concerns**

### **1. Capsules (Dialogue Phase)**
**Purpose**: Conversational data gathering and light processing

**Key Characteristics**:
- **Flexible structure** - Can store any data needed for conversation
- **Light validation** - Basic checks during data entry
- **User-friendly** - Questions and responses in natural language
- **Stores everything** - Both InfoEx fields and additional context

**Example**:
```json
"temperature": {
  "high": -2,
  "low": -8,
  "user_said": "it was cold, maybe minus 8 at the coldest",
  "notes": "measured at 2000m"
}
```

### **2. AURORA_IDEAL (API Phase)**
**Purpose**: Strict API validation and submission

**Key Characteristics**:
- **Strict structure** - Must match InfoEx API exactly
- **Full validation** - Claude ensures all fields are correct
- **API-ready** - Direct submission to InfoEx endpoints
- **Error handling** - Retry logic for failed submissions

**Example**:
```json
{
  "tempHigh": -2,
  "tempLow": -8
}
```

## 🔄 **Data Inheritance System**

### **Automatic Inheritance**
Values marked with `"inherited": true` are automatically populated from previous capsules:

```json
"obDate": {
  "value": "{{inherited.report_date}}",
  "inherited": true
}
```

### **Inherited Values**
- `obDate` - Report date
- `operationUUID` - Organization identifier
- `locationUUIDs` - Zone identifiers
- `obStartTime` - Operations start time
- `obEndTime` - Operations end time
- Guide names and other context

### **Fixed Values (Auto-populated)**
- `state` - Submission state (default: "IN_REVIEW")
- `createUserUUID` - User identifier
- `createTime` - Timestamp

## 📊 **Database Schema**

### **Core Tables**
```sql
-- Static capsule definitions
CREATE TABLE capsule_templates (
  capsule_type TEXT PRIMARY KEY,
  question TEXT NOT NULL,
  capsule_structure JSONB NOT NULL
);

-- Dynamic report data
CREATE TABLE report_capsules (
  capsule_uuid UUID PRIMARY KEY,
  parent_report_uuid UUID NOT NULL,
  report_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  is_complete BOOLEAN DEFAULT FALSE,
  missing_required_fields TEXT[] DEFAULT '{}',
  missing_ideal_fields TEXT[] DEFAULT '{}',
  validation_errors TEXT[] DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP,
  infoex_uuid TEXT,
  submission_status TEXT DEFAULT 'pending'
);
```

## 🔄 **Session Management**

### **Redis Session Structure**
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

### **Claude Retry Management**
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

## 📅 **Date Format Standards**

- **Internal Storage**: ISO format `yyyy-MM-dd`
- **User Display**: ISO format `yyyy-MM-dd`
- **InfoEx API**: `MM/DD/YYYY` (converted at submission)

## 🚀 **InfoEx Submission Process**

### **Submission Flow**
1. **Trigger**: Manual trigger after report review
2. **Retrieval**: Claude pulls JSON from Postgres
3. **Validation**: Check required fields, formats
4. **Conversion**: Date format conversion (ISO → MM/DD/YYYY)
5. **Submission**: Individual endpoint calls to InfoEx
6. **Response**: Store results in Postgres

### **Submission States**
- **IN_REVIEW**: Draft state, not public (default)
- **SUBMITTED**: Final state, publicly visible

### **Error Handling Strategy**
When InfoEx returns an error, Claude:

1. **Parses Error**: Extract field-specific issues
2. **Creates Context**: Store in Redis with error details
3. **Modifies Payload**: Attempt to fix based on error
4. **Retries**: Up to 3 attempts with modifications
5. **Reports**: Return detailed status to caller

## 🎯 **Validation Strategy**

### **Stage 1: Dialogue Validation (Light)**
- Required fields present
- Basic format checks
- User-friendly error messages
- Allow flexibility for conversation flow

### **Stage 2: API Validation (Strict)**
- Exact InfoEx field requirements
- OGRS code compliance
- Enum value validation
- Retry with modifications on failure

## 📡 **InfoEx API Endpoints Used**

- `/observation/fieldSummary` - Field observations with weather
- `/observation/avalancheSummary` - Avalanche activity overview  
- `/observation/avalanche` - Individual avalanche details
- `/observation/hazardAssessment` - Ratings and problems
- `/observation/snowpackAssessment` - Snowpack narrative
- `/observation/snowpack` - Detailed snow profiles
- `/observation/terrain` - Terrain observations
- `/pwl` - Persistent weak layers

**Note**: Aurora does NOT use `/observation/weather` (for automated stations).

## 🎯 **Benefits of Capsule Architecture**

### **1. User Experience**
- **Natural conversation** without rigid API constraints
- **Guided data collection** with structured questions
- **Real-time validation** and progress tracking
- **Flexible workflow** that adapts to user expertise

### **2. Technical Benefits**
- **Modular**: Each section independently processable
- **Resumable**: Continue interrupted reports
- **Trackable**: Clear completion status
- **Testable**: Validate each capsule separately
- **Scalable**: Database-driven state management

### **3. Data Integrity**
- **Strict validation** only where needed (API submission)
- **Automatic inheritance** eliminates manual data passing
- **Error recovery** with Claude's retry logic
- **Audit trail** of all changes and submissions

### **4. Maintainability**
- **Clear separation** between dialogue and API phases
- **Flexible data storage** in capsules
- **Independent service scaling**
- **Clean error handling** and debugging

## 🔄 **Workflow States**

### **Report States**
1. **INITIALIZING** - Creating new report and first capsule
2. **DATA_COLLECTION** - Collecting data through capsules
3. **REVIEW** - All data collected, ready for review
4. **MARKDOWN_GENERATION** - Creating markdown report
5. **SUBMISSION** - Submitting to InfoEx
6. **COMPLETE** - Report fully processed

### **Capsule States**
1. **PENDING** - Not yet started
2. **IN_PROGRESS** - Currently collecting data
3. **COMPLETE** - All required fields filled
4. **SUBMITTED** - Sent to InfoEx

---

*This capsule-based architecture provides a clean separation of concerns between data collection, report generation, and API submission while maintaining flexibility and user-friendliness.*