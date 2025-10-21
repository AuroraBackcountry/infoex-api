# Aurora to InfoEx Individual Endpoint Mapping

## Individual Endpoint Strategy

**Note**: Based on extensive API testing, InfoEx individual endpoints work reliably and are the recommended submission method. Aurora uses individual endpoint submissions for each observation type.

## Available Observation Type Payloads

The following payload templates are available in `infoex-api-payloads/`:
- `avalanche_observation.json` - Individual avalanche observations
- `avalanche_summary.json` - Avalanche activity summary
- `field_summary.json` - Daily field summary (OGRS)
- `hazard_assessment.json` - Hazard assessment with problems and ratings
- `snowProfile_observation.json` - Detailed snow profile observations
- `snowpack_summary.json` - Snowpack summary/assessment
- `terrain_observation.json` - Terrain observations
- `pwl_persistent_weak_layer.json` - Persistent weak layer creation and retrieval

Each payload file includes:
- Three-tier field approach (API Required, Aurora Ideal, Optional Bonus)
- `AURORA_IDEAL_PAYLOAD` - Recommended fields for Aurora submissions
- `COMPREHENSIVE_PAYLOAD` - Complete example with all optional fields
- LLM guidance and field constraints

## Individual Endpoint Submission Process

Aurora reports are submitted as separate API calls to individual InfoEx endpoints:

### Aurora JSON (Input)
```json
{
  "_aurora_metadata": { /* Remove this entire section */ },
  "fieldSummary": { /* Keep as-is for InfoEx */ },
  "weather": { /* Keep as-is for InfoEx */ },
  "avalancheProblems": [ /* Keep as-is for InfoEx */ ],
  "hazardAssessment": { /* Keep as-is for InfoEx */ },
  "_aurora_extensions": { /* Remove this entire section */ }
}
```

### Individual InfoEx Submissions (Output)
```bash
# 1. Field Summary
POST /observation/fieldSummary
{
  "obDate": "10/07/2025",
  "obStartTime": "08:30", 
  "obEndTime": "15:45",
  "tempHigh": 0,
  "tempLow": -2,
  "comments": "Daily operational summary",
  "locationUUIDs": ["real-staging-uuid"],
  "operationUUID": "real-operation-uuid",
  "state": "IN_REVIEW"
}

# 2. Avalanche Summary  
POST /observation/avalancheSummary
{
  "obDate": "10/07/2025",
  "avalanchesObserved": "New avalanches",
  "percentAreaObserved": 75.0,
  "comments": "Avalanche activity summary",
  "locationUUIDs": ["real-staging-uuid"],
  "operationUUID": "real-operation-uuid", 
  "state": "IN_REVIEW"
}

# 3. Hazard Assessment
POST /observation/hazardAssessment
{
  "obDate": "10/07/2025",
  "obTime": "14:00",
  "assessmentType": "Nowcast",
  "usersPresent": ["real-user-uuid"],
  "avalancheProblems": [/* problem objects */],
  "hazardRatings": [/* rating objects */],
  "locationUUIDs": ["real-staging-uuid"],
  "operationUUID": "real-operation-uuid",
  "state": "IN_REVIEW"
}
```

## Direct Field Mappings (No Transformation Needed)

### Weather Observations
| Aurora Field | InfoEx Field | Notes |
|------------------|-------------|---------------|------------------|
| `weather_observations.temperature.max_temp.value` | `tempMax` | WeatherObservationLightDTO | Direct numeric mapping |
| `weather_observations.temperature.min_temp.value` | `tempMin` | WeatherObservationLightDTO | Direct numeric mapping |
| `weather_observations.wind.direction.value` | `windDirection` | WeatherObservationLightDTO | Use OGRS code (N, NE, E, etc.) |
| `weather_observations.wind.speed.value` | `windSpeed` | WeatherObservationLightDTO | Convert to OGRS code (C, L, M, S, X, V) |
| `weather_observations.precipitation.intensity.value` | `precip` | WeatherObservationLightDTO | Use S1-S5 codes |
| `weather_observations.snow_depth.hs.value` | `hs` | WeatherObservationLightDTO | Convert to cm if needed |
| `weather_observations.snow_depth.hn24.value` | `hn24` | WeatherObservationLightDTO | Direct numeric mapping |
| `weather_observations.sky_conditions.value` | `sky` | WeatherObservationLightDTO | Use OGRS sky codes |

