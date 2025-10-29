# Markdown File Cleanup Plan

## 🗂️ **Current File Analysis (39 files)**

### **📋 Files to Keep (Core Documentation)**
1. **README.md** - Main project overview
2. **DATABASE_FUNCTIONS_GUIDE.md** - PostgreSQL functions reference
3. **N8N_AGENT_INSTRUCTIONS.md** - Updated agent instructions
4. **N8N_CAPSULE_INTEGRATION_GUIDE.md** - n8n workflow guide
5. **CAPSULE_ARCHITECTURE.md** - Core architecture documentation
6. **VALIDATION_RULES.md** - Data validation rules
7. **FIELD_MAPPING_TABLE.md** - Field mapping reference
8. **INFOEX_API_REFERENCE.md** - API documentation

### **📁 Files to Consolidate/Merge**
1. **CURRENT_STATUS_AND_NEXT_STEPS.md** + **CAPSULE_FOCUS_UPDATES.md** → Merge into single status file
2. **DOCUMENTATION_UPDATES_SUMMARY.md** + **EFFICIENT_ARCHITECTURE_SUMMARY.md** → Archive as historical
3. **SEPARATION_OF_CONCERNS.md** → Merge into CAPSULE_ARCHITECTURE.md
4. **REDIS_SESSION_MANAGEMENT.md** → Merge into N8N_CAPSULE_INTEGRATION_GUIDE.md

### **🗑️ Files to Delete (Redundant/Outdated)**
1. **GIT_COMMIT_SUMMARY.md** - Temporary file
2. **ARCHITECTURE_UPDATE_PLAN.md** - Completed plan
3. **IMPLEMENTATION_GUIDE.md** - Superseded by N8N_CAPSULE_INTEGRATION_GUIDE.md
4. **ENV_EXAMPLE_SUMMARY.md** - Redundant with service README
5. **agent prompts/elrich_v1.md** - Legacy agent prompts
6. **agent prompts/elrich_v2.md** - Legacy agent prompts  
7. **agent prompts/elrich_v3.md** - Legacy agent prompts
8. **agent prompts/elrich_v4.md** - Legacy agent prompts
9. **agent prompts/markdown-examples/report_1.md** - Test files
10. **agent prompts/markdown-examples/report_2.md** - Test files
11. **agent prompts/markdown-examples/report_3.md** - Test files
12. **agent prompts/markdown-examples/report_4.md** - Test files

### **📂 Files to Reorganize**
1. **capsule prompts/** - Keep all capsule files
2. **infoex-agent-service/** - Keep service-specific docs
3. **agent prompts/** - Remove legacy files, keep structure

## 🎯 **Target Structure (15 files)**
```
├── README.md
├── DATABASE_FUNCTIONS_GUIDE.md
├── N8N_AGENT_INSTRUCTIONS.md
├── N8N_CAPSULE_INTEGRATION_GUIDE.md
├── CAPSULE_ARCHITECTURE.md
├── VALIDATION_RULES.md
├── FIELD_MAPPING_TABLE.md
├── INFOEX_API_REFERENCE.md
├── PROJECT_STATUS.md (merged from 2 files)
├── DATABASE_CLEANUP_LOG.json
├── capsule prompts/
│   ├── *.json (9 capsule files)
│   ├── *.md (4 reference files)
├── infoex-agent-service/
│   ├── README.md
│   ├── *.md (6 service files)
└── agent prompts/
    └── (empty - legacy files removed)
```

## 📊 **Cleanup Benefits**
- **Reduce from 39 to 15 files** (62% reduction)
- **Eliminate redundancy** and outdated information
- **Improve navigation** with clear structure
- **Focus on current architecture** only
- **Maintain essential documentation** for development
