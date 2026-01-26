"""
A2A Client for Gateway

Handles communication with ADK agents via A2A protocol.
"""

import uuid
import json
import httpx
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field


@dataclass
class A2AResponse:
    """A2A JSON-RPC 2.0 response."""
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    
    @classmethod
    def success(cls, result: Dict[str, Any], request_id: Optional[str] = None) -> "A2AResponse":
        return cls(result=result, id=request_id)
    
    @classmethod
    def error_response(cls, code: int, message: str, request_id: Optional[str] = None) -> "A2AResponse":
        """Create an error response (renamed from 'error' to avoid conflict)."""
        return cls(error={"code": code, "message": message}, id=request_id)


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    name: str
    url: str
    description: str = ""


class A2AClient:
    """Client for communicating with ADK agents via A2A protocol."""
    
    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout
        self._agents: Dict[str, AgentInfo] = {}
        self._http_client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(timeout=self.timeout)
        return self._http_client
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None
    
    def register_agent(self, name: str, url: str, description: str = ""):
        """Register an agent for communication."""
        self._agents[name] = AgentInfo(name=name, url=url, description=description)
    
    async def discover_agent(self, url: str) -> Optional[Dict[str, Any]]:
        """Fetch an agent's card from /.well-known/agent.json."""
        client = await self._get_client()
        try:
            response = await client.get(f"{url}/.well-known/agent.json")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"Failed to discover agent at {url}: {e}")
            return None
    
    async def create_session(
        self,
        agent_name: str,
        user_id: str,
        session_id: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> A2AResponse:
        """Create an ADK session before calling /run."""
        if agent_name not in self._agents:
            return A2AResponse.error_response(-32001, f"Unknown agent: {agent_name}")
        
        agent = self._agents[agent_name]
        # ADK app name matches the directory name
        app_name = agent_name 
        
        client = await self._get_client()
        try:
            # ADK session creation endpoint: POST /apps/{app_name}/users/{user_id}/sessions/{session_id}
            url = f"{agent.url}/apps/{app_name}/users/{user_id}/sessions/{session_id}"
            response = await client.post(
                url,
                json=initial_state or {},
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return A2AResponse.success(response.json(), session_id)
            elif response.status_code == 409:
                # Session already exists - this is OK, we can proceed
                return A2AResponse.success({"id": session_id, "exists": True}, session_id)
            else:
                return A2AResponse.error_response(-32004, f"Failed to create session: {response.status_code} {response.text}")
        except httpx.ConnectError as e:
            return A2AResponse.error_response(-32005, f"Session creation failed: Cannot connect to {agent.url}. Is the agent running? Error: {str(e)}")
        except httpx.TimeoutException as e:
            return A2AResponse.error_response(-32005, f"Session creation failed: Timeout connecting to {agent.url}. Error: {str(e)}")
        except Exception as e:
            error_msg = str(e) if str(e) else repr(e)
            return A2AResponse.error_response(-32005, f"Session creation failed: {error_msg} (URL: {agent.url})")
    
    async def send_task(
        self,
        agent_name: str,
        skill: str,
        payload: Dict[str, Any],
        task_id: Optional[str] = None
    ) -> A2AResponse:
        """Send a task to an ADK agent."""
        if agent_name not in self._agents:
            return A2AResponse.error_response(-32001, f"Unknown agent: {agent_name}")
        
        agent = self._agents[agent_name]
        task_id = task_id or str(uuid.uuid4())
        user_id = payload.get("user_id", "default")
        
        # Create session first (idempotent - will succeed if already exists)
        session_result = await self.create_session(agent_name, user_id, task_id)
        if session_result.error is not None:
            # If session already exists (409), that's OK - proceed
            error_msg = ""
            if isinstance(session_result.error, dict):
                error_msg = session_result.error.get("message", "")
            else:
                error_msg = str(session_result.error)
            if "already exists" not in error_msg.lower():
                return session_result
        
        # ADK agents expect camelCase field names
        request_body = {
            "appName": agent_name,  # camelCase - use agent_name directly (e.g., 'ingestion')
            "userId": user_id,  # camelCase
            "sessionId": task_id,  # camelCase
            "newMessage": {  # camelCase
                "role": "user",
                "parts": [{"text": json.dumps({"skill": skill, **payload})}]
            }
        }
        
        client = await self._get_client()
        try:
            # ADK api_server exposes /run endpoint
            response = await client.post(
                f"{agent.url}/run",
                json=request_body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract result from ADK response
                # ADK returns events, we want the final response
                if isinstance(data, list):
                    # Stream of events, get last one with content
                    for event in reversed(data):
                        if event.get("content"):
                            return A2AResponse.success(
                                {"content": event["content"], "task_id": task_id},
                                task_id
                            )
                    return A2AResponse.success({"events": data, "task_id": task_id}, task_id)
                else:
                    return A2AResponse.success(data, task_id)
            else:
                return A2AResponse.error_response(
                    -32002,
                    f"Agent returned status {response.status_code}: {response.text}"
                )
        except Exception as e:
            return A2AResponse.error_response(-32003, f"Request failed: {str(e)}")
    
    async def run_agent(
        self,
        agent_name: str,
        message: str,
        user_id: str = "default",
        session_id: Optional[str] = None
    ) -> A2AResponse:
        """Run an ADK agent with a natural language message."""
        if agent_name not in self._agents:
            return A2AResponse.error_response(-32001, f"Unknown agent: {agent_name}")
        
        agent = self._agents[agent_name]
        session_id = session_id or str(uuid.uuid4())
        
        # Create session first (idempotent - will succeed if already exists)
        session_result = await self.create_session(agent_name, user_id, session_id)
        if session_result.error is not None:
            # If session already exists (409), that's OK - proceed
            error_msg = ""
            if isinstance(session_result.error, dict):
                error_msg = session_result.error.get("message", "")
            else:
                error_msg = str(session_result.error)
            if "already exists" not in error_msg.lower():
                return session_result
        
        # ADK agents expect camelCase field names
        request_body = {
            "appName": agent_name,  # camelCase - use agent_name directly (e.g., 'ingestion')
            "userId": user_id,  # camelCase
            "sessionId": session_id,  # camelCase
            "newMessage": {  # camelCase
                "role": "user",
                "parts": [{"text": message}]
            }
        }
        
        client = await self._get_client()
        try:
            response = await client.post(
                f"{agent.url}/run",
                json=request_body,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                return A2AResponse.success(response.json(), session_id)
            else:
                return A2AResponse.error_response(-32002, f"Agent error: {response.text}")
        except Exception as e:
            return A2AResponse.error_response(-32003, f"Request failed: {str(e)}")
    
    async def get_task_status(
        self,
        agent_name: str,
        task_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get the status of a task (for ADK sessions)."""
        # ADK doesn't have a direct task status endpoint
        # Sessions are managed internally
        return {"id": task_id, "status": "completed"}
    
    async def cancel_task(
        self,
        agent_name: str,
        task_id: str
    ) -> bool:
        """Cancel a running task."""
        # ADK handles this internally
        return True


def create_a2a_client() -> A2AClient:
    """Create an A2A client with all agents registered."""
    from app.core.config import settings
    
    client = A2AClient()
    client.register_agent("ingestion", settings.ingestion_agent_url, "Content parsing")
    client.register_agent("profile", settings.profile_agent_url, "User profiles")
    client.register_agent("synthesis", settings.synthesis_agent_url, "Content generation")
    client.register_agent("planner", settings.planner_agent_url, "Priority calculation")
    client.register_agent("orchestrator", settings.orchestrator_agent_url, "Background coordination")
    
    return client


_client: Optional[A2AClient] = None


async def get_a2a_client() -> A2AClient:
    """Get or create the A2A client singleton."""
    global _client
    if _client is None:
        _client = create_a2a_client()
    return _client
