# Self-Contained Capsule Structure Reference

## Standard Capsule Format

Every capsule follows this exact structure for consistency and optimal prompt caching:

```json
{
  "capsule_type": "string",
  "question": "string",
  "payload": {},
  "completion_status": {}
}
```

## Field Structure in Payload

Each field in the payload contains:

```json
"field_name": {
  "value": null | "{{inherited.field}}" | default_value,
  "type": "string" | "number" | "array" | "object",
  "required": true | false,
  "inherited": true | false,
  
  // Validation options (as applicable):
  "enum": ["option1", "option2"],
  "validation": "range:min:max" | "format_type",
  "max_length": number,
  "format": "MM/DD/YYYY" | "HH:MM" | etc
}
```

## Completion Status Structure

```json
"completion_status": {
  "is_complete": false,
  "required_fields_missing": ["field1", "field2"],
  "aurora_ideal_missing": ["field3", "field4"],
  "validation_errors": []
}
```

## Inheritance Patterns

### Fields marked as inherited:
```json
"obDate": {
  "value": "{{inherited.obDate}}",
  "type": "string",
  "format": "MM/DD/YYYY",
  "required": true,
  "inherited": true
}
```

### Complex inheritance (arrays):
```json
"usersPresent": {
  "value": "{{inherited.usersPresent}}",
  "type": "array",
  "required": true,
  "inherited": true
}
```

## Validation Types

1. **Enum validation**:
   ```json
   "enum": ["CLR", "FEW", "SCT", "BKN", "OVC", "X"]
   ```

2. **Range validation**:
   ```json
   "validation": "range:-50:50"
   "validation": "range:0:100,gte:otherField"
   ```

3. **Format validation**:
   ```json
   "validation": "24_hour_format"
   "validation": "iso_date_format"
   "validation": "precip_code"
   ```

4. **Length validation**:
   ```json
   "max_length": 4096
   ```

## Special Field Types

### Array with structure:
```json
"avalancheProblems": {
  "value": [],
  "type": "array",
  "required": true,
  "max_items": 3,
  "item_structure": {
    // Structure of each array item
  }
}
```

### Auto-calculated fields:
```json
"hazardChart": {
  "type": "string",
  "required": true,
  "format": "JSON_string",
  "auto_calculated": true
}
```

## Question Design Principles

1. **Comprehensive**: Ask for ALL fields in one question
2. **Structured**: List what's needed in a logical order
3. **Clear options**: Include enums in the question (e.g., "Calm/Light/Moderate/Strong/Extreme")
4. **Natural flow**: Group related fields together

## Example Question Pattern

"Now I need [topic]. Please provide: [field1 with units/options], [field2 with format], [field3 with choices (option1/option2/option3)], and [optional narrative field]."

## Benefits for Prompt Caching

1. **Consistent JSON structure** - Same keys in same order
2. **Minimal dynamic content** - Only the capsule changes
3. **Predictable patterns** - Inherited fields always formatted the same
4. **Small payload** - Only essential data included

## Database Integration Points

- `is_complete: true` → Trigger next capsule creation
- `required_fields_missing` → Validation feedback to agent
- `inherited` fields → Populated from previous capsules
- `capsule_type` → Determines processing logic

This structure enables efficient prompt caching while maintaining flexibility for complex InfoEx payloads.
