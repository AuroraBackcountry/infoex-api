# Separation of Concerns: Capsules vs AURORA_IDEAL

## Overview

The Aurora InfoEx reporting system maintains a clear separation between data collection (capsules) and API submission (AURORA_IDEAL payloads).

## 1. Dialogue Agent & Capsules

**Purpose**: Conversational data gathering and light processing

### Capsule Structure
```json
{
  "capsule_type": "field_summary",
  "question": "User-friendly question",
  "payload": {
    // Can contain both:
    // - InfoEx-ready field names (obDate, tempHigh)
    // - Additional context not for InfoEx
    // - User-friendly aliases
  },
  "completion_status": {
    "is_complete": false,
    "required_missing": []
  }
}
```

### Key Characteristics
- **Flexible structure** - Can store any data needed for conversation
- **Light validation** - Basic checks during data entry
- **User-friendly** - Questions and responses in natural language
- **Stores everything** - Both InfoEx fields and additional context

### Inherited Values
Values that flow between capsules via Supabase triggers:
- `obDate` - Report date
- `operationUUID` - Organization identifier
- `locationUUIDs` - Zone identifiers
- Guide names and other context

## 2. InfoEx Agent Service & AURORA_IDEAL

**Purpose**: Strict API validation and submission

### AURORA_IDEAL Payload
Located in: `infoex-agent-service/data/aurora_templates/`

Represents exactly what Aurora Backcountry submits to InfoEx:
- All required fields
- Selected optional fields that Aurora uses
- Proper InfoEx field names and formats

### Key Characteristics
- **Strict structure** - Must match InfoEx API exactly
- **Full validation** - Claude ensures all fields are correct
- **API-ready** - Direct submission to InfoEx endpoints
- **Error handling** - Retry logic for failed submissions

## 3. Data Flow

```
1. DIALOGUE PHASE (Capsules)
   User Input → Capsule Questions → Light Validation → Postgres Storage
   
2. MARKDOWN GENERATION
   Capsule Data → OGRS Translation → Human-Readable Report
   Example: HN24: 30 → "30 cm of snow fell in the last 24 hours"
   
3. API SUBMISSION (On Trigger)
   Capsule Data → Create AURORA_IDEAL → Claude Validation → InfoEx API
```

## 4. Validation Strategy

### Stage 1: Dialogue Validation (Light)
- Required fields present
- Basic format checks
- User-friendly error messages
- Allow flexibility for conversation flow

### Stage 2: API Validation (Strict)
- Exact InfoEx field requirements
- OGRS code compliance
- Enum value validation
- Retry with modifications on failure

## 5. Documentation Guidelines

### Capsule Documentation Should:
- Focus on conversation flow
- Explain inherited value patterns
- Document flexible data storage
- Use user-friendly terminology

### InfoEx Agent Documentation Should:
- Reference AURORA_IDEAL payloads
- Detail strict validation rules
- Explain retry strategies
- Use exact InfoEx terminology

## 6. Why This Separation?

1. **User Experience**: Natural conversation without rigid API constraints
2. **Data Integrity**: Strict validation only where needed (API submission)
3. **Flexibility**: Capsules can evolve without breaking API integration
4. **Error Recovery**: Claude can fix issues without bothering users
5. **Maintainability**: Changes to dialogue don't affect API integration

## Example: Temperature Field

### In Capsule (Flexible)
```json
"temperature": {
  "high": -2,
  "low": -8,
  "user_said": "it was cold, maybe minus 8 at the coldest",
  "notes": "measured at 2000m"
}
```

### In AURORA_IDEAL (Strict)
```json
{
  "tempHigh": -2,
  "tempLow": -8
}
```

The capsule stores context and natural language, while AURORA_IDEAL contains only what InfoEx needs.

---

*This separation ensures a smooth user experience while maintaining strict API compliance.*
