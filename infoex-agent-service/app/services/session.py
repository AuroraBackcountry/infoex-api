"""Redis session management service"""

import json
import redis.asyncio as redis
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import structlog
import uuid

from app.config import settings
from app.models import Session, RequestValues, ConversationMessage

logger = structlog.get_logger()


class SessionManager:
    """Manages conversation sessions in Redis"""
    
    def __init__(self):
        """Initialize Redis connection"""
        self.redis: Optional[redis.Redis] = None
        self.ttl = settings.session_ttl_seconds
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis = redis.from_url(
                settings.effective_redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis.ping()
            logger.info("redis_connected", 
                       host=settings.redis_host,
                       port=settings.redis_port,
                       db=settings.redis_db)
        except Exception as e:
            logger.error("redis_connection_failed", error=str(e))
            raise
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis:
            await self.redis.close()
            logger.info("redis_disconnected")
    
    def _get_session_key(self, session_id: str) -> str:
        """Generate Redis key for session"""
        return f"{settings.redis_session_prefix}:{session_id}"
    
    async def create_session(self, request_values: RequestValues) -> Session:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        session = Session(
            session_id=session_id,
            created_at=now,
            last_updated=now,
            request_values=request_values,
            conversation_history=[],
            payloads={},
            metadata={}
        )
        
        # Store in Redis
        await self.save_session(session)
        
        logger.info("session_created", 
                   session_id=session_id,
                   zone=request_values.zone_name)
        
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """Retrieve session from Redis"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        key = self._get_session_key(session_id)
        
        try:
            data = await self.redis.get(key)
            if not data:
                logger.warning("session_not_found", session_id=session_id)
                return None
            
            # Parse JSON and reconstruct session
            session_data = json.loads(data)
            
            # Convert datetime strings back to datetime objects
            session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
            session_data['last_updated'] = datetime.fromisoformat(session_data['last_updated'])
            
            # Convert conversation history
            for msg in session_data.get('conversation_history', []):
                if 'timestamp' in msg:
                    msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
            
            # Reconstruct Session object
            session = Session(**session_data)
            
            logger.info("session_retrieved", 
                       session_id=session_id,
                       messages=len(session.conversation_history))
            
            return session
            
        except json.JSONDecodeError as e:
            logger.error("session_decode_error", 
                        session_id=session_id,
                        error=str(e))
            return None
        except Exception as e:
            logger.error("session_get_error",
                        session_id=session_id,
                        error=str(e))
            return None
    
    async def save_session(self, session: Session) -> bool:
        """Save session to Redis"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        key = self._get_session_key(session.session_id)
        
        try:
            # Convert to dict with ISO format datetimes
            session_dict = session.model_dump()
            
            # Convert datetime objects to ISO format strings
            session_dict['created_at'] = session.created_at.isoformat()
            session_dict['last_updated'] = session.last_updated.isoformat()
            
            # Convert conversation timestamps
            for msg in session_dict.get('conversation_history', []):
                if 'timestamp' in msg and isinstance(msg['timestamp'], datetime):
                    msg['timestamp'] = msg['timestamp'].isoformat()
            
            # Store with TTL
            data = json.dumps(session_dict)
            await self.redis.setex(key, self.ttl, data)
            
            logger.info("session_saved",
                       session_id=session.session_id,
                       ttl=self.ttl)
            
            return True
            
        except Exception as e:
            logger.error("session_save_error",
                        session_id=session.session_id,
                        error=str(e))
            return False
    
    async def update_session(self, session: Session) -> bool:
        """Update existing session"""
        session.last_updated = datetime.utcnow()
        return await self.save_session(session)
    
    async def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        key = self._get_session_key(session_id)
        
        try:
            result = await self.redis.delete(key)
            logger.info("session_deleted",
                       session_id=session_id,
                       existed=bool(result))
            return bool(result)
        except Exception as e:
            logger.error("session_delete_error",
                        session_id=session_id,
                        error=str(e))
            return False
    
    async def extend_session_ttl(self, session_id: str) -> bool:
        """Extend session TTL"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        key = self._get_session_key(session_id)
        
        try:
            result = await self.redis.expire(key, self.ttl)
            logger.info("session_ttl_extended",
                       session_id=session_id,
                       ttl=self.ttl,
                       success=result)
            return result
        except Exception as e:
            logger.error("session_extend_error",
                        session_id=session_id,
                        error=str(e))
            return False
    
    async def get_session_ttl(self, session_id: str) -> int:
        """Get remaining TTL for session"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        key = self._get_session_key(session_id)
        
        try:
            ttl = await self.redis.ttl(key)
            return ttl if ttl > 0 else 0
        except Exception as e:
            logger.error("session_ttl_error",
                        session_id=session_id,
                        error=str(e))
            return 0
    
    async def list_active_sessions(self) -> List[str]:
        """List all active session IDs"""
        if not self.redis:
            raise RuntimeError("Redis not connected")
        
        try:
            pattern = "infoex:session:*"
            keys = []
            async for key in self.redis.scan_iter(match=pattern):
                # Extract session ID from key
                session_id = key.split(":")[-1]
                keys.append(session_id)
            
            logger.info("sessions_listed", count=len(keys))
            return keys
        except Exception as e:
            logger.error("session_list_error", error=str(e))
            return []
    
    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions (Redis handles this automatically with TTL)"""
        # This is mainly for logging/monitoring purposes
        # Redis automatically removes keys when TTL expires
        active_sessions = await self.list_active_sessions()
        logger.info("session_cleanup_check", active_count=len(active_sessions))
        return len(active_sessions)


# Create a singleton instance
session_manager = SessionManager()
