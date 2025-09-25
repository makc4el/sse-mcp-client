#!/usr/bin/env python3
"""
LangChain Integration for SSE MCP Client

This module provides LangChain BaseTool wrappers for MCP tools,
allowing seamless integration with LangChain agents.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Type, Union
from pydantic import BaseModel, Field

# LangChain imports
from langchain.tools import BaseTool
from langchain.callbacks.manager import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)

# Import our MCP client
from mcp_client import SSEMCPClient, Tool as MCPTool

logger = logging.getLogger(__name__)


class MCPToolWrapper(BaseTool):
    """
    LangChain tool wrapper for MCP tools
    
    This wrapper allows MCP tools to be used as LangChain tools
    in agents and other LangChain components.
    """
    
    # Tool metadata
    name: str
    description: str
    args_schema: Optional[Type[BaseModel]] = None
    
    # MCP-specific attributes
    mcp_tool: MCPTool = Field(exclude=True)
    mcp_client: SSEMCPClient = Field(exclude=True)
    
    class Config:
        arbitrary_types_allowed = True
    
    def __init__(self, mcp_tool: MCPTool, mcp_client: SSEMCPClient, **kwargs):
        """
        Initialize the MCP tool wrapper
        
        Args:
            mcp_tool: The MCP tool definition
            mcp_client: Connected MCP client instance
        """
        # Create Pydantic schema from MCP tool schema
        args_schema = self._create_pydantic_schema(mcp_tool)
        
        super().__init__(
            name=mcp_tool.name,
            description=mcp_tool.description,
            args_schema=args_schema,
            mcp_tool=mcp_tool,
            mcp_client=mcp_client,
            **kwargs
        )
    
    def _create_pydantic_schema(self, mcp_tool: MCPTool) -> Type[BaseModel]:
        """Create Pydantic schema from MCP tool input schema"""
        schema = mcp_tool.inputSchema
        properties = schema.get("properties", {})
        required = schema.get("required", [])
        
        # Build Pydantic fields dynamically with proper annotations
        annotations = {}
        field_definitions = {}
        
        for prop_name, prop_def in properties.items():
            prop_type = prop_def.get("type", "string")
            prop_desc = prop_def.get("description", "")
            
            # Map JSON schema types to Python types
            if prop_type == "number":
                python_type = float
            elif prop_type == "integer":
                python_type = int
            elif prop_type == "boolean":
                python_type = bool
            else:
                python_type = str
            
            # Make field optional if not required
            if prop_name in required:
                annotations[prop_name] = python_type
                field_definitions[prop_name] = Field(description=prop_desc)
            else:
                annotations[prop_name] = Optional[python_type]
                field_definitions[prop_name] = Field(default=None, description=prop_desc)
        
        # Create dynamic Pydantic model with proper annotations
        namespace = {
            "__annotations__": annotations,
            **field_definitions
        }
        
        return type(f"{mcp_tool.name}Schema", (BaseModel,), namespace)
    
    def _run(
        self,
        run_manager: Optional[CallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the tool synchronously (handles event loop properly)"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in a loop, create a new thread for the async call
                import concurrent.futures
                import threading
                
                def run_in_thread():
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    try:
                        return new_loop.run_until_complete(self._arun(run_manager=None, **kwargs))
                    finally:
                        new_loop.close()
                
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(run_in_thread)
                    return future.result(timeout=30)
                    
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                return asyncio.run(self._arun(run_manager=None, **kwargs))
                
        except Exception as e:
            return f"Error executing tool {self.name}: {str(e)}"
    
    async def _arun(
        self,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
        **kwargs: Any,
    ) -> str:
        """Run the tool asynchronously"""
        try:
            logger.info(f"Calling MCP tool: {self.name} with args: {kwargs}")
            
            # Call the MCP tool
            result = await self.mcp_client.call_tool(self.name, kwargs)
            
            # Extract text content from MCP response
            content = result.get("content", [])
            if content and isinstance(content, list):
                # Get first text content
                for item in content:
                    if item.get("type") == "text":
                        return item.get("text", str(result))
            
            # Fallback to JSON representation
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Error calling MCP tool {self.name}: {e}")
            raise


class MCPToolAdapter:
    """
    Adapter that converts MCP tools to LangChain tools
    
    This class manages the connection to an MCP server and provides
    LangChain-compatible tools for use in agents.
    """
    
    def __init__(self, server_url: str, timeout: int = 30):
        """
        Initialize the MCP tool adapter
        
        Args:
            server_url: MCP server URL
            timeout: Request timeout
        """
        self.server_url = server_url
        self.timeout = timeout
        self.client: Optional[SSEMCPClient] = None
        self.tools: List[MCPToolWrapper] = []
        self._connected = False
    
    async def connect(self) -> bool:
        """Connect to the MCP server and initialize"""
        try:
            self.client = SSEMCPClient(self.server_url, self.timeout)
            
            if not await self.client.connect():
                raise Exception("Failed to connect to MCP server")
            
            if not await self.client.initialize():
                raise Exception("Failed to initialize MCP session")
            
            self._connected = True
            logger.info(f"Connected to MCP server at {self.server_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server"""
        if self.client:
            await self.client.disconnect()
            self.client = None
        self._connected = False
        self.tools.clear()
    
    async def load_tools(self) -> List[MCPToolWrapper]:
        """
        Load tools from the MCP server and wrap them as LangChain tools
        
        Returns:
            List of LangChain-compatible tools
        """
        if not self._connected or not self.client:
            raise Exception("Not connected to MCP server")
        
        try:
            # Get tools from MCP server
            mcp_tools = await self.client.list_tools()
            
            # Wrap each MCP tool as a LangChain tool
            self.tools = []
            for mcp_tool in mcp_tools:
                wrapper = MCPToolWrapper(mcp_tool, self.client)
                self.tools.append(wrapper)
            
            logger.info(f"Loaded {len(self.tools)} tools from MCP server")
            return self.tools
            
        except Exception as e:
            logger.error(f"Failed to load tools: {e}")
            raise
    
    def get_tools(self) -> List[MCPToolWrapper]:
        """Get the loaded LangChain tools"""
        return self.tools
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        await self.load_tools()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()


# Convenience functions
async def create_mcp_tools(server_url: str, timeout: int = 30) -> List[MCPToolWrapper]:
    """
    Create LangChain tools from an MCP server
    
    Args:
        server_url: MCP server URL
        timeout: Request timeout
        
    Returns:
        List of LangChain tools
    """
    adapter = MCPToolAdapter(server_url, timeout)
    await adapter.connect()
    tools = await adapter.load_tools()
    return tools


async def create_persistent_mcp_adapter(server_url: str, timeout: int = 30) -> MCPToolAdapter:
    """
    Create a persistent MCP adapter for long-running applications
    
    Args:
        server_url: MCP server URL
        timeout: Request timeout
        
    Returns:
        Connected MCP tool adapter
    """
    adapter = MCPToolAdapter(server_url, timeout)
    await adapter.connect()
    await adapter.load_tools()
    return adapter
