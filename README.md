# Aurora Avalanche Reporting System

## Overview

This project consists of **two separate systems** with a **two-agent architecture** that work together to transform conversational avalanche safety reports into structured data submitted to the InfoEx Canadian avalanche database.

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                         SYSTEM 1: Report Generation                  │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Agent 1: Conversational Data Collection (Elrich Dumont)        │ │
│  │ - Natural 15-step conversation with guides                     │ │
│  │ - Captures raw responses                                       │ │
│  │ - No formatting or validation                                  │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│                    Raw Conversational Data                           │
│                              ↓                                       │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │ Agent 2: Formatting & Translation                              │ │
│  │ - Translates casual language → OGRS terminology                │ │
│  │ - Maps to Aurora/InfoEx schema                                 │ │
│  │ - Generates Markdown view                                      │ │
│  │ - Validates against InfoEx constants                           │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                              ↓                                       │
│                  Aurora JSON (JSONB) + Metadata                      │
│                              ↓                                       │
│                      Supabase Storage                                │
│                  - structured_data (JSONB)                           │
│                  - markdown_view (TEXT, generated)                   │
└──────────────────────────────────────────────────────────────────────┘
                                ↓
┌──────────────────────────────────────────────────────────────────────┐
│                   SYSTEM 2: InfoEx API Submission                    │
│                                                                      │
│  Read Aurora JSON from Supabase                                     │
│            ↓                                                         │
│  Strip Aurora Metadata (_aurora_metadata, _aurora_extensions)       │
│            ↓                                                         │
│  Submit via Individual Endpoints (Proven Working)                  │
│            ↓                                                         │
│  Update submission status in Supabase                               │
└──────────────────────────────────────────────────────────────────────┘
```

---

## System 1: Report Generation

### Two-Agent Architecture

#### Agent 1: Conversational Data Collection

#### Agent 1: Conversational Data Collection

**Purpose**: Natural conversation with guides to collect report information

**Responsibilities**:
- Guide users through 15-step report collection process
- Maintain conversational, empathetic tone
- Capture raw responses without formatting
- Store conversational data for Agent 2

**Agent 1 Does NOT**:
- Format data to schemas
- Translate to OGRS codes
- Validate enums
- Generate final JSON

**Output**: Raw conversational data (key-value pairs)

#### Agent 2: Formatting & Translation

**Purpose**: Transform raw conversational data into validated Aurora/InfoEx schema

**Responsibilities**:
- Translate casual language to OGRS terminology (e.g., "light winds" → "L")
- Map responses to exact InfoEx enums (e.g., "possible" → "Possible")
- Structure data according to Aurora/InfoEx hybrid schema
- Generate Markdown view for human reading
- Validate against InfoEx constants pulled from API
- Apply CMAH (Conceptual Model of Avalanche Hazard) methodology
- Add metadata for lineage tracking

**Agent 2 Does NOT**:
- Interact with users
- Conduct conversations
- Modify Agent 1's workflow

**Output**: 
- Aurora JSON (JSONB) with InfoEx-compatible structure
- Markdown view (generated, not stored as source)
- Validation metadata

### Agent Training & Enum Validation

Both agents are trained with:
- **Strict system prompts** defining exact terminology
- **JSON Schema constraints** for structured outputs
- **Few-shot examples** showing correct vs incorrect formats
- **Real-time validation** against database-stored InfoEx constants
- **Embedding-based similarity** for catching near-misses

**Critical Enum Mappings** (database-driven):
```
Likelihood → Sensitivity:
  "Unlikely" → "Unreactive"
  "Possible" → "Reactive"
  "Likely" → "Touchy"
  "Certain" → "Touchy"

Avalanche Types:
  "Storm Slabs" → "STORM_SLAB"
  "Wind Slabs" → "WIND_SLAB"
  etc.

