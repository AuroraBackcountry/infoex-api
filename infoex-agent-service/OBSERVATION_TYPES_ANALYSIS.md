# InfoEx Observation Types Analysis

## Summary of Key Issues to Fix

### 1. **field_summary**
Common mapping issues:
- Wind speed: Natural language (e.g., "strong wind") → Code (S)
- Wind direction: Cardinal directions need proper case (e.g., "north" → "N")
- Sky conditions: Natural descriptions → Codes (e.g., "overcast" → "OVC")
- Precipitation: Natural language → OGRS codes (e.g., "light snow" → "S1")

### 2. **avalanche_observation**
Critical mappings needed:
- Trigger: Natural language → Codes (e.g., "skier triggered" → "Sa", "natural" → "Na")
- Character: Two-letter codes → Full names (e.g., "SS" → "STORM_SLAB")
- Size: Ensure numeric format (e.g., "size 2" → "2")
- Num: Handle numeric and special values
- Aspects: Arrays expected, not single values

### 3. **hazard_assessment**
Complex structure issues:
- location: Must be JSON string with proper elevation bands
- hazardChart: Must be JSON string with calculated x/y values
- distribution/sensitivity: Specific enum values
- hazardRatings: Complex nested structure by elevation
- Multiple avalanche problems array

### 4. **snowpack_summary**
Mostly free-text fields, but needs:
- Proper date formatting
- Numeric values for snow depths

### 5. **snowProfile_observation**
Complex layer structure:
- Each layer has multiple properties
- Grain forms have specific codes
- Hardness values have specific scales

### 6. **terrain_observation**
Key mappings:
- atesRating: Specific values like "Simple", "Challenging", "Complex"
- strategicMindset: Specific enum values
- terrainFeature: Specific terrain types

## Common Issues Across All Types

1. **Date Fields**: All use `obDate` not `observationDateTime`
2. **Boolean to Enum**: Many fields need conversion from yes/no to specific strings
3. **Array vs Single**: Some fields expect arrays (locationUUIDs, aspects)
4. **Case Sensitivity**: Many enums are case-sensitive
5. **Numeric Strings**: Some numeric values must be strings

## Implementation Plan

1. Extend field mappings for all types
2. Add value conversion functions for common patterns
3. Update prompts with specific guidance per type
4. Add validation for complex structures
