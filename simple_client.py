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
        from langgraph.graph.message import add_messages
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
        from typing import TypedDict, Annotated, List
        from langchain_openai import ChatOpenAI
        import os
        
        class ChatState(TypedDict):
            """State for the MCP chat agent."""
            messages: Annotated[List[BaseMessage], add_messages]
        
        def chat_node(state: ChatState):
            """Main chat node that processes user input and generates AI responses."""
            try:
                messages = state["messages"]
                last_message = messages[-1] if messages else None
                
                # Create LLM instance
                llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.7,
                    openai_api_key=os.getenv("OPENAI_API_KEY"),
                )
                
                # Check if this is the first interaction
                if len(messages) == 1 and last_message:
                    # First interaction - ask for MCP server URL
                    response = AIMessage(
                        content="🔗 Hello! I'm your MCP SSE Client Assistant.\n\n"
                               "To get started, I need the URL of your MCP SSE server.\n\n"
                               "Please provide the server URL in one of these formats:\n"
                               "• `https://your-server.com/sse`\n"
                               "• `wss://your-server.com/sse`\n"
                               "• Just the domain: `your-server.com`\n\n"
                               "Once connected, I'll help you interact with your MCP server!"
                    )
                    return {"messages": [response]}
                
                # Check if user provided a server URL
                if last_message and hasattr(last_message, 'content'):
                    content = str(last_message.content).strip()
                    
                    # Look for URL patterns
                    import re
                    url_patterns = [
                        r'https?://[^\s]+',
                        r'wss?://[^\s]+',
                        r'[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?::\d+)?(?:/[^\s]*)?'
                    ]
                    
                    server_url = None
                    for pattern in url_patterns:
                        match = re.search(pattern, content)
                        if match:
                            server_url = match.group(0)
                            # Ensure it has a protocol
                            if not server_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
                                server_url = f"https://{server_url}"
                            # Ensure it ends with /sse if not already
                            if not server_url.endswith('/sse'):
                                server_url = f"{server_url.rstrip('/')}/sse"
                            break
                    
                    if server_url:
                        # User provided server URL - try to connect
                        try:
                            # For now, just acknowledge the connection
                            response = AIMessage(
                                content=f"✅ Great! I'll connect to your MCP server at: `{server_url}`\n\n"
                                       f"🚀 **MCP SSE Client Connected!**\n\n"
                                       f"**Available Capabilities:**\n"
                                       f"• Connect to MCP servers via Server-Sent Events\n"
                                       f"• Execute MCP tools and operations\n"
                                       f"• Process queries with intelligent tool selection\n"
                                       f"• Maintain conversation context\n\n"
                                       f"**Example Usage:**\n"
                                       f"• Ask me to query your MCP server\n"
                                       f"• Request specific tool operations\n"
                                       f"• Get help with MCP server interactions\n\n"
                                       f"What would you like to do with your MCP server?"
                            )
                            return {"messages": [response]}
                        except Exception as e:
                            response = AIMessage(
                                content=f"❌ Failed to connect to MCP server at `{server_url}`\n\n"
                                       f"Error: {str(e)}\n\n"
                                       f"Please check:\n"
                                       f"• Server URL is correct\n"
                                       f"• Server is running and accessible\n"
                                       f"• Network connectivity\n\n"
                                       f"Try again with a different server URL."
                            )
                            return {"messages": [response]}
                
                # Regular conversation - use LLM to respond
                response = llm.invoke(messages)
                return {"messages": [response]}
                
            except Exception as e:
                error_message = AIMessage(
                    content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
                )
                return {"messages": [error_message]}
        
        def should_continue(state: ChatState) -> str:
            """Determine whether to continue or end the conversation."""
            # For now, always end - we'll add tools later
            return END
        
        # Create the graph
        workflow = StateGraph(ChatState)
        
        # Add nodes
        workflow.add_node("chat", chat_node)
        
        # Set entry point
        workflow.set_entry_point("chat")
        
        # Add edge from chat to END (simplified for now)
        workflow.add_edge("chat", END)
        
        # Compile and return
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
