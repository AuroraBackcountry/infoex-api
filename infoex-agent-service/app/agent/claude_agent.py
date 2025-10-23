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
                    # Return the entire JSON payload as extracted data
                    logger.info("extracted_json_from_claude", 
                               observation_type=obs_type,
                               fields=list(json_data.keys()))
                    return json_data
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
    
    def get_template_for_type(self, observation_type: str) -> Optional[Dict[str, Any]]:
        """Get AURORA_IDEAL template for observation type"""
        return self.templates.get(observation_type)
