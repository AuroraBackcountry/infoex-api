# InfoEx Agent Service - Bugs and Inconsistencies Report

## 1. Auto-Submit References (CRITICAL)

**Issue**: The service still contains many references to `auto_submit` functionality, but user stated "auto-submit is not going to be really a thing anymore."

**Affected Files**:
- `app/main.py`:
  - Line 116: Example body includes `"auto_submit": true`
  - Line 127: Documents `auto_submit` field
  - Line 168: Error message references `fixed_values` instead of `request_values`

- `app/models.py`:
  - Line 43: `auto_submit` field in `ProcessReportRequest` with default `True`
  - Line 56: Documentation references `auto_submit=true`

- `app/api/routes.py`:
  - Lines 60-67, 138: Still checks and logs `auto_submit` parameter
  - Line 125: References "Auto-submission results"

- `app/agent/prompts.py`:
  - Lines 133-134: Still describes different states based on `auto_submit`

## 2. Fixed Values vs Inherited Values Terminology

**Issue**: Inconsistent terminology - should use "inherited values" not "fixed values"

**Affected Files**:
- `app/main.py`:
  - Line 168: Error message mentions `'fixed_values' instead of 'request_values'`
  
- `test_service.py`:
  - Line 55: Comment says "Fixed values for testing"

## 3. Submission Logic Contradiction

**Issue**: The service automatically submits when payloads are "ready", contradicting the "triggered on request" approach

**Affected Code** (`app/api/routes.py`):
```python
# Lines 69-125: Automatic submission when "ready for" and "submission" detected
if "ready for" in response_text.lower() and "submission" in response_text.lower():
    # Auto-submit ready payloads
```

**Expected Behavior**: Submissions should only occur when explicitly triggered via `/api/submit-to-infoex` endpoint

## 4. Documentation Gaps

**Issue**: Service documentation doesn't reflect new capsule architecture

**Missing Context**:
- No mention of capsule-based dialogue system
- No documentation about inherited values flowing between payloads
- README still shows old workflow without capsules

## 5. Validation Error Message Inconsistency

**Issue**: Validation error helper still suggests old field names

**Location**: `app/main.py` line 168
```python
"The most common issue is using 'fixed_values' instead of 'request_values'."
```
Should be:
```python
"The most common issue is using 'inherited_values' instead of 'request_values'."
```

## 6. Session Prefix Configuration

**Issue**: Redis session prefix is set to "claude" but this might conflict with dialogue agent

**Location**: `app/config.py` line 76
```python
redis_session_prefix: Optional[str] = Field(default="claude", description="Redis key prefix for sessions")
```

**Consideration**: Should this be changed to something like "infoex-service" to avoid conflicts?

## 7. Prompts Need Update

**Issue**: System prompts still reference old concepts

**Location**: `app/agent/prompts.py`
- Still mentions auto_submit behavior
- Doesn't acknowledge capsule architecture
- Contains references to both IN_REVIEW and SUBMITTED states based on auto_submit

## 8. Missing Capsule Integration

**Issue**: Service doesn't integrate with new capsule system

**Expected Features**:
- Ability to receive and validate individual capsule payloads
- Support for inherited values from capsules
- Clear separation between dialogue data and API payloads

## 9. Confusing State Management

**Issue**: Submission state logic is complex and potentially confusing

**Current Logic**:
1. Can be set via environment variable (`INFOEX_SUBMISSION_STATE`)
2. Can be overridden in request (`submission_state` field)
3. Defaults to "IN_REVIEW"
4. But also mentions different behavior for auto_submit true/false

## 10. Test Script Terminology

**Issue**: Test script uses outdated terminology

**Location**: `test_service.py`
- Line 55: "Fixed values for testing"
- Should be updated to reflect current architecture

## Recommendations

### Immediate Fixes Needed:
1. Remove all `auto_submit` references from models, routes, and prompts
2. Update terminology from "fixed values" to "inherited values"
3. Remove automatic submission logic from `/api/process-report`
4. Update validation error messages

### Architecture Updates:
1. Add support for receiving capsule payloads
2. Implement inherited value processing
3. Update prompts to understand capsule context
4. Clarify submission flow (manual trigger only)

### Documentation Updates:
1. Update README to reflect capsule architecture
2. Document inherited values pattern
3. Clarify that submission is always manual
4. Add examples of capsule integration

### Configuration Clarifications:
1. Rename Redis prefix to avoid conflicts
2. Simplify submission state logic (always IN_REVIEW unless specified)
3. Remove auto_submit from all examples
