"""Pydantic models for request/response validation"""

from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
import re


class FixedValues(BaseModel):
    """Fixed values provided by n8n for each request"""
    operation_id: str = Field(..., description="InfoEx operation UUID")
    location_uuids: List[str] = Field(..., description="List of location UUIDs")
    zone_name: str = Field(..., description="Zone name for context")
    date: str = Field(..., description="Report date in MM/DD/YYYY format")
    user_name: Optional[str] = Field(default=None, description="Name of the user submitting")
    user_id: Optional[str] = Field(default=None, description="UUID of the user")
    
    @validator("date")
    def validate_date_format(cls, v):
        """Ensure date is in MM/DD/YYYY format"""
        pattern = r"^\d{2}/\d{2}/\d{4}$"
        if not re.match(pattern, v):
            raise ValueError(f"Date must be in MM/DD/YYYY format, got: {v}")
        
        # Basic date validation
        try:
            month, day, year = map(int, v.split("/"))
            if not (1 <= month <= 12):
                raise ValueError(f"Invalid month: {month}")
            if not (1 <= day <= 31):
                raise ValueError(f"Invalid day: {day}")
            if not (1900 <= year <= 2100):
                raise ValueError(f"Invalid year: {year}")
        except Exception as e:
            raise ValueError(f"Invalid date: {v} - {str(e)}")
        
        return v


class ProcessReportRequest(BaseModel):
    """Request model for processing a report message"""
    session_id: str = Field(..., description="Unique session identifier")
    message: str = Field(..., description="User message to process")
    fixed_values: FixedValues = Field(..., description="Fixed values from n8n")


class ProcessReportResponse(BaseModel):
    """Response model for processed report - plain text"""
    response: str = Field(..., description="Claude's plain text response")


class SubmissionRequest(BaseModel):
    """Request model for submitting to InfoEx"""
    session_id: str = Field(..., description="Session ID with completed payloads")
    submission_types: List[str] = Field(
        ...,
        description="List of observation types to submit",
        example=["field_summary", "avalanche_observation", "hazard_assessment"]
    )


class SubmissionResponse(BaseModel):
    """Response model for InfoEx submission results"""
    success: bool = Field(..., description="Overall submission success")
    message: str = Field(..., description="Summary message")
    submissions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Individual submission results"
    )


class SessionStatus(BaseModel):
    """Session status information"""
    session_id: str
    status: Literal["active", "expired", "error"]
    payloads_ready: List[str] = Field(
        default_factory=list,
        description="List of completed payloads ready for submission"
    )
    missing_data: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Missing data by observation type"
    )
    last_updated: datetime
    conversation_length: int = Field(0, description="Number of messages in conversation")
    
    
class PayloadStatus(BaseModel):
    """Status of a specific payload being built"""
    observation_type: str
    status: Literal["incomplete", "ready", "submitted", "error"]
    missing_fields: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
    data: Dict[str, Any] = Field(default_factory=dict)


class ConversationMessage(BaseModel):
    """Single message in conversation history"""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    """Complete session data"""
    session_id: str
    created_at: datetime
    last_updated: datetime
    fixed_values: FixedValues
    conversation_history: List[ConversationMessage] = Field(default_factory=list)
    payloads: Dict[str, PayloadStatus] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    code: Optional[str] = Field(None, description="Error code")


class HealthCheckResponse(BaseModel):
    """Health check response"""
    status: Literal["healthy", "degraded", "unhealthy"]
    timestamp: datetime
    checks: Dict[str, bool] = Field(
        default_factory=dict,
        description="Individual service health checks"
    )
    version: str = Field(..., description="Service version")
