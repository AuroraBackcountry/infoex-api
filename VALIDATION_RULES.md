# Validation Rules and Standards Reference

## Overview
This document provides detailed validation rules for the two-agent Aurora reporting system, based on OGRS standards, InfoEx guidelines, and Canadian Avalanche Association practices.

## Two-Agent Architecture Context
The reports are generated through a two-agent system:

### Agent 1: Conversational Data Collection (Elrich Dumont)
- Guides users through structured 15-step process
- Captures raw conversational responses
- Does NOT format or validate data
- Focuses on natural conversation flow

### Agent 2: Formatting & Translation
- Translates casual language to OGRS terminology
- Maps responses to InfoEx-compatible enums
- Validates against database-stored InfoEx constants
- Generates Aurora/InfoEx hybrid JSON
- Creates Markdown view for human review
- Uses CMAH (Conceptual Model of Avalanche Hazard) for hazard assessment

## Field-Specific Validation Rules

### Date and Time Fields

#### Date Format
- **Required Format**: MM/DD/YYYY (month/day/year)
- **Input Variations**: 
  - `2025-02-21` → `02/21/2025`
  - `2025/02/21` → `02/21/2025`
  - `21-02-2025` → `02/21/2025`
- **Validation**: Must be a valid calendar date
- **Range**: Typically within 7 days of current date for operational reports
- **API Error**: "must have format of mm/dd/yyyy" if incorrect format used

#### Time Format
- **Required Format**: 24-hour format (HH:MM)
- **Examples**: `08:30`, `14:00`, `15:45`
- **Validation**: Hours 00-23, Minutes 00-59

### Geographic and Location Fields

#### Zone Names

**Data Sources**:
- **Primary Source**: InfoEx API GET `/location` endpoint
- **Secondary Source**: Supabase database with synchronized zone data

**Zone Structure**:
1. **Zone Name**: Official operational area name (e.g., "Sea to Sky Gondola", "Glacier National Park")
2. **Zone UUID**: Unique identifier assigned by InfoEx system
3. **Sub-locations**: Specific areas within a zone stored as JSONB in Supabase

**Sub-location Examples**:

*Sea to Sky Gondola Zone*:
- Exit Gully
- Ledge Trees
- Cleavage Couloir

*Glacier National Park Zone*:
- Video Peak
- Balu Pass
- Asulkan Drainage
- Rogers Pass

**Data Management**:
- Zones can be added, modified, or deleted in InfoEx
- Changes are synchronized to Supabase database
- Sub-locations are managed independently in Supabase

**Validation Rules**:
- Zone name must match exactly with InfoEx-approved operational areas
- Zone UUID must be valid and active in InfoEx system
- Sub-locations must belong to their parent zone
- Case-sensitive matching for zone names

#### Elevation References
- **Format**: Integer values in meters
- **Common Thresholds**: 1200m, 1500m, 1800m, 1900m, 2400m
- **Parsing Patterns**:
  - `above 1500 meters` → 1500
  - `below 1500 m` → 1500
  - `> 1800 m` → 1800
  - `up to 2400m` → 2400

### Weather Observation Standards

#### Wind Direction
- **Allowed Values**: N, NE, E, SE, S, SW, W, NW
- **Input Variations**:
  - `south` → `S`
  - `west` → `W`
  - `Light W` → direction: `W`, speed: `Light`

#### Wind Speed Descriptors
- **Standard Terms**: Light, Moderate, Strong
- **Qualifiers**: Can be combined (e.g., "Strong to moderate")
- **Location Qualifiers**: "at ridge tops", "in the alpine"

#### Temperature
- **Units**: Celsius (°C)
- **Range**: -40°C to +40°C (reasonable mountain range)
- **Validation**: min_temp ≤ max_temp
- **Format**: Integer or decimal values

#### Precipitation
- **Types**: NIL, Snowing, Rain, Mixed
- **Intensity Codes**: S1, S2, S3, S4, S5, S6, S7, S8, S9, S10 (InfoEx standard)
- **Parsing**: Extract intensity from phrases like "Snowing at S2 intensity"