### Report Metadata
| Aurora Field Path | InfoEx Field | InfoEx Schema | Conversion Notes |
|------------------|-------------|---------------|------------------|
| `report_header.date.value` | `obDate` | All schemas | Convert YYYY-MM-DD → yyyy/mm/dd |
| `report_header.zone.value` | `locationUUIDs` | All schemas | Resolve zone name to UUID array |
| `operational_summary.start_time.value` | `obTime` | All schemas | Use HH:MM format |
| `operational_summary.summary.value` | `comments` | FieldSummaryLightDTO | Narrative text |

### Avalanche Problems
| Aurora Field Path | InfoEx Field | InfoEx Schema | Conversion Notes |
|------------------|-------------|---------------|------------------|
| `avalanche_problems.problems[].type.value` | `character` | AvalancheProblemDTO | Map to ENUM (STORM_SLAB, etc.) |
| `avalanche_problems.problems[].location.value` | `location` | AvalancheProblemDTO | Direct text mapping |
| `avalanche_problems.problems[].distribution.value` | `distribution` | AvalancheProblemDTO | Direct mapping (Isolated, Specific, Widespread) |
| `avalanche_problems.problems[].likelihood.value` | `sensitivity` | AvalancheProblemDTO | Map Unlikely→Unreactive, Possible→Stubborn, etc. |
| `avalanche_problems.problems[].size.value` | `typicalSize` | AvalancheProblemDTO | Map 1→Size1, 1.5→Size15, etc. |

### Hazard Assessment
| Aurora Field Path | InfoEx Field | InfoEx Schema | Conversion Notes |
|------------------|-------------|---------------|------------------|
| `hazard_assessment.alpine.value` | `hazardRatings[0].hazardRating` | HazardAssessmentDTO | Create array entry with elevationBand: "ALP" |
| `hazard_assessment.treeline.value` | `hazardRatings[1].hazardRating` | HazardAssessmentDTO | Create array entry with elevationBand: "TL" |
| `hazard_assessment.below_treeline.value` | `hazardRatings[2].hazardRating` | HazardAssessmentDTO | Create array entry with elevationBand: "BTL" |

### Avalanche Observations (Conditional)
| Aurora Field Path | InfoEx Field | InfoEx Schema | Conversion Notes |
|------------------|-------------|---------------|------------------|
| `avalanche_observations.avalanche_details.num.value` | `num` | AvalancheObservationLightDTO | Convert integer to string |
| `avalanche_observations.avalanche_details.type.value` | `character` | AvalancheObservationLightDTO | Map to ENUM values |
| `avalanche_observations.avalanche_details.trigger.value` | `trigger` | AvalancheObservationLightDTO | Map to trigger codes (Na, Sa, etc.) |
| `avalanche_observations.avalanche_details.size.value` | `sizeMin` | AvalancheObservationLightDTO | Direct numeric mapping |
| `avalanche_observations.avalanche_details.failure_plane.value` | `grainForm` | AvalancheObservationLightDTO | Map to OGRS grain form codes |

## Conversion Functions Required

### 1. Date Format Conversion
```javascript
function convertDateFormat(isoDate) {
  // "2025-02-21" → "2025/02/21"
  return isoDate.replace(/-/g, '/');
}
```

### 2. Zone to UUID Resolution
```javascript
function resolveZoneToUUID(zoneName) {
  const zoneMapping = {
    "Whistler Blackcomb": ["uuid-whistler-blackcomb"],
    "Duffey, Cayoosh": ["uuid-duffey", "uuid-cayoosh"],
    "Sea to Sky Gondola (STSG)": ["uuid-stsg"]
  };
  return zoneMapping[zoneName] || [];
}
```

### 3. Avalanche Character Mapping
```javascript
function mapAvalancheCharacter(auroraType) {
  const mapping = {
    "Storm Slabs": "STORM_SLAB",
    "Wind Slabs": "WIND_SLAB", 
    "Persistent Slabs": "PERSISTENT_SLAB",
    "Deep Persistent Slabs": "DEEP_PERSISTENT_SLAB",
    "Wet Avalanches": "WET_SLAB",
    "Loose Wet": "LOOSE_WET_AVALANCHE",
    "Loose Dry": "LOOSE_DRY_AVALANCHE",
    "Cornice Fall": "CORNICE"
  };
  return mapping[auroraType] || "UNKNOWN";
}
```

