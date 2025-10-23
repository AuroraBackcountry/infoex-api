# n8n Claude Tool - HTTP Request Fields Configuration

## Quick Copy-Paste Fields for n8n HTTP Request Node

When configuring the Claude tool in n8n as an HTTP Request node with "Using Fields Below", add these 7 fields:

1. **session_id**
   - Name: `session_id`
   - Value: `{{ $json.sessionId }}`
   - Type: Expression

2. **message**
   - Name: `message`
   - Value: `{{ $json.formatted_message }}`
   - Type: Expression

3. **auto_submit**
   - Name: `auto_submit`
   - Value: `false`
   - Type: Fixed
   - Note: Set to `true` if you want final submission (SUBMITTED state)

4. **operation_id**
   - Name: `request_values.operation_id`
   - Value: `{{ $vars.INFOEX_OPERATION_ID }}`
   - Type: Expression

5. **location_uuids (first location)**
   - Name: `request_values.location_uuids[0]`
   - Value: `{{ $json.location_uuids[0] }}`
   - Type: Expression

6. **zone_name**
   - Name: `request_values.zone_name`
   - Value: `{{ $json.zone_name }}`
   - Type: Expression

7. **date**
   - Name: `request_values.date`
   - Value: `{{ $now.format('MM/dd/yyyy') }}`
   - Type: Expression


### If You Have Multiple Locations

Add additional location fields:
- Name: `request_values.location_uuids[1]`
- Value: `{{ $json.location_uuids[1] }}`
- Type: Expression

Continue with `[2]`, `[3]`, etc. for more locations.

## Example of What This Creates

The above fields will create this JSON body:
```json
{
  "session_id": "c74d60b2b7b345778cfd5f3a4999d7f7",
  "message": "Submit avalanche observation:\nTime: 11:30\nSize: 2...",
  "auto_submit": false,
  "request_values": {
    "operation_id": "4a9c17c0-e86b-4124-9a94-db8fbcd81d7c",
    "location_uuids": ["fe206d0d-c886-47c3-8ac6-b85d6b3c45c9"],
    "zone_name": "North Bowl",
    "date": "10/23/2025"
  }
}
```

## Field Entry Tips

1. Click "Add Parameter" for each field
2. Enter the Name exactly as shown (including dots for nested fields)
3. Choose Expression or Fixed as the type
4. Paste the Value
5. The dot notation automatically creates nested JSON structure
