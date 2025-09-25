#!/usr/bin/env python3
"""
SSE MCP Client - A client for connecting to SSE MCP servers
Follows MCP specification for HTTP with SSE transport
"""

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator
import httpx
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting" 
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPResponse:
    """MCP response from server"""
    id: Optional[str]
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


@dataclass
class Tool:
    """Tool definition from server"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class SSEMCPClient:
    """
    MCP Client for connecting to SSE-enabled MCP servers
    
    This client handles:
    - SSE connection establishment
    - MCP protocol communication
    - Tool discovery and execution
    - Event handling and notifications
    """
    
    def __init__(self, server_url: str, timeout: int = 30):
        """
        Initialize the MCP client
        
        Args:
            server_url: Base URL of the MCP server (e.g., "http://localhost:8000")
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip('/')
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self.message_endpoint: Optional[str] = None
        self.state = ConnectionState.DISCONNECTED
        self.tools: List[Tool] = []
        self.initialized = False
        
        # Event handlers
        self.on_notification: Optional[Callable[[Dict[str, Any]], None]] = None
        self.on_connection_state_change: Optional[Callable[[ConnectionState], None]] = None
        
        # HTTP client
        self.http_client = httpx.AsyncClient(timeout=timeout)
        
        # SSE task
        self._sse_task: Optional[asyncio.Task] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()
        
    def _update_state(self, new_state: ConnectionState):
        """Update connection state and notify handlers"""
        if self.state != new_state:
            logger.info(f"Connection state changed: {self.state.value} -> {new_state.value}")
            self.state = new_state
            if self.on_connection_state_change:
                self.on_connection_state_change(new_state)
    
    async def _handle_sse_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """Handle incoming SSE events from server"""
        try:
            self._update_state(ConnectionState.CONNECTING)
            
            async with self.http_client.stream(
                "GET", 
                f"{self.server_url}/connect",
                headers={"Accept": "text/event-stream"}
            ) as response:
                response.raise_for_status()
                self._update_state(ConnectionState.CONNECTED)
                
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])  # Remove "data: " prefix
                            yield data
                        except json.JSONDecodeError as e:
                            logger.error(f"Failed to parse SSE data: {e}")
                            continue
                            
        except Exception as e:
            logger.error(f"SSE connection error: {e}")
            self._update_state(ConnectionState.ERROR)
            raise
    
    async def _process_sse_events(self):
        """Process SSE events in background task"""
        try:
            async for event in self._handle_sse_events():
                await self._handle_event(event)
        except Exception as e:
            logger.error(f"Error processing SSE events: {e}")
            self._update_state(ConnectionState.ERROR)
    
    async def _handle_event(self, event: Dict[str, Any]):
        """Handle individual SSE event"""
        method = event.get("method")
        
        if method == "endpoint":
            # Extract session ID and message endpoint from the endpoint event
            params = event.get("params", {})
            uri = params.get("uri", "")
            if "sessionId=" in uri:
                self.session_id = uri.split("sessionId=")[1].split("&")[0]
                self.message_endpoint = f"{self.server_url}/messages?sessionId={self.session_id}"
                logger.info(f"Received endpoint: {self.message_endpoint}")
                
        elif method == "notifications/message":
            # Handle notification from server
            params = event.get("params", {})
            level = params.get("level", "info")
            data = params.get("data", "")
            logger.log(getattr(logging, level.upper(), logging.INFO), f"Server notification: {data}")
            
            if self.on_notification:
                self.on_notification(event)
                
        elif method == "ping":
            # Handle heartbeat
            logger.debug("Received heartbeat from server")
            
        else:
            logger.debug(f"Received event: {event}")
    
    async def connect(self) -> bool:
        """
        Connect to the MCP server via SSE
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to MCP server at {self.server_url}")
            
            # Start SSE event processing
            self._sse_task = asyncio.create_task(self._process_sse_events())
            
            # Wait for endpoint event to get session info
            max_wait = 10  # seconds
            waited = 0
            while not self.session_id and waited < max_wait:
                await asyncio.sleep(0.1)
                waited += 0.1
                
            if not self.session_id:
                raise Exception("Failed to receive session ID from server")
                
            logger.info(f"Connected with session ID: {self.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self._update_state(ConnectionState.ERROR)
            return False
    
    async def disconnect(self):
        """Disconnect from the server"""
        logger.info("Disconnecting from MCP server")
        
        if self._sse_task and not self._sse_task.done():
            self._sse_task.cancel()
            try:
                await self._sse_task
            except asyncio.CancelledError:
                pass
                
        await self.http_client.aclose()
        self._update_state(ConnectionState.DISCONNECTED)
        self.session_id = None
        self.message_endpoint = None
        self.initialized = False
        self.tools.clear()
    
    async def _send_request(self, method: str, params: Optional[Dict[str, Any]] = None) -> MCPResponse:
        """Send MCP request to server"""
        if not self.message_endpoint:
            raise Exception("Not connected to server")
            
        request_id = str(uuid.uuid4())
        request_data = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params or {}
        }
        
        logger.debug(f"Sending request: {method}")
        
        try:
            response = await self.http_client.post(
                self.message_endpoint,
                json=request_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            response_data = response.json()
            return MCPResponse(
                id=response_data.get("id"),
                result=response_data.get("result"),
                error=response_data.get("error")
            )
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            raise
    
    async def initialize(self) -> bool:
        """
        Initialize the MCP session
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            response = await self._send_request("initialize", {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {}
                },
                "clientInfo": {
                    "name": "sse-mcp-client",
                    "version": "1.0.0"
                }
            })
            
            if response.error:
                logger.error(f"Initialize failed: {response.error}")
                return False
                
            logger.info("MCP session initialized successfully")
            self.initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Initialize failed: {e}")
            return False
    
    async def list_tools(self) -> List[Tool]:
        """
        Get list of available tools from server
        
        Returns:
            List of available tools
        """
        if not self.initialized:
            raise Exception("Client not initialized")
            
        try:
            response = await self._send_request("tools/list")
            
            if response.error:
                raise Exception(f"Failed to list tools: {response.error}")
                
            tools_data = response.result.get("tools", [])
            self.tools = [
                Tool(
                    name=tool["name"],
                    description=tool["description"],
                    inputSchema=tool["inputSchema"]
                )
                for tool in tools_data
            ]
            
            logger.info(f"Retrieved {len(self.tools)} tools")
            return self.tools
            
        except Exception as e:
            logger.error(f"Failed to list tools: {e}")
            raise
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool on the server
        
        Args:
            tool_name: Name of the tool to call
            arguments: Arguments for the tool
            
        Returns:
            Tool execution result
        """
        if not self.initialized:
            raise Exception("Client not initialized")
            
        try:
            response = await self._send_request("tools/call", {
                "name": tool_name,
                "arguments": arguments
            })
            
            if response.error:
                raise Exception(f"Tool call failed: {response.error}")
                
            return response.result
            
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
    
    async def health_check(self) -> bool:
        """
        Check if server is healthy
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = await self.http_client.get(f"{self.server_url}/health")
            response.raise_for_status()
            data = response.json()
            return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    def set_notification_handler(self, handler: Callable[[Dict[str, Any]], None]):
        """Set handler for server notifications"""
        self.on_notification = handler
    
    def set_connection_state_handler(self, handler: Callable[[ConnectionState], None]):
        """Set handler for connection state changes"""
        self.on_connection_state_change = handler


# Convenience functions for quick usage
async def create_client(server_url: str, timeout: int = 30) -> SSEMCPClient:
    """
    Create and connect an MCP client
    
    Args:
        server_url: Server URL
        timeout: Request timeout
        
    Returns:
        Connected MCP client
    """
    client = SSEMCPClient(server_url, timeout)
    
    if not await client.connect():
        raise Exception("Failed to connect to server")
        
    if not await client.initialize():
        raise Exception("Failed to initialize MCP session")
        
    return client


async def quick_tool_call(server_url: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """
    Quick tool call - connect, call tool, disconnect
    
    Args:
        server_url: Server URL  
        tool_name: Tool to call
        arguments: Tool arguments
        
    Returns:
        Tool result
    """
    async with SSEMCPClient(server_url) as client:
        await client.connect()
        await client.initialize()
        return await client.call_tool(tool_name, arguments)
