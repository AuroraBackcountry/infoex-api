# Aurora Database Functions Guide

## Overview
This guide documents the PostgreSQL functions that power the Aurora InfoEx reporting system's capsule-based workflow.

## Report Initialization Functions

### `start_new_report()`
The main entry point for creating a new daily report.

**Parameters:**
- `p_user_id` (TEXT) - Unique identifier for the user
- `p_user_name` (TEXT) - Display name of the guide
- `p_operation_uuid` (UUID) - Aurora Backcountry operation UUID
- `p_operation_name` (TEXT) - Operation display name
- `p_report_date` (DATE) - Optional, defaults to today
- `p_timezone` (TEXT) - Optional, defaults to 'America/Vancouver' (PST)

**Returns:** JSONB containing:
```json
{
  "success": true,
  "parent_report_uuid": "uuid",
  "report_date": "2025-10-29",
  "user": {"id": "user123", "name": "Guide Name"},
  "operation": {"uuid": "...", "name": "Aurora Backcountry"},
  "capsules_created": [...],
  "initial_capsule": {...},
  "next_action": "Present initial_data_collection question to user"
}
```

**Example:**
```sql
SELECT start_new_report(
    'guide123',
    'Sarah Johnson',
    '00000000-0000-0000-0000-000000000001'::uuid,
    'Aurora Backcountry'
);
```

### `initialize_report_capsules()`
Creates all capsule rows for a new report from templates.

**What it does:**
- Creates 8 capsule rows (PWL created on demand)
- Copies question text and payload structure from templates
- Sets up tracking arrays for missing fields
- Assigns sequential numbers for workflow ordering

### `populate_initial_capsule()`
Pre-fills the first capsule with known data.

**Auto-populated fields:**
- `report_date` - Today's date in MM/DD/YYYY format
- `guides` - Array with current user's info
- `constants_populated` - Operation details, timezone, etc.

## Validation Functions

### `validate_capsule_payload()`
Main validation function that checks an entire capsule.

**Parameters:**
- `p_capsule_uuid` (UUID) - The capsule to validate

**Returns:** JSONB containing:
```json
{
  "valid": false,
  "has_all_required": false,
  "missing_required_fields": ["zone_name", "start_time"],
  "missing_ideal_fields": ["guest_count", "objectives"],
  "validation_errors": ["start_time must be in HH:MM format"],
  "capsule_type": "initial_data_collection",
  "capsule_uuid": "..."
}
```

### `update_capsule_field()`
Updates a single field with validation.

**Parameters:**
- `p_capsule_uuid` (UUID) - The capsule to update
- `p_field_name` (TEXT) - Field to update (e.g., 'zone_name')
- `p_field_value` (JSONB) - New value

**Example:**
```sql
-- Update zone name
SELECT update_capsule_field(
    'capsule-uuid-here'::uuid,
    'zone_name',
    '"Rogers Pass"'
);

-- Update start time
SELECT update_capsule_field(
    'capsule-uuid-here'::uuid,
    'start_time',
    '"08:30"'
);

-- Update array field
SELECT update_capsule_field(
    'capsule-uuid-here'::uuid,
    'location_uuids',
    '["uuid1", "uuid2"]'::jsonb
);
```

### `update_completion_status()`
Updates the capsule's completion tracking.

**What it does:**
- Runs full validation
- Updates `is_complete` flag
- Populates missing field arrays
- Stores validation errors

**Automatically called by:**
- `update_capsule_field()` after each update

### `validate_field_value()`
Low-level field validator.

**Validations:**
- Type checking (string, number, array, object)
- Format validation (dates, times)
- Enum validation
- Range validation for numbers
- Max length for strings
- Min/max items for arrays
- Special formats (precipitation codes)

### `validate_special_formats()`
Handles OGRS-specific validations:
- Precipitation codes (NIL, S1-S10, R, etc.)
- 24-hour time format
- ISO date format
- Zone name validation

### `validate_cross_field_rules()`
Validates relationships between fields:
- Temperature: `tempLow ≤ tempHigh`
- Elevation: `elevationMin ≤ elevationMax`
- Avalanche size: `sizeMin ≤ sizeMax`
- Depth: `depthMin ≤ depthMax`

## Workflow Example

```sql
-- 1. Start a new report
SELECT * FROM start_new_report(
    'guide456',
    'John Smith',
    'aurora-operation-uuid'::uuid,
    'Aurora Backcountry'
);

-- Returns parent_report_uuid and initial capsule_uuid

-- 2. Update fields as user provides information
SELECT update_capsule_field(capsule_uuid, 'zone_name', '"Wapta Icefields"');
SELECT update_capsule_field(capsule_uuid, 'start_time', '"07:45"');
SELECT update_capsule_field(capsule_uuid, 'end_time', '"16:30"');

-- 3. Check validation status
SELECT * FROM validate_capsule_payload(capsule_uuid);

-- 4. When complete, move to next capsule
-- (Field inheritance functions coming soon)
```

## Error Handling

All functions return structured JSONB responses:
- `success`: boolean indicating if operation succeeded
- `error` or `errors`: Description of what went wrong
- `validation_errors`: Array of specific validation failures

Example error response:
```json
{
  "success": false,
  "field": "start_time",
  "validation_errors": ["start_time must be in HH:MM format (24-hour)"]
}
```

## Best Practices

1. **Always validate before submission**
   - Use `validate_capsule_payload()` before marking complete
   - Check `is_complete` flag in database

2. **Use convenience functions**
   - `update_capsule_field()` instead of direct updates
   - `start_new_report()` instead of manual initialization

3. **Handle arrays properly**
   - Pass arrays as JSONB: `'["item1", "item2"]'::jsonb`
   - Don't forget empty arrays need casting: `ARRAY[]::UUID[]`

4. **Check for nulls**
   - Functions handle null/empty values gracefully
   - Required fields will fail validation if null

## Coming Soon

### Field Inheritance Functions
- `inherit_capsule_values()` - Copy values between capsules
- `get_inherited_field_values()` - Extract inheritable fields
- `apply_field_inheritance()` - Update next capsule

### Workflow Management
- `get_next_capsule()` - Determine sequence
- `mark_capsule_complete()` - Trigger next steps
- `create_complete_daily_report()` - Aggregate all data

