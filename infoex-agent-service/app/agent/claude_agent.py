"""Claude agent for InfoEx payload construction"""

import json
from typing import Dict, List, Any, Optional, Tuple
import anthropic
import structlog
from datetime import datetime

from app.config import settings
from app.models import (
    RequestValues, 
    ConversationMessage, 
    Session,
    PayloadStatus
)
from app.agent.constants import infoex_constants
from app.agent.prompts import build_system_prompt
from app.agent.knowledge_base import get_knowledge_base

logger = structlog.get_logger()


class ClaudeAgent:
    """Handles conversation with Claude for payload construction"""
    
    def __init__(self):
        """Initialize Claude client and load templates"""
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        self.knowledge_base = get_knowledge_base()
        self.templates = self.knowledge_base.payloads  # Use knowledge base templates
    
    def process_message(
        self, 
        session: Session,
        message: str
    ) -> Tuple[str, Session]:
        """Process a user message and return Claude's response"""
        
        # Add user message to history
        user_msg = ConversationMessage(
            role="user",
            content=message,
            timestamp=datetime.utcnow()
        )
        session.conversation_history.append(user_msg)
        
        # Build messages for Claude
        messages = self._build_claude_messages(session)
        
        # Get system prompt with request values
        system_prompt = build_system_prompt(
            session.request_values,
            infoex_constants
        )
        
        try:
            # Call Claude
            response = self.client.messages.create(
                model=settings.claude_model,
                max_tokens=settings.claude_max_tokens,
                temperature=settings.claude_temperature,
                system=system_prompt,
                messages=messages
            )
            
            # Extract response text
            response_text = response.content[0].text
            
            # Add Claude's response to history
            assistant_msg = ConversationMessage(
                role="assistant",
                content=response_text,
                timestamp=datetime.utcnow()
            )
            session.conversation_history.append(assistant_msg)
            
            # Update payloads based on conversation
            session = self._update_payloads_from_conversation(session, message, response_text)
            
            # Update session timestamp
            session.last_updated = datetime.utcnow()
            
            logger.info("claude_response_processed",
                       session_id=session.session_id,
                       message_length=len(message),
                       response_length=len(response_text))
            
            return response_text, session
            
        except Exception as e:
            logger.error("claude_processing_error", 
                        session_id=session.session_id,
                        error=str(e))
            raise
    
    def _build_claude_messages(self, session: Session) -> List[Dict[str, str]]:
        """Build message history for Claude"""
        messages = []
        
        # If there's n8n context and this is the first message, include it
        if session.metadata.get("n8n_context") and len(session.conversation_history) == 1:
            context_msg = (
                "Context from n8n conversation:\n"
                f"{session.metadata['n8n_context']}\n\n"
                "Based on this context, process the following request:"
            )
            messages.append({
                "role": "user",
                "content": context_msg
            })
            messages.append({
                "role": "assistant", 
                "content": "I understand the context. I'll process your request based on this information."
            })
        
        # Include conversation history (limited to avoid token limits)
        history_limit = settings.max_conversation_length
        relevant_history = session.conversation_history[-history_limit:]
        
        for msg in relevant_history:
            if msg.role in ["user", "assistant"]:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Add current payload status as context
        if session.payloads:
            status_text = "\n\nCurrent payload status:\n"
            for obs_type, payload in session.payloads.items():
                if payload.status == "ready":
                    status_text += f"- {obs_type}: Ready for submission\n"
                elif payload.status == "incomplete":
                    status_text += f"- {obs_type}: Missing {', '.join(payload.missing_fields)}\n"
            
            if messages and messages[-1]["role"] == "assistant":
                messages[-1]["content"] += status_text
        
        # Inject relevant knowledge for active observation types
        if session.payloads:
            knowledge_text = "\n\n[REFERENCE KNOWLEDGE]\n"
            for obs_type in session.payloads:
                context = self.knowledge_base.format_for_claude_context(obs_type)
                knowledge_text += f"\n{context}\n"
            
            # Add as system context at beginning of conversation
            if messages:
                messages.insert(0, {
                    "role": "user", 
                    "content": f"[SYSTEM CONTEXT]{knowledge_text}\n[END CONTEXT]"
                })
                messages.insert(1, {
                    "role": "assistant",
                    "content": "I understand the InfoEx payload requirements. I'll help ensure accurate submission."
                })
        
        return messages
    
    def _update_payloads_from_conversation(
        self, 
        session: Session,
        user_message: str,
        claude_response: str
    ) -> Session:
        """Extract and update payload data from conversation"""
        
        # This is a simplified version - in production, you'd want more sophisticated
        # extraction logic, possibly using Claude itself to extract structured data
        
        # Look for observation types mentioned
        mentioned_types = self._detect_observation_types(user_message, claude_response)
        
        # Initialize payloads for mentioned types
        for obs_type in mentioned_types:
            if obs_type not in session.payloads:
                session.payloads[obs_type] = PayloadStatus(
                    observation_type=obs_type,
                    status="incomplete",
                    missing_fields=infoex_constants.get_required_fields(obs_type),
                    data={
                        "obDate": session.request_values.date,
                        "locationUUIDs": session.request_values.location_uuids,
                        "operationUUID": session.request_values.operation_id,
                        "state": "IN_REVIEW"
                    }
                )
        
        # Extract data from conversation (simplified example)
        # In production, this would be much more sophisticated
        for obs_type, payload in session.payloads.items():
            if payload.status != "submitted":
                # Update data based on conversation
                extracted_data = self._extract_data_for_type(
                    obs_type, 
                    user_message,
                    session.conversation_history,
                    claude_response
                )
                
                # Merge extracted data
                payload.data.update(extracted_data)
                
                # Check if all required fields are present
                required = set(infoex_constants.get_required_fields(obs_type))
                present = set(payload.data.keys())
                missing = required - present
                
                payload.missing_fields = list(missing)
                payload.status = "ready" if not missing else "incomplete"
                
                logger.info("payload_status_updated",
                           observation_type=obs_type,
                           status=payload.status,
                           required_fields=list(required),
                           present_fields=list(present),
                           missing_fields=list(missing))
        
        return session
    
    def _detect_observation_types(
        self, 
        user_message: str, 
        claude_response: str
    ) -> List[str]:
        """Detect which observation types are being discussed"""
        types = []
        
        # Simple keyword detection - could be enhanced with NLP
        keywords = {
            "field_summary": ["field summary", "daily summary", "operational summary"],
            "avalanche_observation": ["avalanche", "size 2", "storm slab", "wind slab"],
            "avalanche_summary": ["avalanche activity", "avalanches observed"],
            "hazard_assessment": ["hazard", "rating", "alpine", "treeline"],
            "snowpack_summary": ["snowpack", "layers", "snow structure"],
            "terrain_observation": ["terrain", "ates", "strategic mindset"]
        }
        
        combined_text = (user_message + " " + claude_response).lower()
        
        for obs_type, terms in keywords.items():
            if any(term in combined_text for term in terms):
                types.append(obs_type)
        
        return types
    
    def _extract_data_for_type(
        self,
        obs_type: str,
        current_message: str,
        conversation_history: List[ConversationMessage],
        claude_response: str = None
    ) -> Dict[str, Any]:
        """Extract relevant data for observation type from conversation"""
        
        import re
        import json
        
        # First, check if Claude generated a JSON payload in the response
        if claude_response:
            # Look for JSON block in Claude's response
            json_match = re.search(r'```json\s*\n(.*?)\n```', claude_response, re.DOTALL)
            if json_match:
                try:
                    json_data = json.loads(json_match.group(1))
                    
                    # Field mapping corrections for common mistakes
                    field_mappings = {
                        # Common date field mappings
                        "observationDateTime": "obDate",
                        "observationDate": "obDate",
                        "date": "obDate",
                        
                        # Common field name variations
                        "operation_id": "operationUUID",
                        "location_uuids": "locationUUIDs",
                        "operationId": "operationUUID",
                        
                        # avalanche_summary specific
                        "avalanches_observed": "avalanchesObserved",
                        "percent_area_observed": "percentAreaObserved",
                        "percentArea": "percentAreaObserved",
                        
                        # avalanche_observation specific
                        "observation_time": "obTime",
                        "number": "num",
                        "avalanche_type": "character",
                        "type": "character",
                        "min_size": "sizeMin",
                        "max_size": "sizeMax",
                        "depth_average": "depthAvg",
                        "depth_min": "depthMin",
                        "depth_max": "depthMax",
                        
                        # field_summary specific
                        "start_time": "obStartTime",
                        "end_time": "obEndTime",
                        "temperature_high": "tempHigh",
                        "temperature_low": "tempLow",
                        "wind_speed": "windSpeed",
                        "wind_direction": "windDirection",
                        "sky_condition": "sky",
                        "precipitation": "precip",
                        "new_snow_24h": "hn24",
                        "snow_height": "hs",
                        
                        # hazard_assessment specific
                        "assessment_time": "obTime",
                        "type": "assessmentType",
                        "problems": "avalancheProblems",
                        "ratings": "hazardRatings",
                        
                        # terrain_observation specific
                        "ates": "atesRating",
                        "terrain": "terrainFeature",
                        "mindset": "strategicMindset",
                        "percent_observed": "percentAreaObserved"
                    }
                    
                    # Apply field mappings
                    corrected_data = {}
                    for key, value in json_data.items():
                        # Check if this field needs to be renamed
                        correct_key = field_mappings.get(key, key)
                        corrected_data[correct_key] = value
                    
                    # Apply observation-type specific value conversions
                    corrected_data = self._apply_value_conversions(obs_type, corrected_data)
                    
                    logger.info("extracted_json_from_claude", 
                               observation_type=obs_type,
                               fields=list(corrected_data.keys()))
                    return corrected_data
                except json.JSONDecodeError:
                    logger.warning("failed_to_parse_claude_json", observation_type=obs_type)
        
        # Fallback to basic extraction
        extracted = {}
        
        # Example extractions for specific types
        if obs_type == "avalanche_observation":
            # Look for size mentions
            size_match = re.search(r'size\s*(\d+(?:\.\d+)?)', current_message.lower())
            if size_match:
                extracted["sizeMin"] = float(size_match.group(1))
                extracted["sizeMax"] = float(size_match.group(1))
            
            # Look for trigger types
            if "skier" in current_message.lower():
                extracted["trigger"] = "Sa"  # Skier accidental
            elif "natural" in current_message.lower():
                extracted["trigger"] = "Na"  # Natural
        
        elif obs_type == "field_summary":
            # Look for time mentions
            time_match = re.search(r'(\d{1,2}:\d{2})', current_message)
            if time_match:
                if "start" in current_message.lower():
                    extracted["obStartTime"] = time_match.group(1)
                elif "end" in current_message.lower():
                    extracted["obEndTime"] = time_match.group(1)
        
        return extracted
    
    def _apply_value_conversions(self, obs_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply observation-type specific value conversions"""
        
        # avalanche_summary conversions
        if obs_type == "avalanche_summary":
            # Convert boolean/yes/no to proper enum
            if "avalanchesObserved" in data:
                val = data["avalanchesObserved"]
                if isinstance(val, bool) or str(val).lower() in ["yes", "true", "1"]:
                    data["avalanchesObserved"] = "New avalanches"
                elif str(val).lower() in ["no", "false", "0"]:
                    data["avalanchesObserved"] = "No new avalanches"
                elif str(val).lower() in ["sluffing", "pinwheeling"]:
                    data["avalanchesObserved"] = "Sluffing/Pinwheeling only"
            
            # Ensure percentAreaObserved is numeric
            if "percentAreaObserved" in data and isinstance(data["percentAreaObserved"], str):
                try:
                    data["percentAreaObserved"] = float(data["percentAreaObserved"])
                except:
                    pass
        
        # avalanche_observation conversions
        elif obs_type == "avalanche_observation":
            # Convert trigger descriptions to codes
            trigger_mappings = {
                "natural": "Na", "skier": "Sa", "skier triggered": "Sa",
                "snowmobile": "Ma", "explosive": "Xa", "cornice": "Nc",
                "unknown": "U", "vehicle": "Va"
            }
            if "trigger" in data and data["trigger"].lower() in trigger_mappings:
                data["trigger"] = trigger_mappings[data["trigger"].lower()]
            
            # Convert character codes to full names
            character_mappings = {
                "L": "LOOSE_DRY_AVALANCHE", "WL": "LOOSE_WET_AVALANCHE",
                "SS": "STORM_SLAB", "WS": "WIND_SLAB", "PS": "PERSISTENT_SLAB",
                "DPS": "DEEP_PERSISTENT_SLAB", "WS2": "WET_SLAB",
                "G": "GLIDE", "C": "CORNICE", "U": "UNKNOWN",
                "storm slab": "STORM_SLAB", "wind slab": "WIND_SLAB",
                "wet slab": "WET_SLAB", "persistent slab": "PERSISTENT_SLAB", 
                "deep persistent": "DEEP_PERSISTENT_SLAB", "cornice": "CORNICE",
                "glide": "GLIDE", "loose dry": "LOOSE_DRY_AVALANCHE",
                "loose wet": "LOOSE_WET_AVALANCHE"
            }
            if "character" in data:
                char_val = str(data["character"]).lower()
                # First try lowercase lookup
                if char_val in character_mappings:
                    data["character"] = character_mappings[char_val]
                # Then try uppercase code lookup
                elif char_val.upper() in character_mappings:
                    data["character"] = character_mappings[char_val.upper()]
                # Finally try to match by checking if it already has the right format
                elif char_val.upper().replace(" ", "_") in ["LOOSE_DRY_AVALANCHE", "LOOSE_WET_AVALANCHE",
                                                             "STORM_SLAB", "WIND_SLAB", "PERSISTENT_SLAB",
                                                             "DEEP_PERSISTENT_SLAB", "WET_SLAB", "GLIDE",
                                                             "CORNICE", "UNKNOWN"]:
                    data["character"] = char_val.upper().replace(" ", "_")
            
            # Ensure size is string
            if "size" in data:
                data["size"] = str(data["size"])
            
            # Ensure aspects are arrays
            if "aspectFrom" in data and isinstance(data["aspectFrom"], list):
                data["aspectFrom"] = data["aspectFrom"][0] if data["aspectFrom"] else "N"
            if "aspectTo" in data and isinstance(data["aspectTo"], list):
                data["aspectTo"] = data["aspectTo"][-1] if data["aspectTo"] else "N"
        
        # field_summary conversions
        elif obs_type == "field_summary":
            # Wind speed mappings
            wind_mappings = {
                "calm": "C", "light": "L", "moderate": "M",
                "strong": "S", "extreme": "X", "variable": "V"
            }
            for field in ["windSpeed", "amWindSpeed", "pmWindSpeed"]:
                if field in data and isinstance(data[field], str):
                    wind_val = data[field].lower()
                    if wind_val in wind_mappings:
                        data[field] = wind_mappings[wind_val]
            
            # Sky condition mappings
            sky_mappings = {
                "clear": "CLR", "few": "FEW", "scattered": "SCT",
                "broken": "BKN", "overcast": "OVC", "obscured": "X"
            }
            for field in ["sky", "amSky", "pmSky"]:
                if field in data and isinstance(data[field], str):
                    sky_val = data[field].lower()
                    if sky_val in sky_mappings:
                        data[field] = sky_mappings[sky_val]
            
            # Precipitation mappings
            if "precip" in data:
                precip_val = str(data["precip"]).lower()
                if "no" in precip_val or "nil" in precip_val:
                    data["precip"] = "NIL"
                elif "light snow" in precip_val:
                    data["precip"] = "S1"
                elif "moderate snow" in precip_val:
                    data["precip"] = "S2"
                elif "heavy snow" in precip_val:
                    data["precip"] = "S3"
                elif "rain" in precip_val:
                    data["precip"] = "R"
        
        # terrain_observation conversions
        elif obs_type == "terrain_observation":
            # ATES rating normalization
            if "atesRating" in data:
                ates_val = str(data["atesRating"]).title()
                if ates_val in ["Simple", "Challenging", "Complex"]:
                    data["atesRating"] = ates_val
            
            # Strategic mindset normalization
            mindset_mappings = {
                "assessment": "Assessment", "stepping out": "Stepping Out",
                "status quo": "Status Quo", "stepping back": "Stepping Back",
                "maintenance": "Maintenance", "entrenchment": "Entrenchment",
                "open season": "Open Season", "spring diurnal": "Spring Diurnal"
            }
            if "strategicMindset" in data and data["strategicMindset"].lower() in mindset_mappings:
                data["strategicMindset"] = mindset_mappings[data["strategicMindset"].lower()]
        
        # Common conversions for all types
        # Ensure locationUUIDs is always an array
        if "locationUUIDs" in data and not isinstance(data["locationUUIDs"], list):
            data["locationUUIDs"] = [data["locationUUIDs"]]
        
        # Ensure numeric values are proper type
        numeric_fields = ["tempHigh", "tempLow", "elevationMin", "elevationMax",
                         "hs", "hn24", "hst", "percentAreaObserved", "sizeMin", "sizeMax",
                         "depthMin", "depthMax", "depthAvg", "width", "length"]
        for field in numeric_fields:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = float(data[field])
                except:
                    pass
        
        return data
    
    def get_template_for_type(self, observation_type: str) -> Optional[Dict[str, Any]]:
        """Get AURORA_IDEAL template for observation type"""
        return self.templates.get(observation_type)
