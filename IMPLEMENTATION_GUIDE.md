# Implementation Guide for Aurora Reporting System

## Quick Start for Two-Agent Architecture

This guide provides implementation instructions for the Aurora two-agent reporting system that transforms conversational avalanche reports into InfoEx-compatible structured data.

## System Architecture

### System 1: Report Generation
1. **`agent_system_prompt_report_process.md`** - Agent 1 & 2 workflows
2. **`aurora-json-template.json`** - Aurora/InfoEx hybrid schema
3. **`VALIDATION_RULES.md`** - Two-agent validation rules
4. **`OGRS.txt`** - Official Guidelines for Reporting Standards

### System 2: InfoEx Submission  
5. **`FIELD_MAPPING_TABLE.md`** - Individual endpoint field mapping guide
6. **`INFOEX_API_REFERENCE.md`** - Complete InfoEx API documentation
7. **`infoex-api-docs.json`** - InfoEx API schema
8. **`infoex-api-payloads/`** - Working payload templates for each observation type
9. **`env.example`** - Environment configuration for staging/production

### Supporting Documentation
10. **`README.md`** - Overall system architecture
11. **`AGENT_INTEGRATION_SUMMARY.md`** - Two-agent workflow details
12. **`markdown-examples/`** - Sample reports for reference

## Conversion Process

### Step 1: Parse Markdown Structure
1. Identify report sections by headers
2. Extract key-value pairs from structured sections
3. Capture narrative text for summary fields

### Step 2: Apply Data Transformations
1. **Dates**: Convert to ISO 8601 format (YYYY-MM-DD)
2. **Temperatures**: Extract numeric values, preserve Celsius units
3. **Elevations**: Convert to meters, extract thresholds
4. **Wind**: Parse direction and speed components
5. **Snow depths**: Convert to centimeters (m → cm × 100)

### Step 3: Validate Against Standards
1. Check required fields are present
2. Verify values against allowed lists
3. Ensure logical consistency (temp ranges, hazard progression)
4. Validate format compliance

### Step 4: Generate JSON Output
1. Populate template with extracted values
2. Include validation metadata
3. Flag any issues or assumptions made

## Critical Validation Points

### Must-Have Fields
- Date (ISO format)
- Zone (from approved list)
- At least one guide name
- Hazard ratings for all three elevation bands
- Evidence summary (all four categories)

### Common Parsing Challenges
1. **Multiple date formats**: Handle `/` and `-` separators
2. **Temperature negatives**: Properly parse `-7°C`
3. **Elevation references**: Extract from phrases like "above 1500m"
4. **Wind descriptions**: Split direction from speed
5. **Avalanche problems**: Parse multi-line structured data

### Quality Assurance Checks
- Temperature logic: min ≤ max
- Hazard progression: typically Alpine ≥ Treeline ≥ BTL
- Problem limits: Maximum 3 avalanche problems
- Size scale: Only use 1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5, 5

## Example Conversion Workflow

```
Input Markdown → Parse Sections → Extract Data → Validate → Output JSON
     ↓              ↓              ↓           ↓         ↓
   report_1.md → Header parsing → Date: 2025/02/21 → Format check → "2025-02-21"
                → Weather section → Max Temp: 0°C → Range check → 0
                → Problems section → Storm Slabs → Type validation → "Storm Slabs"
                → Hazard section → Alpine: Considerable (3) → Scale check → 3
```

## Error Handling Strategy

### Recoverable Errors
- **Format issues**: Auto-correct common patterns
- **Missing optional fields**: Use null/empty values
- **Minor inconsistencies**: Flag but continue processing

### Critical Errors
- **Missing required fields**: Halt processing, request clarification
- **Invalid enum values**: Reject, provide valid alternatives
- **Logical impossibilities**: Flag for manual review

## Best Practices for LLMs

1. **Be Conservative**: When uncertain, flag for review rather than guess
2. **Preserve Context**: Include source text in validation messages
3. **Document Assumptions**: Note any interpretations made during conversion
4. **Validate Incrementally**: Check each section as it's processed
5. **Maintain Traceability**: Link JSON fields back to source Markdown

## Testing Your Implementation

Use the provided examples in `markdown-examples/` to verify:
1. All four reports convert without critical errors
2. Required fields are properly extracted
3. Validation rules catch intentional errors
4. Output JSON validates against the template schema

---

*This implementation guide should be used in conjunction with the detailed validation rules and template documentation.*
