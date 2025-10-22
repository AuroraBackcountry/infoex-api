"""Configuration management for InfoEx Agent Service"""

from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator, model_validator
import json
import os
from urllib.parse import urlparse


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Anthropic API
    anthropic_api_key: str = Field(..., description="Anthropic API key")
    claude_model: str = Field(default="claude-3-opus-20240229", description="Claude model to use")
    claude_max_tokens: int = Field(default=1024, description="Max tokens for Claude response")
    claude_temperature: float = Field(default=0.3, description="Temperature for Claude responses")
    
    # Redis Configuration - Can be set via REDIS_URL or individual components
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    redis_host: str = Field(default="localhost", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_db: int = Field(default=0, description="Redis database number")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_ssl: bool = Field(default=False, description="Use SSL for Redis connection")
    
    # Environment selection
    environment: str = Field(default="staging", description="Active environment (staging/production)")
    
    # InfoEx Staging Configuration
    staging_api_key: Optional[str] = Field(default=None, description="Staging API key")
    staging_url: str = Field(default="https://staging-can.infoex.ca/safe-server")
    
    # InfoEx Production Configuration
    production_api_key: Optional[str] = Field(default=None, description="Production API key")
    production_url: str = Field(default="https://can.infoex.ca/safe-server")
    
    # Shared InfoEx Configuration
    operation_uuid: str = Field(..., description="Aurora Backcountry operation UUID")
    
    # Active InfoEx Configuration (set based on environment)
    infoex_api_key: Optional[str] = Field(default=None, description="Active InfoEx API key")
    infoex_operation_uuid: Optional[str] = Field(default=None, description="Active operation UUID")
    infoex_base_url: Optional[str] = Field(default=None, description="Active InfoEx base URL")
    
    # Service Configuration
    service_host: str = Field(default="0.0.0.0", description="Service host")
    service_port: int = Field(default=8000, description="Service port")
    port: Optional[int] = Field(default=None, description="Port from Render")
    log_level: str = Field(default="INFO", description="Logging level")
    session_ttl_seconds: int = Field(default=3600, description="Session TTL in seconds")
    max_conversation_length: int = Field(default=50, description="Max messages in conversation")
    
    # CORS Configuration
    cors_allowed_origins: List[str] = Field(
        default=["http://localhost:5678"],
        description="Allowed CORS origins"
    )
    
    # Rate Limiting
    rate_limit_requests: int = Field(default=100, description="Rate limit requests")
    rate_limit_period: int = Field(default=60, description="Rate limit period in seconds")
    
    # Redis Session Configuration
    redis_session_prefix: str = Field(default="infoex:session", description="Redis key prefix for sessions")
    
    @validator("cors_allowed_origins", pre=True)
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list"""
        if isinstance(v, str):
            # Try to parse as JSON first
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Otherwise split by comma
                return [origin.strip() for origin in v.split(",")]
        return v
    
    @model_validator(mode='after')
    def configure_environment(self):
        """Configure active InfoEx settings based on environment"""
        env = self.environment.lower()
        
        # Set active InfoEx configuration based on environment
        if env == "production":
            self.infoex_api_key = self.production_api_key or self.infoex_api_key
            self.infoex_base_url = self.production_url
        else:  # Default to staging
            self.infoex_api_key = self.staging_api_key or self.infoex_api_key
            self.infoex_base_url = self.staging_url
        
        # Operation UUID is the same for both environments
        self.infoex_operation_uuid = self.operation_uuid
        
        # Validate that we have required InfoEx credentials
        if not self.infoex_api_key:
            raise ValueError(f"Missing InfoEx API key for {env} environment")
        if not self.infoex_operation_uuid:
            raise ValueError(f"Missing InfoEx operation UUID for {env} environment")
        
        # Parse Redis URL if provided (for Render deployment)
        if self.redis_url:
            parsed = urlparse(self.redis_url)
            if parsed.hostname:
                self.redis_host = parsed.hostname
            if parsed.port:
                self.redis_port = parsed.port
            if parsed.password:
                self.redis_password = parsed.password
            if parsed.scheme == "rediss":
                self.redis_ssl = True
            if parsed.path and len(parsed.path) > 1:
                try:
                    self.redis_db = int(parsed.path[1:])
                except ValueError:
                    pass
        
        # Use PORT from Render if available
        if self.port:
            self.service_port = self.port
        
        return self
    
    @property
    def infoex_environment(self) -> str:
        """Get the InfoEx environment name for logging"""
        return self.environment
    
    @property
    def effective_redis_url(self) -> str:
        """Get the effective Redis URL (either provided or constructed)"""
        if self.redis_url:
            return self.redis_url
        
        protocol = "rediss" if self.redis_ssl else "redis"
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Create a global settings instance
settings = Settings()
