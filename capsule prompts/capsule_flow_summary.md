# InfoEx Capsule Flow Summary

## Capsule Order & Dependencies

### 1. Initial Data Collection (ALWAYS FIRST)
- **File**: `initial_data_collection_capsule.json`
- **Gathers**: Date, zone, guides, times, guest count, objectives, daily summary
- **Provides to all**: obDate, locationUUIDs, operationUUID, state, times, user info

### 2. Field Summary
- **File**: `field_summary_capsule.json`
- **Gathers**: Weather observations (temp, wind, precip, sky, snow depth)
- **Inherits**: Date, times, locations, operation
- **Aurora Priority**: High - Daily operational weather

### 3. Avalanche Summary
- **File**: `avalanche_summary_capsule.json`
- **Gathers**: Overall avalanche activity assessment
- **Inherits**: Date, locations, operation
- **Aurora Priority**: Medium - General avalanche conditions

### 4. Avalanche Observation
- **File**: `avalanche_observation_capsule.json`
- **Gathers**: Specific avalanche details (if any observed)
- **Inherits**: Date, locations, operation, timezone
- **Aurora Priority**: High when avalanches observed
- **Note**: May have multiple entries

### 5. Hazard Assessment
- **File**: `hazard_assessment_capsule.json`
- **Gathers**: Hazard ratings by elevation, avalanche problems
- **Inherits**: Date, times, locations, operation, users
- **Aurora Priority**: High - Critical safety assessment

### 6. Snowpack Summary
- **File**: `snowpack_summary_capsule.json`
- **Gathers**: Overall snowpack conditions narrative
- **Inherits**: Date, time, locations, operation
- **Aurora Priority**: Medium - General conditions

### 7. Snow Profile Observation
- **File**: `snowProfile_observation_capsule.json`
- **Gathers**: Specific snow profile details (if dug)
- **Inherits**: Date, locations, operation
- **Aurora Priority**: High when profiles dug
- **Note**: May have multiple entries

### 8. Terrain Observation
- **File**: `terrain_observation_capsule.json`
- **Gathers**: Terrain choices and management
- **Inherits**: Date, locations, operation
- **Aurora Priority**: Medium - Operational decisions

### 9. PWL (Persistent Weak Layer)
- **File**: `pwl_persistent_weak_layer_capsule.json`
- **Gathers**: New PWL identification
- **Inherits**: Operation only
- **Aurora Priority**: Special - Only when new PWL identified
- **Note**: Not part of daily flow, triggered separately

## Typical Daily Flow

```
1. Initial Data Collection (Required)
   ↓
2. Field Summary (Aurora Ideal)
   ↓
3. Hazard Assessment (Aurora Ideal)
   ↓
4. Avalanche Observations (If applicable)
   ↓
5. Avalanche Summary (Aurora Ideal)
   ↓
6. Snowpack Summary (Optional but recommended)
   ↓
7. Snow Profile Observations (If profiles dug)
   ↓
8. Terrain Observation (Optional)
```

## Database Trigger Logic

When `completion_status.is_complete = true`:

1. Save current capsule data
2. Determine next capsule based on:
   - Fixed order for required capsules
   - User preferences for optional capsules
   - Skip logic (e.g., skip avalanche_observation if none observed)
3. Create new row with:
   - Next capsule type
   - Inherited fields populated
   - New fields set to null

## Inheritance Efficiency

Fields inherited by most capsules:
- `obDate` - 100% of capsules
- `operationUUID` - 100% of capsules
- `locationUUIDs` - 87.5% of capsules (all except PWL)
- `state` - 100% of capsules
- Time fields - Variable by capsule need

This inheritance pattern reduces ~25-30% of data entry across all capsules.
