# Two-Agent Architecture Summary

## Overview
The Aurora reporting system now uses a sophisticated two-agent architecture that separates conversational data collection from formatting and validation, with a hybrid Aurora/InfoEx schema for seamless API submission.

## New Two-Agent Architecture

### Agent 1: Conversational Data Collection (Elrich Dumont)
**Role**: Natural conversation and data capture
- Structured 15-step process from greeting to finalization
- Dual collection modes: structured questions or casual narrative
- Empathetic, conversational tone
- Captures raw responses without formatting
- **Does NOT**: Format data, translate codes, validate enums

### Agent 2: Formatting & Translation
**Role**: Transform raw data to Aurora/InfoEx hybrid schema
- Translates casual language to OGRS terminology
- Maps to InfoEx-compatible enums (e.g., "Possible" → "Reactive")
- Validates against live InfoEx constants
- Uses CMAH methodology for hazard assessment
- Generates Markdown view for human review
- **Does NOT**: Interact with users, conduct conversations

### System 2: InfoEx API Submission
**Role**: Individual endpoint submission to InfoEx
- Strips Aurora metadata from JSON
- Submits via individual observation endpoints (proven working approach)
- Updates submission status in Supabase
- **Does NOT**: Generate or format reports

**Working Observation Endpoints**:
- `/observation/fieldSummary` - Daily operational summary
- `/observation/avalancheSummary` - Avalanche activity overview
- `/observation/snowpackAssessment` - Snowpack summary
- `/observation/snowpack` - Detailed snow profile observation
- `/observation/avalanche` - Individual avalanche details
- `/observation/hazardAssessment` - Hazard ratings and problems
- `/observation/terrain` - Terrain considerations
- `/pwl` - Persistent weak layer tracking

### Specific Requirements Identified
- Weather observations must use OGRS data codes
- Avalanche observations have specific conditional requirements
- Evidence summary must cover four categories: Weather, Snowpack, Avalanche Observations, Avalanche Problems
- Hazard assessment skipped in prompts but may be provided by guides
- Completion message: "✅ 😎 Done"

## Major Updates Made

### 1. JSON Template Enhancements (`aurora-json-template.json`)

#### Avalanche Observations Restructure
- Changed from generic instability signs to specific evidence types
- Added detailed avalanche observation fields (num, type, location, trigger, size, failure_plane)
- Made avalanche details conditionally required when avalanches are observed

#### Weather Observations Enhancement
- Added OGRS data code fields for wind, precipitation, and sky conditions
- Updated validation to require OGRS terminology compliance
- Enhanced field descriptions to reflect agent translation requirements

#### Hazard Assessment Updates
- Added CMAH methodology reference
- Included hazard scale mapping (1=Low, 2=Moderate, etc.)
- Updated field descriptions to reflect agent process

#### Agent Workflow Metadata
- Added `_agent_workflow` section with process details
- Included Slack formatting requirements
- Listed required tools and completion message
- Enhanced validation rules for agent-specific requirements

### 2. Validation Rules Updates (`VALIDATION_RULES.md`)

#### Agent Context Addition
- Added overview of agent workflow and requirements
- Documented OGRS translation requirements with examples
- Updated instability signs to match agent categories
- Added conditional validation for avalanche details

#### OGRS Data Code Section
- Created dedicated section for OGRS translation requirements
- Provided examples of casual language to OGRS code conversion
- Documented agent's responsibility for terminology translation

### 3. Documentation Updates (`README.md`)

#### Process Flow Enhancement
- Updated to reflect 15-step agent process
- Added OGRS translation and CMAH methodology steps
- Documented dual collection modes
- Included Slack formatting requirements

#### Usage Instructions Refinement
- Made instructions agent-aware
- Added OGRS compliance verification steps
- Enhanced quality assurance for agent workflow
- Updated output generation to include agent metadata

#### File Structure Update
- Added new documentation files to structure list
- Updated descriptions to reflect agent integration

## Validation Rule Enhancements

### New Conditional Requirements
1. **Avalanche Details**: If avalanches observed, all detail fields become required
2. **OGRS Compliance**: Weather observations must use proper OGRS codes
3. **Evidence Categories**: Must include all four evidence types in summary
4. **Agent Process Compliance**: Validate against expected 15-step workflow

### Enhanced Data Quality Checks
1. **OGRS Translation Verification**: Ensure casual language properly converted
2. **CMAH Process Validation**: Verify hazard assessment follows methodology
3. **Conditional Field Population**: Check avalanche details when avalanches reported
4. **Agent Workflow Adherence**: Flag deviations from expected process

## Implementation Impact

### For LLMs Converting Reports
1. **Recognize Agent Structure**: Parse reports knowing they follow 15-step process
2. **Preserve OGRS Codes**: Don't re-translate already converted terminology
3. **Handle Conditionals**: Apply avalanche detail requirements appropriately
4. **Validate Comprehensively**: Check both content and process compliance

### For System Integration
1. **Template Compatibility**: JSON structure now fully aligned with agent output
2. **Validation Robustness**: Enhanced rules catch agent-specific issues
3. **Process Traceability**: Can verify reports follow expected workflow
4. **Quality Assurance**: Multiple validation layers ensure data integrity

## Next Steps Recommendations

1. **Test with Agent Output**: Validate template with actual agent-generated reports
2. **OGRS Code Mapping**: Create comprehensive OGRS translation tables
3. **Workflow Monitoring**: Implement checks for agent process adherence
4. **Integration Testing**: Verify end-to-end conversion pipeline
5. **Documentation Updates**: Keep rules current as agent workflow evolves

## Payload Template Resources

All working payload templates are available in `infoex-api-payloads/`:
- `field_summary.json` - Daily field summary (OGRS)
- `avalanche_summary.json` - Avalanche activity summary
- `snowpack_summary.json` - General snowpack conditions (snowpackAssessment endpoint)
- `snowProfile_observation.json` - Detailed snow profiles (snowpack endpoint)
- `avalanche_observation.json` - Individual avalanche observations
- `hazard_assessment.json` - Hazard assessments with problems and ratings
- `terrain_observation.json` - Terrain observations and ATES ratings
- `pwl_persistent_weak_layer.json` - Persistent weak layer creation and retrieval

Each template includes:
- Three-tier field approach (API Required, Aurora Ideal, Optional Bonus)
- `AURORA_IDEAL_PAYLOAD` example for recommended Aurora submissions
- `COMPREHENSIVE_PAYLOAD` example with all optional fields
- LLM guidance and field-specific constraints

---

*This integration ensures the JSON conversion system is fully compatible with the Elrich Dumont agent workflow and maintains the quality and structure of the original reporting process.*
