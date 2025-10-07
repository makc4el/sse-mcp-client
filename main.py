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
        llm = create_llm()
        
        # Initialize MCP tools if not already present
        if "mcp_tools" not in state:
            state["mcp_tools"] = initialize_mcp_tools()
        
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