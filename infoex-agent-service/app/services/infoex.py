"""InfoEx API client service"""

import httpx
from typing import Dict, Any, List, Optional, Tuple
import structlog
from datetime import datetime

from app.config import settings
from app.services.payload import payload_builder

logger = structlog.get_logger()


class InfoExClient:
    """Client for InfoEx API submissions"""
    
    def __init__(self):
        """Initialize with configuration"""
        self.base_url = settings.infoex_base_url
        self.api_key = settings.infoex_api_key
        self.operation_uuid = settings.infoex_operation_uuid
        self.headers = {
            "api_key": self.api_key,
            "operation": self.operation_uuid,
            "Content-Type": "application/json"
        }
        
    async def submit_observation(
        self,
        observation_type: str,
        payload: Dict[str, Any]
    ) -> Tuple[bool, Dict[str, Any]]:
        """Submit a single observation to InfoEx"""
        
        # Map observation types to endpoints
        endpoint_map = {
            "field_summary": "/observation/fieldSummary",
            "avalanche_observation": "/observation/avalanche",
            "avalanche_summary": "/observation/avalancheSummary",
            "hazard_assessment": "/observation/hazardAssessment",
            "snowpack_summary": "/observation/snowpackAssessment",
            "snowProfile_observation": "/observation/snowpack",
            "terrain_observation": "/observation/terrain",
            "pwl_persistent_weak_layer": "/pwl"
        }
        
        endpoint = endpoint_map.get(observation_type)
        if not endpoint:
            error_msg = f"Unknown observation type: {observation_type}"
            logger.error("unknown_observation_type", type=observation_type)
            return False, {"error": error_msg}
        
        url = f"{self.base_url}{endpoint}"
        
        # Strip Aurora metadata
        clean_payload = payload_builder.strip_aurora_metadata(payload)
        
        # Ensure state is SUBMITTED for actual submission
        clean_payload["state"] = "SUBMITTED"
        
        logger.info("submitting_to_infoex",
                   observation_type=observation_type,
                   endpoint=endpoint,
                   fields=list(clean_payload.keys()),
                   payload=clean_payload)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=clean_payload,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Check if response contains a UUID (successful submission)
                    if result.get("uuid"):
                        logger.info("submission_successful",
                                  observation_type=observation_type,
                                  uuid=result.get("uuid"))
                        
                        return True, {
                            "status": "success",
                            "uuid": result.get("uuid"),
                            "observation_type": observation_type,
                            "submitted_at": datetime.utcnow().isoformat()
                        }
                    else:
                        # 200 response but no UUID - likely an error
                        logger.error("submission_failed_no_uuid",
                                   observation_type=observation_type,
                                   response=result)
                        
                        return False, {
                            "status": "error",
                            "error": "Submission returned no UUID",
                            "response": result,
                            "observation_type": observation_type
                        }
                
                else:
                    error_data = {
                        "status": "error",
                        "status_code": response.status_code,
                        "observation_type": observation_type
                    }
                    
                    try:
                        error_response = response.json()
                        error_data["error"] = error_response
                        
                        # Extract validation errors if present
                        if "errors" in error_response:
                            validation_errors = []
                            for error in error_response["errors"]:
                                field = error.get("field", "Unknown")
                                detail = error.get("errorDetails", error.get("error", "Unknown error"))
                                validation_errors.append(f"{field}: {detail}")
                            error_data["validation_errors"] = validation_errors
                    except:
                        error_data["error"] = response.text
                    
                    logger.error("submission_failed",
                               observation_type=observation_type,
                               status_code=response.status_code,
                               error=error_data)
                    
                    return False, error_data
                    
            except httpx.TimeoutException:
                error_msg = "Request timeout"
                logger.error("submission_timeout", observation_type=observation_type)
                return False, {"error": error_msg, "status": "timeout"}
                
            except Exception as e:
                error_msg = str(e)
                logger.error("submission_exception",
                           observation_type=observation_type,
                           error=error_msg)
                return False, {"error": error_msg, "status": "exception"}
    
    async def submit_multiple(
        self,
        observations: List[Tuple[str, Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """Submit multiple observations"""
        results = {
            "success": True,
            "total": len(observations),
            "successful": 0,
            "failed": 0,
            "submissions": []
        }
        
        for obs_type, payload in observations:
            success, result = await self.submit_observation(obs_type, payload)
            
            submission_result = {
                "observation_type": obs_type,
                "success": success,
                "result": result
            }
            
            if success:
                results["successful"] += 1
            else:
                results["failed"] += 1
                results["success"] = False
            
            results["submissions"].append(submission_result)
        
        logger.info("batch_submission_complete",
                   total=results["total"],
                   successful=results["successful"],
                   failed=results["failed"])
        
        return results
    
    async def test_connection(self) -> bool:
        """Test connection to InfoEx API"""
        try:
            url = f"{self.base_url}/observation/constants/"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    logger.info("infoex_connection_test_successful")
                    return True
                else:
                    logger.error("infoex_connection_test_failed",
                               status_code=response.status_code)
                    return False
                    
        except Exception as e:
            logger.error("infoex_connection_test_exception", error=str(e))
            return False
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """Get available locations for the operation"""
        try:
            url = f"{self.base_url}/location"
            params = {
                "operationUUID": self.operation_uuid,
                "type": "OPERATING_ZONE"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    locations = response.json()
                    logger.info("locations_retrieved", count=len(locations))
                    return locations
                else:
                    logger.error("locations_retrieval_failed",
                               status_code=response.status_code)
                    return []
                    
        except Exception as e:
            logger.error("locations_retrieval_exception", error=str(e))
            return []


# Create singleton instance
infoex_client = InfoExClient()
