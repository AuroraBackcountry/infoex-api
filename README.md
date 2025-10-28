# Aurora InfoEx Reporting System

## Overview

The Aurora InfoEx Reporting System transforms conversational avalanche safety reports into structured data for submission to the InfoEx Canadian avalanche database. The system uses a **capsule-based architecture** that breaks complex reports into manageable, self-contained questions.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Conversation (n8n)                       │
│     - Dialogue Agent with dynamic question capsules              │
│     - Collects responses progressively                          │
│     - Stores data in Postgres                                   │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│               Markdown Report Generator (Tool)                   │
│     - Triggered when all capsules complete                      │
│     - Creates formatted human-readable report                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Postgres Database                             │
│     - Stores completed capsule JSON payloads                    │
│     - Ready for InfoEx submission                               │
└─────────────────────────────────────────────────────────────────┘
                              ↓ (On manual trigger)
┌─────────────────────────────────────────────────────────────────┐
│              Claude Microservice (Render)                        │
│     - Validates individual capsule payloads                     │
│     - Converts date formats (ISO → MM/DD/YYYY)                 │
│     - Submits to InfoEx API endpoints                          │
│     - Handles errors and retries                               │
└─────────────────────────────────────────────────────────────────┘
```

## Key Components

### 1. Capsule System
Self-contained question units that guide report creation:
- `initial_data_collection` - Basic report info (date, guides, zone)
- `field_summary` - Weather and snow observations
- `avalanche_observation` - Individual avalanche details
- `avalanche_summary` - Overall avalanche activity
- `hazard_assessment` - Danger ratings and problems
- `snowpack_summary` - Snowpack structure
- `terrain_observation` - Terrain choices and strategy
- `pwl_persistent_weak_layer` - Seasonal tracking

See [CAPSULE_ARCHITECTURE.md](CAPSULE_ARCHITECTURE.md) for detailed documentation.

### 2. Claude Microservice
A separate FastAPI service that handles InfoEx API submission:
- Validates payloads against InfoEx requirements
- Manages authentication and API calls
- Provides retry logic for failed submissions
- Returns actionable error messages

See [infoex-agent-service/README.md](infoex-agent-service/README.md) for microservice documentation.

## Data Standards

### Date Formats
- **Display/Storage**: ISO format `yyyy-MM-dd`
- **InfoEx API**: `MM/DD/YYYY` (converted at submission)

### OGRS Compliance
All weather observations follow Official Guidelines for Reporting Standards:
- Wind: Calm/Light/Moderate/Strong/Extreme → C/L/M/S/X
- Precipitation: Descriptive → S1-S10 intensity codes
- Sky: Clear/Few/Scattered/Broken/Overcast → CLR/FEW/SCT/BKN/OVC

### Submission States
- **IN_REVIEW**: Draft mode (default) - not publicly visible
- **SUBMITTED**: Final mode - publicly visible in InfoEx

## InfoEx API Integration

### Endpoints Used
Aurora submits to these InfoEx observation endpoints:
- `/observation/fieldSummary` - Daily operational summary with weather
- `/observation/avalancheSummary` - Avalanche activity overview
- `/observation/avalanche` - Individual avalanche observations
- `/observation/hazardAssessment` - Hazard ratings and problems
- `/observation/snowpackAssessment` - Snowpack conditions
- `/observation/terrain` - Terrain observations

**Note**: Aurora does NOT use `/observation/weather` (for automated weather stations).

## Quick Start

### Prerequisites
- Node.js 18+ (for n8n)
- Python 3.11+ (for Claude microservice)
- PostgreSQL 14+
- Redis 7+

### Setup

1. **Database Setup**
   ```sql
   -- Create tables for capsule storage
   -- See CAPSULE_ARCHITECTURE.md for schema
   ```

2. **n8n Configuration**
   - Import workflow templates
   - Configure environment variables
   - Set up capsule questions

3. **Claude Microservice**
   ```bash
   cd infoex-agent-service
   cp env.example .env
   # Edit .env with your credentials
   docker-compose up
   ```

## Documentation

- [CAPSULE_ARCHITECTURE.md](CAPSULE_ARCHITECTURE.md) - Detailed capsule system design
- [REDIS_SESSION_MANAGEMENT.md](REDIS_SESSION_MANAGEMENT.md) - Session handling documentation
- [VALIDATION_RULES.md](VALIDATION_RULES.md) - Data validation standards
- [INFOEX_API_REFERENCE.md](INFOEX_API_REFERENCE.md) - Complete InfoEx API documentation
- [FIELD_MAPPING_TABLE.md](FIELD_MAPPING_TABLE.md) - Aurora to InfoEx field mappings

## Environment Variables

### n8n Agent
```env
POSTGRES_CONNECTION=postgresql://user:pass@localhost/aurora
REDIS_URL=redis://localhost:6379
INFOEX_OPERATION_UUID=your-aurora-operation-uuid
```

### Claude Microservice
```env
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
ENVIRONMENT=staging
STAGING_API_KEY=your-staging-key
STAGING_OPERATION_UUID=your-staging-uuid
```

## Development Workflow

1. **User starts report** → n8n dialogue agent presents first capsule
2. **Progressive completion** → Each capsule stored in Postgres
3. **Generate markdown** → Tool creates human-readable report
4. **Review report** → User checks and approves
5. **Trigger submission** → Claude validates and sends to InfoEx
6. **Track results** → Store InfoEx responses

## Testing

- Capsule validation tests: `capsule prompts/`
- API payload examples: `infoex-api-payloads/`
- Agent prompt versions: `agent prompts/`

## Support

For issues or questions:
1. Check the documentation in this repository
2. Review InfoEx API documentation
3. Contact Aurora Backcountry development team

---

*This system ensures accurate, consistent avalanche reporting while maintaining a conversational user experience.*