Size: 1 → "Size1", 1.5 → "Size15", etc.
Wind Speed: "Light" → "L", "Moderate" → "M", etc.
```

### Data Storage

**Single Source of Truth**: Aurora JSON (JSONB) in Supabase

**Storage Structure**:
```sql
CREATE TABLE reports (
  id UUID PRIMARY KEY,
  user_id UUID NOT NULL,
  structured_data JSONB NOT NULL,  -- Aurora JSON with metadata
  markdown_view TEXT,               -- Generated on-demand or cached
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  submitted_at TIMESTAMP
);
```

**Aurora JSON includes**:
- `_aurora_metadata`: Lineage tracking (report_id, schema_version, created_by, timestamps)
- InfoEx-compatible observation data (fieldSummary, weather, avalancheProblems, hazardAssessment)
- `_aurora_extensions`: Submission status, InfoEx response data

### System 1 Does NOT
### System 1 Does NOT
- Submit to InfoEx APIs
- Handle downstream processing
- Transform Aurora schema (already InfoEx-compatible)

### Relevant Documentation
- `agent_system_prompt_report_process.md` - Agent 1 workflow and instructions
- `aurora-json-template.json` - Aurora/InfoEx hybrid schema specification
- `VALIDATION_RULES.md` - Field validation rules for Aurora schema
- `OGRS.txt` - Official Guidelines for Reporting Standards

---

## System 2: InfoEx API Submission

### Purpose
Submit Aurora-formatted reports from Supabase to the InfoEx API system using individual endpoint submissions.

### Process Flow
1. **Retrieve**: Read Aurora JSON from Supabase `structured_data` column
2. **Prepare**: Strip Aurora-specific metadata fields (`_aurora_metadata`, `_aurora_extensions`)
3. **Submit**: Individual POST calls to proven working endpoints
4. **Update**: Mark report as submitted in Supabase with InfoEx response data

### Individual Endpoint Submission Strategy
Uses separate API calls for each observation type for reliable, tested approach:

```bash
# 1. Field Summary
POST /observation/fieldSummary
{
  "obDate": "10/07/2025",
  "obStartTime": "08:30",
  "obEndTime": "15:45",
  "tempHigh": 0,
  "tempLow": -2,
  "comments": "Daily operational summary",
  "locationUUIDs": ["zone-uuid"],
  "operationUUID": "operation-uuid",
  "state": "SUBMITTED"
}

# 2. Avalanche Summary
POST /observation/avalancheSummary
{
  "obDate": "10/07/2025",
  "avalanchesObserved": "New avalanches",
  "percentAreaObserved": 75.0,
  "comments": "Avalanche activity summary",
  "locationUUIDs": ["zone-uuid"],
  "operationUUID": "operation-uuid",
  "state": "SUBMITTED"
}

# 3. Hazard Assessment
POST /observation/hazardAssessment
{
  "obDate": "10/07/2025",
  "obTime": "14:00",
  "assessmentType": "Nowcast",
  "usersPresent": ["user-uuid"],
  "avalancheProblems": [{ /* problem objects */ }],
  "hazardRatings": [{ /* rating objects */ }],
  "locationUUIDs": ["zone-uuid"],
  "operationUUID": "operation-uuid",
  "state": "SUBMITTED"
}

