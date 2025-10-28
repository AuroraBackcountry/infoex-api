# Architecture Update Plan - October 2025

## Overview
This document outlines the comprehensive updates needed to align the codebase with the new capsule-based architecture for Aurora's InfoEx reporting system.

## 1. Date Format Standardization

### Current State
- Mixed formats: `MM/DD/YYYY`, `yyyy-MM-dd`, `yyyy/mm/dd`
- Confusion about which format to use where

### New Standard
- **Display/Markdown**: ISO format `yyyy-MM-dd`
- **InfoEx API**: `MM/DD/YYYY` (converted at submission time)
- **Internal Storage**: ISO format `yyyy-MM-dd`

### Files to Update
- All markdown documentation files
- All capsule JSON files  
- Agent prompts
- Claude microservice payload conversion logic

## 2. Architecture Clarification

### New Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    User Conversation                             │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│     Agent 1: Dialogue Agent (Static Prompt + Dynamic Capsules)   │
│     - Guides conversation using question capsules                │
│     - Collects data progressively                               │
│     - Stores responses in Postgres                              │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│           Agent Tool: Markdown Report Generator                  │
│           - Triggered when all data collected                    │
│           - Creates formatted markdown report                     │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Postgres Database                               │
│     - Stores capsule JSON payloads                             │
│     - Stores report context                                      │
│     - Ready for InfoEx submission                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (On trigger)
┌─────────────────────────────────────────────────────────────────┐
│            Claude Microservice (Render)                          │
│     - Retrieves JSON from Postgres                             │
│     - Validates individual capsule payloads                      │
│     - Submits to InfoEx API                                     │
│     - Handles errors and retries                                │
└─────────────────────────────────────────────────────────────────┘
```

### Key Changes
- No more "Agent 2" - it's now an agent tool for markdown generation
- Claude is strictly a microservice for InfoEx submission
- Capsules are processed individually, not as complete reports
- Postgres stores all payload data

## 3. Redis Session Management

### Remove
- Shared Redis context documentation
- Redis prefix complications
- References to n8n/Claude shared sessions

### Implement
- Simple session ID as Redis key
- Claude maintains its own retry context for API failures
- Consider alternative to chat history for API retry logic

## 4. Postgres Integration

### New Storage Pattern
```sql
-- Example table structure
reports (
  id UUID,
  session_id TEXT,
  created_at TIMESTAMP,
  
  -- Capsule payloads (JSONB)
  initial_data_collection JSONB,
  field_summary JSONB,
  avalanche_observation JSONB,
  avalanche_summary JSONB,
  hazard_assessment JSONB,
  snowpack_summary JSONB,
  terrain_observation JSONB,
  pwl JSONB,
  
  -- Metadata
  submission_state TEXT DEFAULT 'IN_REVIEW',
  submitted_at TIMESTAMP,
  infoex_response JSONB
)
```

## 5. Submission Flow Updates

### Remove
- auto_submit flag and all references
- Automatic submission logic

### Implement  
- Trigger-based submission only
- Default state: `IN_REVIEW`
- State determines InfoEx visibility (public vs review)

## 6. Weather Endpoint Clarification

### Documentation Updates
- Aurora submits to `/observation/fieldSummary` (includes weather data)
- Aurora does NOT submit to `/observation/weather` (for weather stations)
- Field observations contain weather information but are guide-based
- Weather stations submit continuous automated data

## 7. Files to Remove/Update

### Remove Completely
- `AGENT_INTEGRATION_SUMMARY.md`
- References to `new_system_prompt_report_process.md`
- Shared Redis documentation that conflicts

### Update Agent Prompts
- Remove "Upload Daily Report to Airtable" references
- Remove "Knowledge Query" tool
- Remove "reference_dynamic_docs" tool  
- Update to use capsule-based questioning

## 8. Capsule Architecture Focus

### Capsule Structure
```json
{
  "capsule_type": "field_summary",
  "question": "Single comprehensive question",
  "payload": {
    "obDate": {
      "value": null,
      "type": "string", 
      "format": "yyyy-MM-dd",
      "required": true
    },
    // Inherited values populated automatically
    "operationUUID": {
      "value": "{{inherited.operationUUID}}",
      "type": "string",
      "required": true,
      "inherited": true
    }
  },
  "completion_status": {
    "is_complete": false,
    "required_missing": ["obDate", "tempHigh"]
  }
}
```

### AURORA_IDEAL Payload Usage
- Reserved exclusively for Claude microservice
- Not used in capsules or agent prompts
- Contains InfoEx-ready field structure

## 9. Fixed Values in Capsules

### Standard Fixed Values
- `operationUUID` - Aurora operation identifier
- `locationUUIDs` - Zone/location identifiers  
- `state` - Always "IN_REVIEW" by default
- `date` - Can be inherited from initial capsule

### Implementation
- Populated via database triggers
- Inherited through capsule chain
- Never asked from user

## 10. Tool Updates for Agent Prompts

### Deprecated Tools (Remove)
- Upload Daily Report to Airtable
- Knowledge Query
- reference_dynamic_docs
- Update Intent After Airtable Upload

### Current Tools
- Draft Generator Agent
- Update Intent (simplified)
- Think (for complex scenarios)

## Implementation Priority

1. **High Priority**
   - Update architecture documentation
   - Remove conflicting Redis documentation
   - Update agent prompts to remove deprecated tools

2. **Medium Priority**
   - Standardize date formats
   - Update capsule documentation
   - Create Postgres integration docs

3. **Low Priority**  
   - Clean up old references
   - Update example files
   - Archive v1/v2 agent prompts

## Testing Requirements

- Verify capsules work with new inherited value pattern
- Test Claude microservice with individual payloads
- Ensure date conversion works properly
- Validate Postgres storage and retrieval

---

*This plan ensures a clean, consistent architecture that separates concerns properly between dialogue collection, report generation, and API submission.*
