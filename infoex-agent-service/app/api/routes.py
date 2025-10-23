"""API route handlers for InfoEx Claude Agent"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List
import structlog

from app.models import (
    ProcessReportRequest,
    ProcessReportResponse,
    SubmissionRequest,
    SubmissionResponse,
    SessionStatus,
    ErrorResponse,
    HealthCheckResponse
)
from app.services.session import session_manager
from app.services.payload import payload_builder
from app.services.infoex import infoex_client
from app.agent.claude_agent import ClaudeAgent
from datetime import datetime
from app import __version__

logger = structlog.get_logger()

# Create router
router = APIRouter()

# Initialize Claude agent
claude_agent = ClaudeAgent()


@router.post("/api/process-report", response_model=ProcessReportResponse)
async def process_report(request: ProcessReportRequest):
    """Process a report message through Claude"""
    try:
        # Get or create session
        session = await session_manager.get_session(request.session_id)
        
        if not session:
            # Create new session with fixed values
            session = await session_manager.create_session(request.fixed_values)
            # Update session ID to match request
            session.session_id = request.session_id
            await session_manager.save_session(session)
        
        # Process message with Claude
        response_text, updated_session = claude_agent.process_message(
            session,
            request.message
        )
        
        # Save updated session
        await session_manager.save_session(updated_session)
        
        # Check if auto-submit is enabled and payloads are ready
        if request.auto_submit and "ready for" in response_text.lower() and "submission" in response_text.lower():
            # Log payload states for debugging
            logger.info("checking_payloads_for_submission",
                       session_id=request.session_id,
                       payloads_count=len(updated_session.payloads),
                       payload_states={k: v.status for k, v in updated_session.payloads.items()})
            
            # Find which payloads are ready
            ready_types = []
            for obs_type, payload in updated_session.payloads.items():
                if payload.status == "ready":
                    ready_types.append(obs_type)
            
            if ready_types:
                logger.info("submitting_ready_payloads",
                           session_id=request.session_id,
                           ready_types=ready_types)
                
                # Auto-submit ready payloads
                submission_results = []
                for obs_type in ready_types:
                    # Build payload
                    payload_data, errors = payload_builder.build_payload(obs_type, updated_session)
                    
                    if not errors:
                        # Submit to InfoEx
                        success, result = await infoex_client.submit_observation(obs_type, payload_data)
                        
                        if success:
                            submission_results.append(f"{obs_type}: Submitted (UUID: {result.get('uuid')})")
                            updated_session.payloads[obs_type].status = "submitted"
                        else:
                            submission_results.append(f"{obs_type}: Failed - {result.get('error', 'Unknown error')}")
                    else:
                        submission_results.append(f"{obs_type}: Validation errors - {', '.join(errors)}")
                
                # Save updated session with submission status
                await session_manager.save_session(updated_session)
                
                # Append submission results to response
                response_text += f"\n\nAuto-submission results:\n" + "\n".join(submission_results)
            else:
                logger.warning("no_ready_payloads_despite_response",
                              session_id=request.session_id,
                              response_contains_ready=("ready for" in response_text.lower()),
                              payloads_count=len(updated_session.payloads))
        
        logger.info("report_processed",
                   session_id=request.session_id,
                   message_length=len(request.message),
                   response_length=len(response_text),
                   auto_submit=request.auto_submit)
        
        return ProcessReportResponse(response=response_text)
        
    except Exception as e:
        logger.error("process_report_error",
                    session_id=request.session_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/submit-to-infoex", response_model=SubmissionResponse)
async def submit_to_infoex(request: SubmissionRequest):
    """Submit completed payloads to InfoEx"""
    try:
        # Get session
        session = await session_manager.get_session(request.session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build payloads for requested types
        submissions = []
        overall_success = True
        messages = []
        
        for obs_type in request.submission_types:
            if obs_type not in session.payloads:
                messages.append(f"{obs_type}: Not initialized in session")
                overall_success = False
                continue
            
            # Build payload
            payload, errors = payload_builder.build_payload(obs_type, session)
            
            if errors:
                submission = {
                    "observation_type": obs_type,
                    "success": False,
                    "errors": errors
                }
                submissions.append(submission)
                messages.append(f"{obs_type}: Validation errors")
                overall_success = False
                continue
            
            # Submit to InfoEx
            success, result = await infoex_client.submit_observation(obs_type, payload)
            
            submission = {
                "observation_type": obs_type,
                "success": success,
                "result": result
            }
            submissions.append(submission)
            
            if success:
                messages.append(f"{obs_type}: Submitted (UUID: {result.get('uuid')})")
                # Update payload status
                session.payloads[obs_type].status = "submitted"
            else:
                messages.append(f"{obs_type}: Failed - {result.get('error', 'Unknown error')}")
                overall_success = False
        
        # Save updated session
        await session_manager.save_session(session)
        
        # Build summary message
        summary = f"Processed {len(submissions)} submissions. "
        if overall_success:
            summary += "All successful!"
        else:
            failed = sum(1 for s in submissions if not s["success"])
            summary += f"{failed} failed."
        
        logger.info("submission_complete",
                   session_id=request.session_id,
                   total=len(submissions),
                   success=overall_success)
        
        return SubmissionResponse(
            success=overall_success,
            message=summary + " Details: " + " | ".join(messages),
            submissions=submissions
        )
        
    except Exception as e:
        logger.error("submission_error",
                    session_id=request.session_id,
                    error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/session/{session_id}/status", response_model=SessionStatus)
async def get_session_status(session_id: str):
    """Get current session status"""
    try:
        session = await session_manager.get_session(session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Build status
        payloads_ready = []
        missing_data = {}
        
        for obs_type, payload in session.payloads.items():
            if payload.status == "ready":
                payloads_ready.append(obs_type)
            elif payload.status == "incomplete":
                missing_data[obs_type] = payload.missing_fields
        
        # Get TTL
        ttl = await session_manager.get_session_ttl(session_id)
        status = "active" if ttl > 0 else "expired"
        
        return SessionStatus(
            session_id=session_id,
            status=status,
            payloads_ready=payloads_ready,
            missing_data=missing_data,
            last_updated=session.last_updated,
            conversation_length=len(session.conversation_history)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("status_error", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/api/session/{session_id}/clear")
async def clear_session(session_id: str):
    """Clear a session and start fresh"""
    try:
        deleted = await session_manager.delete_session(session_id)
        
        if deleted:
            return {"message": "Session cleared successfully."}
        else:
            return {"message": "Session not found or already expired."}
            
    except Exception as e:
        logger.error("clear_session_error", session_id=session_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    checks = {}
    
    # Check Redis
    try:
        await session_manager.redis.ping()
        checks["redis"] = True
    except:
        checks["redis"] = False
    
    # Check Claude
    try:
        # Just verify we have API key
        checks["claude"] = bool(claude_agent.client.api_key)
    except:
        checks["claude"] = False
    
    # Check InfoEx
    try:
        checks["infoex"] = await infoex_client.test_connection()
    except:
        checks["infoex"] = False
    
    # Overall status
    all_healthy = all(checks.values())
    status = "healthy" if all_healthy else "degraded" if any(checks.values()) else "unhealthy"
    
    return HealthCheckResponse(
        status=status,
        timestamp=datetime.utcnow(),
        checks=checks,
        version=__version__
    )


@router.get("/api/locations")
async def get_locations():
    """Get available InfoEx locations"""
    try:
        locations = await infoex_client.get_locations()
        return {
            "locations": locations,
            "count": len(locations)
        }
    except Exception as e:
        logger.error("get_locations_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
