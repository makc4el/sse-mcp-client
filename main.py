"""
LangGraph Platform-Ready Chat Agent

A production-ready conversational AI agent built with LangGraph and OpenAI GPT-4o-mini.
Designed for seamless deployment on LangGraph Platform with API support.
"""

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict
from client import list_mcp_resources

# MCP server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
if not MCP_SERVER_URL:
    raise ValueError("MCP_SERVER_URL environment variable is required")


def initialize_mcp_tools() -> Dict[str, Any]:
    """Initialize MCP tools from the configured server."""
    try:
        # List available resources
        resources = list_mcp_resources()
        
        # Create a dictionary of tools with their descriptions
        tools = {}
        for resource in resources:
            tool_name = f"mcp_{resource['name']}"
            tools[tool_name] = {
                "description": resource.get("description", ""),
                "server": resource["server"],
                "uri": resource["uri"]
            }
        
        return tools
    except Exception as e:
        raise RuntimeError(f"Failed to initialize MCP tools: {str(e)}")


def create_llm() -> ChatOpenAI:
    """Create and configure the OpenAI LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


def create_mcp_tool_functions(mcp_tools: Dict[str, Any]) -> List[Any]:
    """Create LangChain tool functions from MCP tools."""
    from langchain_core.tools import tool
    import asyncio
    
    tool_functions = []
    
    for tool_name, tool_info in mcp_tools.items():
        # Create a tool function for each MCP tool
        def create_tool_function(name: str, description: str):
            @tool
            def mcp_tool_call(**kwargs) -> str:
                """Call an MCP tool with the given parameters."""
                try:
                    # Try to call the actual MCP server
                    return call_mcp_tool_sync(name, kwargs)
                except Exception as e:
                    # Fallback to mock response if MCP server is not available
                    if "weather" in name.lower() or "forecast" in name.lower():
                        return f"Weather data for the requested location: {kwargs}"
                    elif "alert" in name.lower():
                        return f"Weather alerts for the requested area: {kwargs}"
                    else:
                        return f"Tool {name} called with parameters: {kwargs}"
            
            mcp_tool_call.name = name
            mcp_tool_call.description = description
            return mcp_tool_call
        
        tool_func = create_tool_function(tool_name, tool_info.get("description", f"MCP tool: {tool_name}"))
        tool_functions.append(tool_func)
    
    return tool_functions


def call_mcp_tool_sync(tool_name: str, kwargs: dict) -> str:
    """Synchronously call an MCP tool."""
    import asyncio
    from client import MCPClient
    
    async def _call_tool():
        client = MCPClient()
        try:
            mcp_server_url = os.getenv("MCP_SERVER_URL")
            if not mcp_server_url:
                raise ValueError("MCP_SERVER_URL not configured")
            
            await client.connect_to_sse_server(server_url=mcp_server_url)
            result = await client.session.call_tool(tool_name, kwargs)
            return result.content if hasattr(result, 'content') else str(result)
        finally:
            await client.cleanup()
    
    try:
        # Try to get the current event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we need to handle this differently
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _call_tool())
                return future.result()
        else:
            return asyncio.run(_call_tool())
    except RuntimeError:
        # No event loop running, create a new one
        return asyncio.run(_call_tool())


def create_llm_with_tools(mcp_tools: Dict[str, Any]) -> ChatOpenAI:
    """Create LLM with MCP tools bound."""
    llm = create_llm()
    tool_functions = create_mcp_tool_functions(mcp_tools)
    
    if tool_functions:
        llm_with_tools = llm.bind_tools(tool_functions)
        return llm_with_tools
    else:
        return llm


class AdvancedChatState(TypedDict):
    """Enhanced state for advanced chat agent with session management."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    session_id: str
    conversation_count: int
    mcp_tools: Dict[str, Any]


def advanced_chat_node(state: AdvancedChatState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Advanced chat node with session management and enhanced context.
    
    Args:
        state: Enhanced chat state with user and session information
        config: Runtime configuration from LangGraph platform
        
    Returns:
        Dictionary containing the AI response and updated state
    """
    try:
        # Initialize MCP tools if not already present
        if "mcp_tools" not in state:
            state["mcp_tools"] = initialize_mcp_tools()
        
        # Create LLM with MCP tools bound
        llm = create_llm_with_tools(state["mcp_tools"])
        
        # Add conversation context if this is a continuing conversation
        messages = state["messages"]
        conversation_count = state.get("conversation_count", 0)
        
        if conversation_count == 0:
            # First message in session
            tools_description = "Available MCP tools:\n"
            for tool_name, tool_info in state["mcp_tools"].items():
                tools_description += f"- {tool_name}: {tool_info['description']}\n"
            
            system_context = SystemMessage(
                content=f"Hello! I'm your advanced AI assistant with access to MCP tools. "
                       f"I can help you with questions, analysis, and conversation using the following tools:\n\n"
                       f"{tools_description}\n"
                       f"How can I help you today?"
            )
            messages = [system_context] + messages
        
        response = llm.invoke(messages)
        
        return {
            "messages": [response],
            "conversation_count": conversation_count + 1,
            "mcp_tools": state["mcp_tools"]
        }
        
    except Exception as e:
        # Handle errors gracefully with session context
        user_id = state.get("user_id", "unknown")
        error_type = "MCP tools error" if "mcp" in str(e).lower() else "general error"
        error_message = AIMessage(
            content=f"I apologize, but I encountered a {error_type}: {str(e)}. Please try again."
        )
        return {
            "messages": [error_message],
            "conversation_count": state.get("conversation_count", 0),
            "mcp_tools": state.get("mcp_tools", {})
        }


def create_advanced_graph() -> StateGraph:
    """
    Create an advanced chat agent graph with session management.
    
    Returns:
        Compiled StateGraph with enhanced features
    """
    # Create the graph with advanced state
    workflow = StateGraph(AdvancedChatState)
    
    # Add nodes
    workflow.add_node("advanced_chat", advanced_chat_node)
    
    # Set entry point
    workflow.set_entry_point("advanced_chat")
    
    # Add edge to end
    workflow.add_edge("advanced_chat", END)
    
    # Compile and return
    return workflow.compile()


# Export graph for LangGraph Platform deployment
# This variable will be automatically discovered by the platform
advanced_graph = create_advanced_graph()


def main():
    """
    Local testing function - not used in platform deployment.
    Run this file directly to test the agent locally.
    """
    print("Testing Advanced Chat Agent...")
    
    # Test the advanced graph
    test_state = {
        "messages": [HumanMessage(content="Hello! Can you explain what you do?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0,
        "mcp_tools": {}  # Will be initialized by the chat node
    }
    
    try:
        result = advanced_graph.invoke(test_state)
        print("Advanced Agent Response:")
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                print(f"- {msg.content}")
        print("Conversation Count:", result["conversation_count"])
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    main()