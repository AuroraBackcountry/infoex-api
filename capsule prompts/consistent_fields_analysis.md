# InfoEx Consistent Fields Analysis

## 1. Fields Present in ALL Payloads (100% Consistency)

### API Required Fields
- **obDate** - Present in all 8 payload types (REQUIRED)
- **state** - Present in all 8 payload types (REQUIRED: "IN_REVIEW" or "SUBMITTED")

### Commonly Shared Fields (Nearly Universal)
- **locationUUIDs** - Present in 7/8 payloads (PWL is exception)
- **operationUUID** - Present in all 8 payloads

## 2. Fields Present in Most Payloads (50%+ Consistency)

### Time-Related
- **obTime** - Present in 5/8 payloads:
  - field_summary
  - avalanche_observation
  - hazard_assessment
  - snowpack_summary
  - snowProfile_observation

### Location/Spatial Fields
- **elevation** - Various forms across payloads:
  - elevationMin/elevationMax (field_summary, avalanche_observation)
  - elevation (snowProfile_observation)
  - elevationBand (hazard_assessment)

- **aspect** - Various forms:
  - aspectFrom/aspectTo (avalanche_observation)
  - aspect (snowProfile_observation)
  - aspectElevation (snowProfile_observation, terrain_observation)
  - location (JSON string with aspects in hazard_assessment)

### Comments/Narrative Fields
- **comments** - Present in 4/8 payloads:
  - field_summary
  - avalanche_observation
  - avalanche_summary
  - pwl_persistent_weak_layer

- **Narrative variants**:
  - snowpackSummary (snowpack_summary)
  - summary (snowProfile_observation)
  - terrainNarrative (terrain_observation)

### Meta/Workflow Fields
- **attachments** - Present in 5/8 payloads
- **shareLevel** - Present in 5/8 payloads
- **workflowExecutionUUID** - Available in most as optional
- **createUserUUID/reviewUserUUID/submitUserUUID** - Available in most as optional

## 3. Passively Gathered Data (System/Session)

These can be automatically populated from the system/session:

### From User Session
- **operationUUID** - User's operation ID (constant for session)
- **createUserUUID** - Current user's ID
- **usersPresent** - Array with current user UUID (hazard_assessment)
- **observers** - Array with current user UUID (snowProfile_observation)

### From System
- **obDate** - Today's date (formatted as MM/DD/YYYY)
- **obTime** - Current time when observation is made
- **occurrenceTimezone** - User's timezone (e.g., "America/Vancouver")
- **state** - Default to "IN_REVIEW" for all submissions

## 4. Initial Interaction Data Collection

Based on the Elrich prompts and consistent fields, gather these in the first interaction:

### Essential First Questions
1. **Date Verification**
   - "Is the report for today, {{today's date}}?"
   - Maps to: obDate (all payloads)

2. **Guide Identification**
   - "Were there any other guides working with you today?"
   - Maps to: 
     - usersPresent (hazard_assessment)
     - observers/observersString (snowProfile_observation)
     - Guide names for report headers

3. **Zone/Location**
   - "Which zone did you operate in today?"
   - Maps to:
     - locationUUIDs (most payloads)
     - Zone name for narratives
     - Helps determine elevation bands

4. **Timing**
   - "What time did you start and end?"
   - Maps to:
     - obStartTime/obEndTime (field_summary)
     - obTime (multiple payloads)
     - Helps establish observation window

5. **Daily Summary**
   - "Brief overview: number of guests, mountain/objective, timing"
   - Maps to:
     - comments (multiple payloads)
     - Daily summary sections
     - Context for all observations

## 5. Recommended Initial Data Structure

```json
{
  "session_data": {
    "user_name": "{{from session}}",
    "user_uuid": "{{from session}}",
    "operation_uuid": "{{from session}}",
    "timezone": "America/Vancouver",
    "today_date": "{{system date}}"
  },
  
  "initial_report_data": {
    "report_date": null,           // Confirmed date (usually today)
    "zone_name": null,             // Selected zone
    "location_uuids": [],          // Mapped from zone
    "guides": [],                  // Array of guide names/UUIDs
    "start_time": null,            // HH:MM format
    "end_time": null,              // HH:MM format
    "guest_count": null,           // Number of guests
    "objectives": null,            // Mountains/routes
    "daily_summary": null          // Brief narrative
  },
  
  "reusable_fields": {
    "obDate": "{{report_date}}",
    "operationUUID": "{{operation_uuid}}",
    "locationUUIDs": "{{location_uuids}}",
    "state": "IN_REVIEW",
    "createUserUUID": "{{user_uuid}}",
    "usersPresent": "{{guide_uuids}}",
    "observers": "{{guide_uuids}}",
    "observersString": "{{guide_names}}"
  }
}
```

## 6. Benefits of Initial Data Collection

### Efficiency Gains
- **obDate** - Used in ALL 8 payload types
- **operationUUID** - Used in ALL 8 payload types  
- **locationUUIDs** - Used in 7/8 payload types
- **state** - Used in ALL 8 payload types
- **Time data** - Reusable across 5/8 payloads
- **Guide/observer data** - Reusable in multiple payloads

### Context Benefits
- Zone selection helps pre-filter location UUIDs
- Daily summary provides context for all subsequent observations
- Time window establishes when observations are valid
- Guide information ensures proper attribution

### Validation Benefits
- Early date confirmation prevents date errors
- Zone validation ensures valid location UUIDs
- Time validation ensures logical start/end sequence

## 7. Additional Recommendations

### Smart Defaults
- Set `shareLevel` based on operation preferences
- Default `assessmentType` to "Nowcast" for hazard assessments
- Pre-populate elevation bands based on zone characteristics

### Progressive Data Enhancement
- If zone has known elevation ranges, pre-populate:
  - elevationMin/elevationMax
  - Elevation bands for hazard ratings
- If specific locations mentioned, extract:
  - Aspect information
  - Elevation details

### Validation Rules
- Ensure obDate is within operational window (typically within 7 days)
- Validate time formats (24-hour HH:MM)
- Confirm location UUIDs exist for the operation
- Verify guide UUIDs are valid (if using UUID system)

This initial data collection strategy ensures that ~25% of required fields across all payload types are captured once and reused, significantly reducing redundancy and improving data consistency.
