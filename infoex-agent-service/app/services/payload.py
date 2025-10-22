"""Payload construction and validation service"""

import json
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import structlog

from app.models import Session, PayloadStatus
from app.agent.constants import infoex_constants

logger = structlog.get_logger()


class PayloadBuilder:
    """Builds and validates InfoEx payloads"""
    
    def __init__(self):
        """Initialize with templates"""
        self.templates = self._load_templates()
        self.validators = self._build_validators()
    
    def _load_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load AURORA_IDEAL templates"""
        templates = {}
        template_dir = Path("data/aurora_templates")
        
        for file_path in template_dir.glob("*.json"):
            obs_type = file_path.stem
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    if "AURORA_IDEAL_PAYLOAD" in data:
                        templates[obs_type] = data["AURORA_IDEAL_PAYLOAD"]
                        logger.info("template_loaded", type=obs_type)
            except Exception as e:
                logger.error("template_load_error", 
                           type=obs_type,
                           error=str(e))
        
        return templates
    
    def _build_validators(self) -> Dict[str, Any]:
        """Build field validators for each observation type"""
        return {
            "avalanche_observation": {
                "character": lambda v: infoex_constants.validate_value("character", v),
                "trigger": lambda v: infoex_constants.validate_value("trigger", v),
                "sizeMin": lambda v: 1 <= v <= 5,
                "sizeMax": lambda v: 1 <= v <= 5,
                "num": lambda v: v in ["1","2","3","4","5","6","7","8","9","10","11","12",
                                     "20","50","100","Iso","Sev","Num","NR","Unknown"],
                "aspectFrom": lambda v: infoex_constants.validate_value("aspectDirection", v),
                "aspectTo": lambda v: infoex_constants.validate_value("aspectDirection", v),
            },
            "hazard_assessment": {
                "assessmentType": lambda v: v in ["Nowcast", "Forecast", "DAILY_ASSESSMENT"],
                "avalancheProblems": self._validate_avalanche_problems,
                "hazardRatings": self._validate_hazard_ratings,
            },
            "field_summary": {
                "windSpeed": lambda v: infoex_constants.validate_value("windSpeed", v),
                "windDirection": lambda v: infoex_constants.validate_value("cardinalDirection", v),
                "sky": lambda v: infoex_constants.validate_value("sky", v),
                "precip": lambda v: infoex_constants.validate_value("precipitation", v),
            },
            "terrain_observation": {
                "atesRating": lambda v: infoex_constants.validate_value("atesRating", v),
                "strategicMindset": lambda v: infoex_constants.validate_value("strategicMindset", v),
                "windExposure": lambda v: all(infoex_constants.validate_value("windExposure", w) for w in v),
                "terrainFeature": lambda v: all(infoex_constants.validate_value("terrainFeature", t) for t in v),
            }
        }
    
    def _validate_avalanche_problems(self, problems: List[Dict[str, Any]]) -> bool:
        """Validate avalanche problems structure"""
        if not isinstance(problems, list):
            return False
        
        for problem in problems:
            # Check required fields
            required = ["character", "distribution", "sensitivity"]
            if not all(field in problem for field in required):
                return False
            
            # Validate enum values
            if not infoex_constants.validate_value("character", problem["character"]):
                return False
            if not infoex_constants.validate_value("distribution", problem["distribution"]):
                return False
            if not infoex_constants.validate_value("sensitivity", problem["sensitivity"]):
                return False
        
        return True
    
    def _validate_hazard_ratings(self, ratings: List[Dict[str, Any]]) -> bool:
        """Validate hazard ratings structure"""
        if not isinstance(ratings, list):
            return False
        
        elevation_bands_seen = set()
        
        for rating in ratings:
            # Check required fields
            if "elevationBand" not in rating or "hazardRating" not in rating:
                return False
            
            # Check for duplicates
            if rating["elevationBand"] in elevation_bands_seen:
                return False
            elevation_bands_seen.add(rating["elevationBand"])
            
            # Validate values
            if rating["elevationBand"] not in ["ALP", "TL", "BTL", "ALL"]:
                return False
            if rating["hazardRating"] not in ["1", "2", "3", "4", "5", "n/a"]:
                return False
        
        return True
    
    def build_payload(
        self,
        observation_type: str,
        session: Session
    ) -> Tuple[Optional[Dict[str, Any]], List[str]]:
        """Build payload for observation type from session data"""
        
        if observation_type not in session.payloads:
            return None, ["Observation type not initialized in session"]
        
        payload_status = session.payloads[observation_type]
        errors = []
        
        # Start with template
        template = self.templates.get(observation_type, {})
        payload = template.copy()
        
        # Merge session data
        payload.update(payload_status.data)
        
        # Add fixed values
        payload["obDate"] = session.fixed_values.date
        payload["locationUUIDs"] = session.fixed_values.location_uuids
        payload["operationUUID"] = session.fixed_values.operation_id
        
        # Ensure state is set
        if "state" not in payload:
            payload["state"] = "IN_REVIEW"
        
        # Validate required fields
        required = infoex_constants.get_required_fields(observation_type)
        missing = []
        
        for field in required:
            if field not in payload or payload[field] is None:
                missing.append(field)
        
        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")
        
        # Validate field values
        validators = self.validators.get(observation_type, {})
        for field, validator in validators.items():
            if field in payload:
                try:
                    if not validator(payload[field]):
                        errors.append(f"Invalid value for {field}: {payload[field]}")
                except Exception as e:
                    errors.append(f"Validation error for {field}: {str(e)}")
        
        # Special validations
        if observation_type == "avalanche_observation":
            # Size validation
            if "sizeMin" in payload and "sizeMax" in payload:
                if payload["sizeMin"] > payload["sizeMax"]:
                    errors.append("sizeMin cannot be greater than sizeMax")
        
        elif observation_type == "field_summary":
            # Temperature validation
            if "tempMin" in payload and "tempMax" in payload:
                if payload["tempMin"] > payload["tempMax"]:
                    errors.append("tempMin cannot be greater than tempMax")
            
            # Time validation
            if "obStartTime" in payload and "obEndTime" in payload:
                # Simple string comparison works for HH:MM format
                if payload["obStartTime"] > payload["obEndTime"]:
                    errors.append("obStartTime cannot be after obEndTime")
        
        if errors:
            logger.warning("payload_validation_errors",
                         observation_type=observation_type,
                         errors=errors)
            return None, errors
        
        logger.info("payload_built",
                   observation_type=observation_type,
                   fields=len(payload))
        
        return payload, []
    
    def validate_payload(
        self,
        observation_type: str,
        payload: Dict[str, Any]
    ) -> List[str]:
        """Validate a complete payload"""
        errors = []
        
        # Check required fields
        required = infoex_constants.get_required_fields(observation_type)
        for field in required:
            if field not in payload or payload[field] is None:
                errors.append(f"Missing required field: {field}")
        
        # Run field validators
        validators = self.validators.get(observation_type, {})
        for field, validator in validators.items():
            if field in payload:
                try:
                    if not validator(payload[field]):
                        errors.append(f"Invalid value for {field}: {payload[field]}")
                except Exception as e:
                    errors.append(f"Validation error for {field}: {str(e)}")
        
        return errors
    
    def get_missing_fields(
        self,
        observation_type: str,
        current_data: Dict[str, Any]
    ) -> List[str]:
        """Get list of missing required fields"""
        required = set(infoex_constants.get_required_fields(observation_type))
        present = set(current_data.keys())
        return list(required - present)
    
    def get_optional_fields(
        self,
        observation_type: str,
        current_data: Dict[str, Any]
    ) -> List[str]:
        """Get list of optional fields not yet provided"""
        template = self.templates.get(observation_type, {})
        all_fields = set(template.keys())
        required = set(infoex_constants.get_required_fields(observation_type))
        optional = all_fields - required
        present = set(current_data.keys())
        return list(optional - present)
    
    def strip_aurora_metadata(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Remove Aurora-specific metadata for InfoEx submission"""
        # Remove any fields starting with underscore
        cleaned = {k: v for k, v in payload.items() if not k.startswith("_")}
        
        # Remove Aurora-specific fields
        aurora_fields = ["_aurora_metadata", "_aurora_extensions", "_agent_workflow"]
        for field in aurora_fields:
            cleaned.pop(field, None)
        
        return cleaned


# Create singleton instance
payload_builder = PayloadBuilder()
