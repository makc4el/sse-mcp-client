#!/usr/bin/env python3
"""
Simple MCP SSE Client for LangGraph deployment
This version avoids complex LangChain imports that cause deployment issues
"""

import asyncio
import json
import os
from typing import Optional, List, Dict, Any
from contextlib import AsyncExitStack

from mcp import ClientSession
from mcp.client.sse import sse_client
from dotenv import load_dotenv

load_dotenv()


class SimpleMCPClient:
    """Simple MCP client without complex LangChain dependencies"""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.session: Optional[ClientSession] = None
        self._streams_context = None
        self._session_context = None
        
    async def connect(self):
        """Connect to the MCP server"""
        try:
            # Connect to MCP server
            self._streams_context = sse_client(url=self.server_url)
            streams = await self._streams_context.__aenter__()
            
            self._session_context = ClientSession(*streams)
            self.session = await self._session_context.__aenter__()
            
            # Initialize session
            await self.session.initialize()
            
            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            print(f"Connected to MCP server with {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            
            return True
        except Exception as e:
            print(f"Failed to connect: {e}")
            return False
    
    async def call_tool(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Call a tool on the MCP server"""
        if not self.session:
            return "Not connected to server"
        
        try:
            result = await self.session.call_tool(tool_name, args)
            if result.content:
                return str(result.content[0].text)
            return "No result"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def cleanup(self):
        """Clean up connections"""
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)


def create_graph():
    """Create LangGraph graph for LangChain platform deployment"""
    try:
        from langgraph.graph import StateGraph, END
        from typing import TypedDict, Annotated
        
        class State(TypedDict):
            messages: Annotated[list[dict], "The messages in the conversation"]
        
        async def chat_node(state: State):
            """Chat node that processes messages"""
            # Simple response for now
            return {"messages": [{"role": "assistant", "content": "MCP SSE Client is running!"}]}
        
        # Create the graph
        workflow = StateGraph(State)
        workflow.add_node("chat", chat_node)
        workflow.set_entry_point("chat")
        workflow.add_edge("chat", END)
        
        return workflow.compile()
    except ImportError as e:
        print(f"Import error in create_graph: {e}")
        return None


async def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python simple_client.py <SSE_SERVER_URL>")
        sys.exit(1)
    
    server_url = sys.argv[1]
    client = SimpleMCPClient(server_url)
    
    try:
        if await client.connect():
            print("\nSimple MCP Client Started!")
            print("Type your queries or 'quit' to exit.")
            
            while True:
                try:
                    query = input("\nQuery: ").strip()
                    
                    if query.lower() == 'quit':
                        break
                    
                    # Simple response for now
                    print(f"Response: I received your query: {query}")
                    
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"\nError: {str(e)}")
    
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