#### Snow Depth
- **HS (Height of Snow)**: Total snow depth
  - Units: cm or m (convert m to cm: 2m → 200cm)
  - Range: 0-1000cm typical
  - Measured vertically from ground to snow surface
- **HN24**: New snow in 24 hours
  - Units: cm
  - Range: 0-100cm typical
  - Per OGRS standards: May exceed HS in early season conditions
  - Measured on 24-hour board, cleared after morning observation

#### Sky Conditions
- **Standard Terms**: Clear, BKN (Broken), Overcast, Obscure
- **Input Variations**: 
  - `Clear skies` → `Clear`
  - `Overcast to obscure` → `Overcast`
- **OGRS Data Codes**: Agent must translate to proper OGRS sky cover codes

## OGRS Data Code Translation Requirements

### Weather Observation Translation
The agent (Elrich Dumont) is required to translate casual language to OGRS terminology:

#### Wind Translation Examples
- `Strong to moderate at ridge tops from the south` → 
  - Direction: `S`
  - Speed: OGRS wind speed code
  - Location: `ridge tops`

#### Precipitation Translation Examples  
- `Snowing at S2 intensity` →
  - Type: `Snowing`
  - Intensity: `S2`
  - OGRS Code: Complete OGRS precipitation data code

#### Sky Cover Translation Examples
- `Overcast to obscure` → OGRS sky cover data code
- `Clear skies` → OGRS clear sky code

### Avalanche Problem Standards

#### Problem Types
**Allowed Values**:
- Storm Slabs
- Wind Slabs  
- Persistent Slabs
- Deep Persistent Slabs
- Wet Avalanches
- Loose Wet
- Loose Dry
- Cornice Fall

#### Distribution
**Allowed Values**:
- Specific
- Isolated  
- Widespread

#### Likelihood
**Allowed Values** (in order):
- Unlikely
- Possible
- Likely
- Certain

#### Size Scale
**Allowed Values**: 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5
- **Size 1**: Relatively harmless to people (sluff)
- **Size 1.5**: Could bury, injure, or kill a person
- **Size 2**: Could bury, injure, or kill a person
- **Size 2.5**: Could bury and destroy a car, damage a truck, destroy a wood frame house, or break a few trees
- **Size 3**: Could bury and destroy a car, damage a truck, destroy a wood frame house, or break a few trees
- **Size 3.5**: Could destroy a railway car, large truck, several buildings, or a forest area up to 4 hectares
- **Size 4**: Could destroy a railway car, large truck, several buildings, or a forest area up to 4 hectares
- **Size 4.5**: Largest snow avalanche known; could destroy a village or forest of 40 hectares
- **Size 5**: Largest snow avalanche known; could destroy a village or forest of 40 hectares

### Hazard Assessment Scale

#### Standard Scale (1-5)
- **1 - Low (Green)**: Generally safe avalanche conditions
- **2 - Moderate (Yellow)**: Heightened awareness is needed
- **3 - Considerable (Orange)**: Dangerous avalanche conditions
- **4 - High (Red)**: Very dangerous avalanche conditions
- **5 - Extreme (Black)**: Avoid avalanche terrain

#### Elevation Band Logic
**Typical Pattern**: Alpine ≥ Treeline ≥ Below Treeline
- Alpine hazard is often highest due to wind loading and exposure
- Below treeline is often lowest due to anchoring and protection
- Exceptions exist based on specific conditions

### Instability Signs (Agent-Specific)

#### Evidence of Instability Types
The agent uses specific categories for instability evidence:
- **Avalanche**: Actual avalanche observed
- **Cracking**: Shooting cracks from skis/boots  
- **Whumpfing**: Collapsing sounds in snowpack
- **Active Ski Cut**: Intentional ski cutting results
- **None**: No instability evidence observed

#### Avalanche Detail Requirements
If avalanches are observed, ALL of the following fields become required:
- **Num**: Number of avalanches (integer)
- **Type**: Avalanche character type
- **Location**: Location description
- **Trigger**: Trigger type that caused avalanche
- **Size**: Size on standard 1-5 scale (including half sizes)
- **Failure Plane**: Layer the avalanche failed on

