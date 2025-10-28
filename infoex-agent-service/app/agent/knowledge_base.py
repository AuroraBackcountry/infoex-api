"""
Knowledge Base for InfoEx API Documentation and Templates

This module pre-processes and structures all reference documentation
for efficient access by the Claude agent.
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()


class KnowledgeBase:
    """Pre-processed knowledge base for InfoEx API"""
    
    def __init__(self, base_path: str = None):
        """Initialize knowledge base with reference files"""
        self.base_path = Path(base_path or os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
        self.payloads: Dict[str, Dict[str, Any]] = {}
        self.endpoints: Dict[str, str] = {}
        self.validation_rules: Dict[str, Any] = {}
        self.field_mappings: Dict[str, Any] = {}
        self.constants: Dict[str, Any] = {}
        
        # Observation type to endpoint mapping
        self.observation_endpoints = {
            "avalanche_observation": "/observation/avalanche",
            "avalanche_summary": "/observation/avalancheSummary", 
            "field_summary": "/observation/fieldSummary",
            "hazard_assessment": "/observation/hazardAssessment",
            "pwl_persistent_weak_layer": "/observation/pwl",
            "snowpack_summary": "/observation/snowpackSummary",
            "snowProfile_observation": "/observation/snowProfile",
            "terrain_observation": "/observation/terrainUse"
        }
        
        self._load_knowledge()
    
    def _load_knowledge(self):
        """Load all reference files into structured knowledge"""
        try:
            # Load payload templates
            self._load_payload_templates()
            
            # Load InfoEx constants
            self._load_constants()
            
            # Load validation rules (simplified version)
            self._load_validation_rules()
            
            # Load field mappings (simplified version)
            self._load_field_mappings()
            
            logger.info("knowledge_base_loaded",
                       payloads=len(self.payloads),
                       endpoints=len(self.endpoints))
            
        except Exception as e:
            logger.error("knowledge_base_load_error", error=str(e))
            raise
    
    def _load_payload_templates(self):
        """Load AURORA_IDEAL_PAYLOAD from each payload file"""
        payload_dir = self.base_path / "infoex-api-payloads"
        
        for obs_type, endpoint in self.observation_endpoints.items():
            json_file = payload_dir / f"{obs_type}.json"
            
            if json_file.exists():
                try:
                    with open(json_file, 'r') as f:
                        data = json.load(f)
                        
                    if 'AURORA_IDEAL_PAYLOAD' in data:
                        self.payloads[obs_type] = data['AURORA_IDEAL_PAYLOAD']
                        self.endpoints[obs_type] = endpoint
                        logger.debug(f"Loaded payload template for {obs_type}")
                    else:
                        logger.warning(f"No AURORA_IDEAL_PAYLOAD in {json_file}")
                        
                except Exception as e:
                    logger.error(f"Error loading {json_file}: {e}")
    
    def _load_constants(self):
        """Load InfoEx constants"""
        constants_file = self.base_path / "infoex_constants_full.json"
        
        if constants_file.exists():
            try:
                with open(constants_file, 'r') as f:
                    self.constants = json.load(f)
                logger.debug("Loaded InfoEx constants")
            except Exception as e:
                logger.error(f"Error loading constants: {e}")
    
    def _load_validation_rules(self):
        """Load key validation rules"""
        # Simplified validation rules - in production, parse VALIDATION_RULES.md
        self.validation_rules = {
            "date_format": "MM/DD/YYYY",
            "time_format": "HH:MM",
            "required_header_fields": ["obDate", "locationUUIDs"],
            "avalanche_sizes": ["0.5", "1", "1.5", "2", "2.5", "3", "3.5", "4", "4.5", "5"],
            "hazard_ratings": ["0:N/A", "1:Low", "2:Moderate", "3:Considerable", "4:High", "5:Extreme"],
            "avalanche_problems": [
                "Dry Loose",
                "Wet Loose", 
                "Wind Slab",
                "Storm Slab",
                "Persistent Slab",
                "Deep Persistent Slab",
                "Wet Slab",
                "Cornice",
                "Glide"
            ]
        }
    
    def _load_field_mappings(self):
        """Load field mapping rules"""
        # Simplified field mappings - in production, parse FIELD_MAPPING_TABLE.md
        self.field_mappings = {
            "date_conversion": {
                "description": "Convert various date formats to MM/DD/YYYY",
                "examples": {
                    "2025-02-21": "02/21/2025",
                    "2025/02/21": "02/21/2025",
                    "21-02-2025": "02/21/2025"
                }
            },
            "location_mapping": {
                "description": "Map location names to UUIDs",
                "note": "UUIDs provided by n8n as inherited values"
            }
        }
    
    def get_payload_template(self, observation_type: str) -> Optional[Dict[str, Any]]:
        """Get payload template for specific observation type"""
        return self.payloads.get(observation_type)
    
    def get_endpoint(self, observation_type: str) -> Optional[str]:
        """Get API endpoint for observation type"""
        return self.endpoints.get(observation_type)
    
    def get_enum_values(self, field_name: str) -> List[str]:
        """Get valid enum values for a field"""
        # Check constants for enum values
        if field_name in self.constants:
            const_data = self.constants[field_name]
            if isinstance(const_data, dict) and 'values' in const_data:
                return const_data['values']
        
        # Check validation rules
        if field_name in self.validation_rules:
            return self.validation_rules[field_name]
        
        return []
    
    def get_validation_context(self, observation_type: str) -> Dict[str, Any]:
        """Get minimal validation context for Claude"""
        template = self.get_payload_template(observation_type)
        endpoint = self.get_endpoint(observation_type)
        
        # Extract field names and types from template
        fields = {}
        if template:
            for key, value in template.items():
                if isinstance(value, list):
                    fields[key] = "array"
                elif isinstance(value, dict):
                    fields[key] = "object"
                else:
                    fields[key] = type(value).__name__
        
        return {
            "observation_type": observation_type,
            "endpoint": endpoint,
            "template_fields": fields,
            "date_format": self.validation_rules.get("date_format"),
            "required_fields": self.validation_rules.get("required_header_fields", [])
        }
    
    def format_for_claude_context(self, observation_type: str) -> str:
        """Format relevant knowledge as concise context for Claude"""
        template = self.get_payload_template(observation_type)
        endpoint = self.get_endpoint(observation_type)
        
        if not template:
            return f"No template found for {observation_type}"
        
        context = f"""
InfoEx Endpoint: {endpoint}
Observation Type: {observation_type}

Required Payload Structure:
{json.dumps(template, indent=2)}

Key Validation Rules:
- Date format: MM/DD/YYYY
- All locationUUIDs must be valid
- Follow OGRS standards for all terminology
"""
        
        return context


# Singleton instance
_knowledge_base: Optional[KnowledgeBase] = None

def get_knowledge_base() -> KnowledgeBase:
    """Get or create knowledge base singleton"""
    global _knowledge_base
    if _knowledge_base is None:
        _knowledge_base = KnowledgeBase()
    return _knowledge_base