### 4. Likelihood to Sensitivity Mapping
```javascript
function mapLikelihoodToSensitivity(likelihood) {
  const mapping = {
    "Unlikely": "Unreactive",
    "Possible": "Stubborn", 
    "Likely": "Reactive",
    "Certain": "Touchy"
  };
  return mapping[likelihood] || "Stubborn";
}
```

### 5. Size Scale Conversion
```javascript
function mapAvalancheSize(auroraSize) {
  const mapping = {
    1: "Size1", 1.5: "Size15", 2: "Size2", 2.5: "Size25",
    3: "Size3", 3.5: "Size35", 4: "Size4", 4.5: "Size45", 5: "Size5"
  };
  return mapping[auroraSize] || "Size1";
}
```

### 6. Wind Speed Conversion
```javascript
function mapWindSpeed(auroraSpeed) {
  if (auroraSpeed.toLowerCase().includes('calm')) return 'C';
  if (auroraSpeed.toLowerCase().includes('light')) return 'L';
  if (auroraSpeed.toLowerCase().includes('moderate')) return 'M';
  if (auroraSpeed.toLowerCase().includes('strong')) return 'S';
  if (auroraSpeed.toLowerCase().includes('extreme')) return 'X';
  return 'V'; // Variable/unknown
}
```

## InfoEx Submission Sequence

### Recommended Order for Aurora Daily Reports
1. **Field Summary** (`POST /observation/fieldSummary`) - Comprehensive daily overview with weather
2. **Avalanche Summary** (`POST /observation/avalancheSummary`) - Overview of avalanche activity (if applicable)
3. **Snowpack Summary** (`POST /observation/snowpackAssessment`) - General snowpack conditions
4. **Snow Profile Observation** (`POST /observation/snowpack`) - Detailed profile data (if collected)
5. **Avalanche Observation** (`POST /observation/avalanche`) - Individual avalanche details (if observed)
6. **Hazard Assessment** (`POST /observation/hazardAssessment`) - Formal hazard rating with problems
7. **Terrain Observation** (`POST /observation/terrain`) - Terrain considerations and ATES ratings
8. **PWL Creation** (`POST /pwl`) - Persistent weak layer tracking (seasonal, 2-3 times per season)

**Note**: Aurora does not submit weather observations (`POST /observation/weather`) as it's not a weather station operation. Weather data is captured in the field summary instead.

### Batch Submission Strategy
```javascript
async function submitAuroraReportToInfoEx(auroraReport) {
  const submissions = [];
  
  // 1. Weather observation
  submissions.push(await submitWeatherObservation(auroraReport));
  
  // 2. Field summary
  submissions.push(await submitFieldSummary(auroraReport));
  
  // 3. Avalanche problems (multiple)
  for (const problem of auroraReport.avalanche_problems.problems) {
    submissions.push(await submitAvalancheProblem(problem, auroraReport));
  }
  
  // 4. Hazard assessment
  submissions.push(await submitHazardAssessment(auroraReport));
  
  // 5. Avalanche observations (conditional)
  if (auroraReport.avalanche_observations.evidence_of_instability.observed) {
    submissions.push(await submitAvalancheObservation(auroraReport));
  }
  
  // 6. General message
  submissions.push(await submitGeneralMessage(auroraReport));
  
  return submissions;
}
```

## Validation Checklist

### Pre-Submission Validation
- [ ] All required InfoEx fields populated
- [ ] Zone names resolved to valid UUIDs
- [ ] Enum values match InfoEx constants
- [ ] Date formats converted correctly
- [ ] Numeric ranges within acceptable bounds
- [ ] Conditional fields handled properly

### Post-Submission Validation
- [ ] All API calls returned success (200)
- [ ] No validation errors in response
- [ ] Observation UUIDs captured for reference
- [ ] Audit trail created for traceability

---

*This field mapping table provides the exact conversions needed to transform Aurora daily operational reports into InfoEx API submissions.*
