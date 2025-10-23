# Avalanche Summary Submission Fix

## The Problem
When n8n submitted avalanche summaries, the submission would appear successful but return `UUID: None` and nothing would appear in InfoEx.

### Root Causes:
1. **Field Name Mismatch**: Claude was generating JSON with incorrect field names:
   - Used `observationDateTime` instead of `obDate`
   - Used generic field names instead of InfoEx-specific ones

2. **Value Mapping Issue**: Natural language inputs weren't being mapped to correct InfoEx enum values:
   - "Avalanches observed: Yes" needs to become `avalanchesObserved: "New avalanches"`
   - Not just a boolean true/false

3. **Silent Failures**: InfoEx returned 200 OK but without a UUID, and the service treated this as success

## The Fix

### 1. Enhanced System Prompt
Added explicit field mapping guidance in `app/agent/prompts.py`:
```
CRITICAL Field Mapping for avalanche_summary:
- "avalanches observed: yes" → avalanchesObserved: "New avalanches"
- "avalanches observed: no" → avalanchesObserved: "No new avalanches"
- "percent area observed: 20" → percentAreaObserved: 20 (numeric)
- Use obDate NOT observationDateTime
- Always use the exact field names from the InfoEx API
```

### 2. Field Name Correction
Added automatic field mapping in `app/agent/claude_agent.py`:
```python
field_mappings = {
    "observationDateTime": "obDate",
    "observationDate": "obDate",
    "date": "obDate",
    "avalanches_observed": "avalanchesObserved",
    "percent_area_observed": "percentAreaObserved",
    "operation_id": "operationUUID",
    "location_uuids": "locationUUIDs"
}
```

### 3. Value Conversion
Added special handling for avalanche_summary boolean to enum conversion:
```python
if obs_type == "avalanche_summary" and "avalanchesObserved" in corrected_data:
    val = corrected_data["avalanchesObserved"]
    if isinstance(val, bool) or str(val).lower() in ["yes", "true"]:
        corrected_data["avalanchesObserved"] = "New avalanches" if val else "No new avalanches"
```

### 4. Better Error Detection
Improved response handling in `app/services/infoex.py`:
- Now checks if UUID exists in 200 response
- Logs detailed error if no UUID returned
- Returns proper error status instead of false success

## Result
Avalanche summaries should now:
- Use correct InfoEx field names
- Map natural language to proper enum values
- Properly detect and report submission failures
- Successfully submit to InfoEx with valid UUIDs
