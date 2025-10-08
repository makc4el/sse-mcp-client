"""
LangGraph Platform-Ready Chat Agent with MCP Integration

A production-ready conversational AI agent built with LangGraph and OpenAI GPT-4o-mini,
using the official langchain-mcp-adapters for seamless MCP tool integration.
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
from langgraph.prebuilt import create_react_agent
from typing_extensions import Annotated, TypedDict
from langchain_mcp_adapters.client import MultiServerMCPClient

# MCP server configuration
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL")
if not MCP_SERVER_URL:
    raise ValueError("MCP_SERVER_URL environment variable is required")


class AdvancedChatState(TypedDict):
    """Enhanced state for advanced chat agent with session management."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    session_id: str
    conversation_count: int


async def initialize_mcp_client() -> MultiServerMCPClient:
    """Initialize the MCP client with weather server configuration."""
    return MultiServerMCPClient({
        "weather": {
            "url": MCP_SERVER_URL,
            "transport": "sse",  # Using SSE transport as per your setup
        }
    })


def create_llm() -> ChatOpenAI:
    """Create and configure the OpenAI LLM instance."""
    return ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


async def advanced_chat_node(state: AdvancedChatState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Advanced chat node with MCP tool integration using langchain-mcp-adapters.
    
    Args:
        state: Enhanced chat state with user and session information
        config: Runtime configuration from LangGraph platform
        
    Returns:
        Dictionary containing the AI response and updated state
    """
    try:
        # Initialize MCP client and get tools
        mcp_client = await initialize_mcp_client()
        tools = await mcp_client.get_tools()
        
        # Create agent with MCP tools
        agent = create_react_agent("openai:gpt-4o-mini", tools)
        
        # Convert messages to the format expected by the agent
        messages = state["messages"]
        conversation_count = state.get("conversation_count", 0)
        
        # Prepare the input for the agent
        if conversation_count == 0:
            # First message in session - add system context
            system_context = SystemMessage(
                content="Hello! I'm your advanced AI assistant with access to weather tools. "
                       "I can help you with weather information, forecasts, and alerts. "
                       "How can I help you today?"
            )
            messages = [system_context] + messages
        
        # Convert to agent input format
        agent_input = {"messages": [msg.content for msg in messages if hasattr(msg, 'content')]}
        
        # Get response from agent
        response = await agent.ainvoke(agent_input)
        
        # Extract the final response
        if "messages" in response and response["messages"]:
            final_message = response["messages"][-1]
            if hasattr(final_message, 'content'):
                ai_response = AIMessage(content=final_message.content)
            else:
                ai_response = AIMessage(content=str(final_message))
        else:
            ai_response = AIMessage(content="I apologize, but I couldn't process your request.")
        
        return {
            "messages": [ai_response],
            "conversation_count": conversation_count + 1,
        }
        
    except Exception as e:
        # Handle errors gracefully
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
        )
        return {
            "messages": [error_message],
            "conversation_count": state.get("conversation_count", 0),
        }


def create_advanced_graph() -> StateGraph:
    """
    Create an advanced chat agent graph with MCP tool integration.
    
    Returns:
        Compiled StateGraph with MCP tools
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


async def main():
    """
    Local testing function - not used in platform deployment.
    Run this file directly to test the agent locally.
    """
    print("Testing Advanced Chat Agent with MCP Integration...")
    
    # Test the advanced graph
    test_state = {
        "messages": [HumanMessage(content="What's the weather like in Spokane?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0,
    }
    
    try:
        result = await advanced_graph.ainvoke(test_state)
        print("Advanced Agent Response:")
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                print(f"- {msg.content}")
        print("Conversation Count:", result["conversation_count"])
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())