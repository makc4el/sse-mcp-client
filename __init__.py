"""
SSE MCP Client Package

A Python client for connecting to MCP servers via Server-Sent Events.
"""

from .mcp_client import (
    SSEMCPClient,
    ConnectionState,
    MCPResponse,
    Tool,
    create_client,
    quick_tool_call
)

__version__ = "1.0.0"
__author__ = "SSE MCP Client"

__all__ = [
    "SSEMCPClient",
    "ConnectionState", 
    "MCPResponse",
    "Tool",
    "create_client",
    "quick_tool_call"
]
