# Capsule Flow Example

## How the Self-Contained Capsules Work

### 1. Initial Load (from Supabase)
When a report session starts, the initial capsule is loaded with constants populated:

```json
{
  "capsule_type": "initial_data_collection",
  
  "question": "Let's get started with your operational report. I need some basic information that will apply to all your observations today. Please tell me: Is this report for today (10/28/2025)? Which zone did you operate in? Were there other guides working with you (and their names)? What time did your operational day start and end? How many guests did you have? What were your main objectives or routes? And can you give me a brief summary of how the day went?",
  
  "payload": {
    "report_date": {
      "value": "10/28/2025",
      "type": "string",
      "format": "MM/DD/YYYY",
      "required": true,
      "default": "10/28/2025"
    },
    "guides": {
      "value": [
        {
          "name": "John Smith",
          "uuid": "user-uuid-123"
        }
      ],
      "type": "array",
      "required": true,
      "min_items": 1
    }
    // ... other fields empty
  },
  
  "constants_populated": {
    "operation_uuid": "op-uuid-456",
    "user_name": "John Smith",
    "user_uuid": "user-uuid-123",
    "today_date": "10/28/2025",
    "timezone": "America/Vancouver"
  }
}
```

### 2. After Agent Processes User Response
The agent populates the payload and updates completion status:

```json
{
  "capsule_type": "initial_data_collection",
  
  "payload": {
    "report_date": {
      "value": "10/28/2025"
    },
    "zone_name": {
      "value": "Whistler Backcountry"
    },
    "location_uuids": {
      "value": ["loc-uuid-789"]
    },
    "guides": {
      "value": [
        {
          "name": "John Smith",
          "uuid": "user-uuid-123"
        },
        {
          "name": "Jane Doe",
          "uuid": "user-uuid-456"
        }
      ]
    },
    "start_time": {
      "value": "08:30"
    },
    "end_time": {
      "value": "15:45"
    },
    "guest_count": {
      "value": 6
    },
    "objectives": {
      "value": "Musical Bumps via Singing Pass"
    },
    "daily_summary": {
      "value": "Great day with stable conditions. Stayed in treeline terrain due to wind loading above."
    }
  },
  
  "completion_status": {
    "is_complete": true,
    "required_fields_missing": [],
    "validation_errors": []
  },
  
  "fields_for_inheritance": {
    "obDate": "10/28/2025",
    "operationUUID": "op-uuid-456",
    "locationUUIDs": ["loc-uuid-789"],
    "state": "IN_REVIEW",
    "obStartTime": "08:30",
    "obEndTime": "15:45",
    "usersPresent": ["user-uuid-123", "user-uuid-456"],
    "observers": ["user-uuid-123", "user-uuid-456"],
    "observersString": "John Smith, Jane Doe"
  }
}
```

### 3. Next Capsule Loads with Inherited Data
When `is_complete = true`, trigger creates field_summary capsule with inherited values:

```json
{
  "capsule_type": "field_summary",
  
  "question": "Now I need the field weather observations...",
  
  "payload": {
    "obDate": {
      "value": "10/28/2025",
      "type": "string",
      "format": "MM/DD/YYYY",
      "required": true,
      "inherited": true
    },
    "obStartTime": {
      "value": "08:30",
      "type": "string",
      "format": "HH:MM",
      "required": false,
      "inherited": true
    },
    "obEndTime": {
      "value": "15:45",
      "type": "string",
      "format": "HH:MM",
      "required": false,
      "inherited": true
    },
    "tempHigh": {
      "value": null,
      "type": "number",
      "required": false,
      "validation": "range:-50:50"
    },
    // ... other fields to be filled
    "locationUUIDs": {
      "value": ["loc-uuid-789"],
      "type": "array",
      "required": true,
      "inherited": true
    },
    "operationUUID": {
      "value": "op-uuid-456",
      "type": "string",
      "required": true,
      "inherited": true
    },
    "state": {
      "value": "IN_REVIEW",
      "type": "string",
      "required": true,
      "enum": ["IN_REVIEW", "SUBMITTED"]
    }
  },
  
  "completion_status": {
    "is_complete": false,
    "required_fields_missing": [],
    "aurora_ideal_missing": [
      "tempHigh",
      "tempLow",
      // ... etc
    ],
    "validation_errors": []
  }
}
```

## Benefits for Prompt Caching

### Static Prompt (Cached)
```
You are an InfoEx report assistant. You help guides complete operational reports.

Rules:
1. Extract data from user responses to populate the payload
2. Validate according to the constraints
3. Update completion_status
4. Be conversational but focused

[... more static instructions ...]
```

### Dynamic Capsule (Not Cached)
Only the JSON capsule changes between interactions, maximizing cache hits.

## Database Flow

1. **Session Start**
   - Create report_session record
   - Insert initial_data_collection capsule with user constants

2. **After Each Response**
   - Update current capsule payload
   - Validate fields
   - If complete, trigger creates next capsule with inherited fields

3. **Completion**
   - All capsules complete
   - Generate final reports from accumulated data
