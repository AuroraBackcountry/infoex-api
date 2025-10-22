"""InfoEx constants loader and manager"""

import json
import os
from typing import Dict, List, Any, Optional
from pathlib import Path
import structlog

logger = structlog.get_logger()


class InfoExConstants:
    """Manages InfoEx validation constants"""
    
    def __init__(self, constants_file: Optional[str] = None):
        """Initialize with constants file path"""
        if constants_file is None:
            # Default to data/infoex_constants.json
            base_dir = Path(__file__).parent.parent.parent
            constants_file = base_dir / "data" / "infoex_constants.json"
        
        self.constants_file = Path(constants_file)
        self.constants: Dict[str, Any] = {}
        self.load_constants()
    
    def load_constants(self) -> None:
        """Load constants from JSON file"""
        try:
            with open(self.constants_file, 'r') as f:
                self.constants = json.load(f)
            logger.info("infoex_constants_loaded", 
                       path=str(self.constants_file),
                       keys=list(self.constants.keys())[:10])
        except FileNotFoundError:
            logger.error("constants_file_not_found", path=str(self.constants_file))
            raise
        except json.JSONDecodeError as e:
            logger.error("constants_json_error", error=str(e))
            raise
    
    def get_valid_values(self, constant_type: str) -> List[Any]:
        """Get valid values for a constant type"""
        if constant_type not in self.constants:
            logger.warning("unknown_constant_type", type=constant_type)
            return []
        
        values = self.constants.get(constant_type, [])
        
        # Handle different data structures
        if isinstance(values, dict):
            # For character types with labels and colors
            if all(isinstance(v, dict) and 'value' in v for v in values.values()):
                return [v['value'] for v in values.values()]
            # For simple key-value mappings
            return list(values.keys())
        elif isinstance(values, list):
            # For lists of dicts with 'value' field
            if values and isinstance(values[0], dict) and 'value' in values[0]:
                return [v['value'] for v in values]
            # For simple lists
            return values
        
        return []
    
    def validate_value(self, constant_type: str, value: Any) -> bool:
        """Check if a value is valid for a constant type"""
        valid_values = self.get_valid_values(constant_type)
        return value in valid_values
    
    def get_character_info(self, character_value: str) -> Optional[Dict[str, str]]:
        """Get character info including label and color"""
        characters = self.constants.get("character", [])
        for char in characters:
            if isinstance(char, dict) and char.get("value") == character_value:
                return char
        return None
    
    def get_elevation_band_info(self, band_code: str) -> Optional[Dict[str, str]]:
        """Get elevation band info"""
        bands = self.constants.get("elevationBand", {})
        return bands.get(band_code)
    
    def get_all_observation_types(self) -> List[str]:
        """Get all available observation types Aurora supports"""
        return [
            "field_summary",
            "avalanche_summary",
            "avalanche_observation",
            "hazard_assessment",
            "snowpack_summary",
            "snowProfile_observation",
            "terrain_observation",
            "pwl_persistent_weak_layer"
        ]
    
    def get_required_fields(self, observation_type: str) -> List[str]:
        """Get required fields for an observation type"""
        # This maps to the AURORA_IDEAL requirements
        required_fields = {
            "field_summary": ["obDate", "obStartTime", "obEndTime", "tempHigh", "tempLow", 
                            "comments", "locationUUIDs", "state"],
            "avalanche_observation": ["obDate", "obTime", "num", "trigger", "character", 
                                    "locationUUIDs", "state"],
            "avalanche_summary": ["obDate", "comments", "avalanchesObserved", 
                                "percentAreaObserved", "locationUUIDs", "state"],
            "hazard_assessment": ["obDate", "obTime", "assessmentType", "avalancheProblems",
                                "hazardRatings", "locationUUIDs", "state"],
            "snowpack_summary": ["obDate", "obTime", "snowpackSummary", "locationUUIDs", "state"],
            "snowProfile_observation": ["obDate", "obTime", "elevation", "aspect", "incline",
                                      "summary", "locationUUIDs", "state"],
            "terrain_observation": ["obDate", "terrainNarrative", "atesRating", "terrainFeature",
                                  "strategicMindset", "locationUUIDs", "state"],
            "pwl_persistent_weak_layer": ["name", "creationDate", "color", "operationUUID", 
                                        "assessment"]
        }
        return required_fields.get(observation_type, [])
    
    def format_for_prompt(self) -> str:
        """Format constants for inclusion in Claude's prompt"""
        formatted = "Valid InfoEx Constants:\n\n"
        
        # Key constants to include
        key_constants = [
            "character",
            "trigger", 
            "distribution",
            "sensitivity",
            "windSpeed",
            "cardinalDirection",
            "sky",
            "precipitation",
            "atesRating",
            "hazardRatingConstants"
        ]
        
        for const_type in key_constants:
            if const_type in self.constants:
                values = self.get_valid_values(const_type)
                formatted += f"{const_type}: {', '.join(map(str, values))}\n"
        
        return formatted


# Create a singleton instance
infoex_constants = InfoExConstants()
