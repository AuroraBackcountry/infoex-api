# Testing Multiple Avalanche Observations

## What We Need to Determine

The InfoEx API endpoint `/observation/avalanche` needs to be tested to see if it accepts:

1. **Single observation per request** (most likely based on API docs)
2. **Array of observations** (would be convenient but unlikely)

## Quick Test Setup

### 1. Set Your Credentials

Edit the `.env` file and replace these values:
```env
STAGING_API_KEY=your_actual_staging_api_key_here
OPERATION_UUID=your_actual_operation_uuid_here
```

You'll also need at least one valid location UUID for your operation. You can find this by:
- Logging into InfoEx staging
- Going to your operation settings
- Looking at your locations

### 2. Run the Test

```bash
./quick_test_avalanche.sh
```

This will:
- ✅ Test 1: Send a single avalanche observation (should work)
- ❓ Test 2: Send an array of avalanche observations (will likely fail with 400 error)

## Expected Results

Based on the API documentation structure, I expect:

- **Single observation**: ✅ SUCCESS (200 response)
- **Array submission**: ❌ FAIL (400 Bad Request)

## What This Means for Architecture

If arrays are NOT supported (most likely):

### Database Structure
- **Single row** with `report_type = 'avalanche_observation'`
- **JSONB payload contains array** of avalanche objects
- Example:
```json
{
  "report_type": "avalanche_observation",
  "payload": [
    { /* avalanche 1 */ },
    { /* avalanche 2 */ },
    { /* avalanche 3 */ }
  ]
}
```

### InfoEx Service Behavior
The service will:
1. Receive submission request with `report_uuid` and `submission_type`
2. Query Postgres for the capsule data
3. If payload is an array, iterate and submit each avalanche separately:

```python
if isinstance(payload, list):
    results = []
    for avalanche in payload:
        response = await infoex_client.submit_observation("avalanche", avalanche)
        results.append(response)
    return results
else:
    # Single observation
    return await infoex_client.submit_observation("avalanche", payload)
```

## Alternative: Without Real Credentials

If you don't have staging credentials available, we can:
1. Proceed with the assumption that arrays are NOT supported (based on API docs)
2. Design the system to handle arrays in the service layer
3. This is the safer approach anyway as it's more flexible