# 4. Avalanche Observation (if applicable)
POST /observation/avalanche
{
  "obDate": "10/07/2025",
  "obTime": "14:00",
  "character": "STORM_SLAB",
  "trigger": "Na",
  "sizeMin": 1.5,
  "sizeMax": 2.0,
  "locationUUIDs": ["zone-uuid"],
  "operationUUID": "operation-uuid",
  "state": "SUBMITTED"
}
```

**Benefits**:
- Proven working endpoints through extensive testing
- Clear error handling per observation type
- Flexible submission (can submit partial reports)
- Direct submission without workflow dependencies

### Dynamic Reference Data Syncing

System 2 maintains up-to-date mappings via periodic sync jobs:

#### Zone Mappings
```sql
-- Daily sync from GET /location
CREATE TABLE zone_mappings (
  zone_name TEXT PRIMARY KEY,
  location_uuid UUID NOT NULL,
  operation_uuid UUID NOT NULL,
  active BOOLEAN DEFAULT true,
  last_synced TIMESTAMP DEFAULT NOW()
);
```

#### InfoEx Constants
```sql
-- Daily sync from GET /observation/constants/
CREATE TABLE infoex_constants (
  constant_type TEXT NOT NULL,
  valid_values JSONB NOT NULL,
  last_updated TIMESTAMP DEFAULT NOW()
);
```

Ensures:
- No hardcoded UUIDs
- Always current enum values
- Validation against live InfoEx data

### System 2 Does NOT
- Interact with guides or users
- Generate Aurora JSON (only reads existing)
- Create Markdown
- Store reports (only reads and updates status)

### Relevant Documentation
- `README.md` (this document) - Overall architecture
- `FIELD_MAPPING_TABLE.md` - Individual endpoint field mapping guide
- `INFOEX_API_REFERENCE.md` - Complete InfoEx API documentation
- `infoex-api-docs.json` - Complete InfoEx API schema
- `infoex-api-payloads/` - Working payload templates:
  - `avalanche_observation.json`
  - `avalanche_summary.json`
  - `field_summary.json`
  - `hazard_assessment.json`
  - `snowProfile_observation.json` (detailed snow profiles)
  - `snowpack_summary.json` (general snowpack assessment)
  - `terrain_observation.json`
  - `pwl_persistent_weak_layer.json`

---

## Data Formats

### Aurora JSON Schema (Hybrid Approach)

The Aurora schema is a **hybrid format** that bridges conversational data collection and InfoEx API submission:

**Design Philosophy**:
- InfoEx-compatible field names and structure
- Optimized for single-document storage (all observations in one JSON)
- Includes metadata for lineage without affecting InfoEx submission
- Minimal transformation required for API submission

**Example Structure**:
```json
{
  "_aurora_metadata": {
    "report_id": "uuid",
    "schema_version": "2.0.0",
    "created_at": "2025-10-05T10:30:00Z",
    "created_by": "guide-name",
    "agent_version": "agent-2-v1.0.0",
    "raw_conversation_id": "uuid",
    "processing_notes": []
  },
  
  "fieldSummary": {
    "obDate": "2025/02/21",
    "tempHigh": 0,
    "tempLow": -2,
    "windSpeed": "M",
    "windDirection": "S",
    "hs": 200,
    "hn24": 30,
    "comments": "Daily operational summary",
    "locationUUIDs": ["zone-uuid"],
    "operationUUID": "operation-uuid",
    "state": "SUBMITTED"
  },
  
  "weather": {
    "obDate": "2025/02/21",
    "obTime": "08:00",
    "tempMax": 0,
    "tempMin": -2,
    "windSpeed": "M",
    "windDirection": "S",
    "locationUUIDs": ["zone-uuid"],
    "operationUUID": "operation-uuid",
    "state": "SUBMITTED"
  },
  
  "avalancheProblems": [
    {
      "obDate": "2025/02/21",
      "character": "STORM_SLAB",
      "location": "North aspects, treeline",
      "distribution": "Specific",
      "sensitivity": "Reactive",
      "typicalSize": "Size15",
      "state": "SUBMITTED"
    }
  ],
  
  "hazardAssessment": {
    "obDate": "2025/02/21",
    "hazardRatings": [
      { "elevationBand": "ALP", "hazardRating": "3" },
      { "elevationBand": "TL", "hazardRating": "2" },
      { "elevationBand": "BTL", "hazardRating": "2" }
    ],
    "state": "SUBMITTED"
  },
  
  "_aurora_extensions": {
    "submission_status": "pending",
    "infoex_submission": null
  }
}
```

### Why Hybrid Schema?

**Problem**: InfoEx schema is split across multiple API endpoints (weather, field summary, avalanche problems, hazard assessment), but guides provide information as one cohesive report.

**Solution**: Store everything in one Aurora document with InfoEx-compatible structure, then split for API submission.

**Benefits**:
- ✅ No transformation layer needed
- ✅ Direct validation against InfoEx schema
- ✅ Single document for queries and display
- ✅ Metadata doesn't interfere with submission
- ✅ Easy to generate Markdown from complete report

---

## Enum Mapping & Validation

### Database-Driven Mappings

All enum conversions are stored in the database and validated at runtime:

```sql
CREATE TABLE enum_mappings (
  id SERIAL PRIMARY KEY,
  mapping_type TEXT NOT NULL,
  source_value TEXT NOT NULL,
  target_value TEXT NOT NULL,
  valid_from DATE DEFAULT CURRENT_DATE,
  valid_to DATE,
  notes TEXT,
  UNIQUE(mapping_type, source_value, valid_from)
);
```

**Critical Mappings**:
- `likelihood_to_sensitivity`: "Possible" → "Reactive"
- `avalanche_types`: "Storm Slabs" → "STORM_SLAB"
- `avalanche_size`: 1.5 → "Size15"
- `wind_speed`: "Moderate" → "M"

### Multi-Layer Validation

1. **Agent 2 validates** during formatting (JSON Schema + few-shot learning)
2. **Database validates** against enum_mappings table
3. **InfoEx constants validate** against live API data
4. **Zod schema validates** structure before storage
5. **InfoEx API validates** on submission

---

## File Structure

### System 1 (Agent) Documentation
- `agent_system_prompt_report_process.md` - Agent 1 & 2 behavior and workflows
- `aurora-json-template.json` - Aurora/InfoEx hybrid schema specification
- `VALIDATION_RULES.md` - Validation rules and enum mappings
- `OGRS.txt` - Reporting standards reference

### System 2 (Submission) Documentation
- `README.md` - This architecture overview
- `FIELD_MAPPING_TABLE.md` - Individual endpoint field mapping guide
- `INFOEX_API_REFERENCE.md` - InfoEx API endpoints and usage
- `infoex-api-docs.json` - Complete API schema
- `infoex-api-payloads/` - Working payload templates for each observation type

### Supporting Documentation
- `AGENT_INTEGRATION_SUMMARY.md` - Two-agent workflow details
- `IMPLEMENTATION_GUIDE.md` - Implementation instructions
- `markdown-examples/` - Sample reports for reference

---

## Key Principles

### Separation of Concerns
- **Agent 1** focuses on conversational UX and data collection
- **Agent 2** focuses on formatting, validation, and schema compliance
- **System 2** focuses on reliable API submission
- Each component can be developed, tested, and deployed independently

### Single Source of Truth
- Aurora JSON (JSONB) is the authoritative data format
- Markdown is generated on-demand for human viewing
- InfoEx submission data is ephemeral (stripped from Aurora JSON)

### Schema Versioning
All Aurora JSON includes `_aurora_metadata.schema_version` for:
- Supporting schema evolution over time
- Converting old reports to new formats
- Maintaining backward compatibility
- Clear migration paths

### Data Flow
1. Raw conversation → Agent 1
2. Formatted data → Agent 2
3. Aurora JSON → Supabase
4. Stripped JSON → InfoEx API
5. Status update → Supabase

### Error Handling
- **Agent 1 errors**: User can retry conversation
- **Agent 2 errors**: Can reprocess raw data without user interaction
- **System 2 errors**: Original Aurora JSON preserved for retry
- **Atomic submission**: All-or-nothing prevents partial data in InfoEx

---

## Standards Compliance

### OGRS (Official Guidelines for Reporting Standards)
Agent 2 translates casual observations to OGRS codes. System 2 preserves these codes in InfoEx submission.

### CAA (Canadian Avalanche Association)
Both agents and submission system follow CAA standards for avalanche observation data structure and terminology.

### InfoEx API
- Aurora schema aligns with InfoEx field names and enums
- System 2 uses atomic batch submission (`/workflow/executionAggregate`)
- Dynamic syncing ensures validation against current InfoEx constants

---

## Development Guidelines

### When Working on Agent 1 (Conversation)
- Focus on natural, empathetic conversation flow
- Capture raw responses without formatting
- Test conversation quality and completion rate
- Ensure all 15 steps are covered
- **Do not** worry about schemas or validation

### When Working on Agent 2 (Formatting)
- Focus on accurate enum translation
- Validate against InfoEx constants
- Test edge cases and casual language variations
- Ensure schema compliance
- Generate accurate Markdown views
- **Do not** modify conversation flow

### When Working on System 2 (Submission)
- Focus on reliable atomic submissions
- Handle API errors gracefully
- Maintain sync jobs for zones and constants
- Track submission status accurately
- **Do not** modify report generation or formatting

---

## Maintenance

### Schema Stability
- Aurora schema changes are versioned (`schema_version` field)
- Old reports can be converted to new schema versions
- Document all breaking changes thoroughly

### API Monitoring
- Monitor InfoEx API changes via their documentation
- Update zone and constant sync jobs as needed
- Test against InfoEx staging environment before production

### Standards Updates
- Update OGRS code translations as standards evolve
- Maintain enum_mappings table with valid date ranges
- Archive example reports for regression testing

### Sync Jobs
- **Daily**: Sync InfoEx zones (`GET /location`)
- **Daily**: Sync InfoEx constants (`GET /observation/constants/`)
- **On failure**: Alert and retry with exponential backoff

---

*This document serves as the authoritative reference for the overall system architecture. Refer to component-specific documentation for implementation details.*
