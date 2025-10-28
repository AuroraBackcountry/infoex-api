# Capsule-Focused Documentation Updates

## Terminology Changes
- **"Fixed values" → "Inherited values"**
  - Values that persist across capsules (obDate, operationUUID, locationUUIDs, etc.)
  - Populated via Supabase functions/triggers

## Architecture Clarification
1. **Capsules (Dialogue Phase)**
   - Self-contained question units
   - Store both InfoEx fields and additional context
   - Light validation only
   - Located in: `capsule prompts/`

2. **AURORA_IDEAL (InfoEx Agent Service)**
   - Strict InfoEx API payloads
   - Final validation and submission
   - Located in: `infoex-agent-service/data/aurora_templates/`

## Key Principles
- **Separation of Concerns**: Clear distinction between dialogue (capsules) and API (AURORA_IDEAL)
- **Progressive Enhancement**: Light validation → Strict validation
- **Context Preservation**: Capsules can store user-friendly data alongside API fields

## Updated Files
✓ Created `SEPARATION_OF_CONCERNS.md` - Main architecture explanation
✓ Created `CAPSULE_ARCHITECTURE.md` - Two-agent system documentation  
✓ Created `REDIS_SESSION_MANAGEMENT.md` - Updated session approach
✓ Updated terminology in:
  - `infoex-agent-service/SUBMISSION_WORKFLOW.md`
  - `infoex-agent-service/N8N_REQUEST_FORMAT.md`
  - `ARCHITECTURE_UPDATE_PLAN.md`
  - `infoex-agent-service/app/agent/knowledge_base.py`
✓ Removed outdated files:
  - `AGENT_INTEGRATION_SUMMARY.md`
  - `MICROSERVICE_ARCHITECTURE.md`
  - `MICROSERVICE_IMPLEMENTATION_SUMMARY.md`
  - `SHARED_REDIS_SUMMARY.md`
  - `infoex-agent-service/SHARED_REDIS_ARCHITECTURE.md`
✓ Updated agent prompts:
  - Removed deprecated tools (Airtable, Knowledge Query)
  - Clarified submission process

## Remaining Focus Areas
- Ensure all docs reference capsules for dialogue, AURORA_IDEAL for API
- Maintain clear separation in documentation structure
- Avoid PostgreSQL integration details (for later session)