### Strategic Mindset Categories

#### Approved Categories
- **Status Quo**: Normal operations with standard precautions
- **Maintenance**: Maintaining current approach with minor adjustments
- **Entrenchment**: Digging in and holding position due to conditions
- **Stepping Out**: Gradually expanding operational terrain
- **Open Season**: Full terrain utilization with good conditions
- **Assessment**: Evaluating conditions before committing
- **Stepping Back**: Reducing terrain exposure due to concerns
- **Spring Diurnal**: Focus on timing and solar aspects

## Data Quality Checks

### Completeness Validation
**Required Sections**:
- Report header (date, zone, guides)
- Operational summary
- Snow conditions description
- Hazard assessment (all three elevation bands)
- Evidence summary (all four categories)
- Risk management strategies
- Strategic mindset
- Forecast expectations

### Consistency Validation
1. **Temperature Logic**: min_temp ≤ max_temp
2. **Hazard Progression**: Check elevation band logic
3. **Problem Alignment**: Avalanche problems should support hazard ratings
4. **Evidence Coherence**: Evidence should support conclusions
5. **Time Sequence**: start_time < end_time

### Format Validation
1. **Numeric Ranges**: All numeric values within reasonable bounds
2. **Enum Values**: All categorical values from approved lists
3. **Date/Time**: Proper formatting and valid values
4. **Array Limits**: Maximum 3 avalanche problems per report

## Error Handling Guidelines

### Missing Required Fields
- Flag as validation error
- Provide specific field name and requirement
- Suggest default values where appropriate

### Invalid Values
- Reject with specific error message
- Provide list of valid alternatives
- Suggest closest valid match when possible

### Format Errors
- Attempt automatic correction (e.g., date format conversion)
- Flag successful corrections for review
- Reject if automatic correction not possible

### Logical Inconsistencies
- Flag for manual review
- Provide explanation of the inconsistency
- Suggest resolution options

## InfoEx Integration Notes

### API Compatibility
- Ensure all fields map to InfoEx submission format
- Maintain traceability to source Markdown sections
- Include metadata for audit trails

### Submission States
- **IN_REVIEW**: For reports requiring validation
- **SUBMITTED**: For completed, validated reports

### InfoEx Observation Types
Aurora submits the following observation types to InfoEx:
1. **Field Summary** (`/observation/fieldSummary`) - Daily operational report INCLUDING weather observations
2. **Avalanche Summary** (`/observation/avalancheSummary`) - Avalanche activity overview
3. **Snowpack Summary** (`/observation/snowpackAssessment`) - General snowpack conditions
4. **Snow Profile Observation** (`/observation/snowpack`) - Detailed snow profiles
5. **Avalanche Observation** (`/observation/avalanche`) - Individual avalanche details
6. **Hazard Assessment** (`/observation/hazardAssessment`) - Hazard ratings and problems
7. **Terrain Observation** (`/observation/terrain`) - Terrain considerations
8. **PWL** (`/pwl`) - Persistent weak layer tracking

**Important Clarification**: 
- Aurora submits **field observations** which INCLUDE weather data via `/observation/fieldSummary`
- Aurora does NOT use `/observation/weather` endpoint (reserved for automated weather stations)
- Field observations are guide-based and include weather as part of operational context
- Weather stations submit continuous automated data to `/observation/weather`

### Payload Templates
All working payload templates are available in `infoex-api-payloads/`:
- `field_summary.json`
- `avalanche_summary.json`
- `snowpack_summary.json` (for general snowpack assessment)
- `snowProfile_observation.json` (for detailed snow profiles)
- `avalanche_observation.json`
- `hazard_assessment.json`
- `terrain_observation.json`
- `pwl_persistent_weak_layer.json`

Each template includes three-tier field approach: API Required, Aurora Ideal, and Optional Bonus fields.

---

*This document should be updated as standards evolve and new validation requirements are identified.*
