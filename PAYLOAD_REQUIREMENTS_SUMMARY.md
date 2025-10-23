# InfoEx Payload Requirements Summary

Based on analysis of the InfoEx API payloads and test scripts, here are the exact requirements for each observation type:

## Common Fields (All Observations)
- **obDate**: MM/DD/YYYY format (e.g., "10/23/2025")
- **locationUUIDs**: Array of strings (even if just one location)
- **operationUUID**: String (your operation ID)
- **state**: "IN_REVIEW" for testing, "SUBMITTED" for production

## 1. Avalanche Summary
**Required Fields:**
- `obDate`
- `avalanchesObserved`: Must be one of:
  - "New avalanches"
  - "No new avalanches" 
  - "Sluffing/Pinwheeling only"
- `locationUUIDs`, `operationUUID`, `state`

**Optional but Recommended:**
- `percentAreaObserved`: Number 0-100
- `comments`: String description

**Aurora Ideal Example:**
```json
{
  "obDate": "10/21/2025",
  "avalanchesObserved": "New avalanches",
  "percentAreaObserved": 20.0,
  "comments": "Observed three avalanches in the distance in alpine terrain...",
  "locationUUIDs": ["uuid"],
  "operationUUID": "uuid",
  "state": "IN_REVIEW"
}
```

## 2. Field Summary
**Required Fields:**
- `obDate`
- `obStartTime`: HH:MM format (e.g., "08:30")
- `obEndTime`: HH:MM format (e.g., "16:00")
- `tempHigh`: Number (Celsius)
- `tempLow`: Number (Celsius)
- `locationUUIDs`, `operationUUID`, `state`

**Optional but Useful:**
- `comments`: String description
- Weather data (hn24, windSpeed, etc.)

**Aurora Ideal Example:**
```json
{
  "obDate": "10/21/2025",
  "obStartTime": "08:00",
  "obEndTime": "16:00",
  "tempHigh": 0,
  "tempLow": -2,
  "comments": "Excellent skiing conditions above 1500m...",
  "locationUUIDs": ["uuid"],
  "operationUUID": "uuid",
  "state": "IN_REVIEW"
}
```

## 3. Avalanche Observation
**Required Fields:**
- `obDate`
- `obTime`: HH:MM format
- `num`: String (usually "1")
- `trigger`: Enum values:
  - "Na" (Natural)
  - "Sa" (Skier accidental)
  - "Ss" (Skier intentional)
  - etc.
- `character`: Enum values:
  - "STORM_SLAB"
  - "WIND_SLAB"
  - "PERSISTENT_SLAB"
  - etc.
- `locationUUIDs`, `operationUUID`, `state`

**Size (one of these required):**
- `size`: String ("1", "1.5", "2", etc.)
- OR `sizeMin` and `sizeMax`: Numbers

**Aspect/Elevation (recommended):**
- `aspectFrom`, `aspectTo`: "N", "NE", "E", etc.
- `elevationMin`, `elevationMax`: Numbers in meters

**Aurora Ideal Example:**
```json
{
  "obDate": "10/21/2025",
  "obTime": "13:00",
  "num": "1",
  "trigger": "Sa",
  "character": "STORM_SLAB",
  "sizeMin": 1.5,
  "sizeMax": 1.5,
  "aspectFrom": "N",
  "aspectTo": "NE",
  "elevationMin": 1500,
  "elevationMax": 1800,
  "comments": "Storm slab triggered by skier...",
  "locationUUIDs": ["uuid"],
  "operationUUID": "uuid",
  "state": "IN_REVIEW"
}
```

## 4. Hazard Assessment
**Required Fields:**
- `obDate`
- `obTime`: HH:MM format
- `assessmentType`: Usually "Forecast"
- `hazardRatings`: Array with 3 elevation bands:
  ```json
  [
    {"elevationBand": "Alpine", "rating": 3},
    {"elevationBand": "Treeline", "rating": 2},
    {"elevationBand": "Below Treeline", "rating": 1}
  ]
  ```
- `avalancheProblems`: Array of problems (see below)
- `locationUUIDs`, `operationUUID`, `state`

**Avalanche Problem Structure:**
```json
{
  "obDate": "10/21/2025",
  "character": "STORM_SLAB",
  "location": "{\"Alpine\":[\"N\",\"NE\"],\"Treeline\":[\"N\"],\"Below Treeline\":[]}",
  "hazardChart": "{\"x\":{\"typical\":2,\"min\":1,\"max\":3},\"y\":{\"typical\":4,\"min\":3,\"max\":5}}",
  "distribution": "Widespread",
  "sensitivity": "Reactive",
  "typicalSize": "Size2",
  "comment": "Storm slabs on north aspects...",
  "locationUUIDs": ["uuid"],
  "operationUUID": "uuid",
  "state": "IN_REVIEW"
}
```

## Key Differences from n8n Instructions

1. **Enums are specific**: 
   - Triggers: "Na", "Sa", not "Natural", "Skier accidental"
   - Character: "STORM_SLAB", not "Storm Slab"
   - Sizes: "Size2" or just "2" depending on field

2. **JSON strings for complex data**:
   - Hazard problem `location` is a JSON string
   - Hazard problem `hazardChart` is a JSON string

3. **Arrays always required**:
   - `locationUUIDs` must be an array even with one location
   - `hazardRatings` must include all three elevation bands
   - `avalancheProblems` is an array of problem objects

## Test Script Pattern
All test scripts:
1. Load the AURORA_IDEAL_PAYLOAD from the JSON file
2. Send with proper headers (api_key, operation, Content-Type)
3. Check for 200 status and extract UUID from response

This is what the Claude agent needs to produce - exact field names and proper enum values!
