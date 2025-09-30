"""
LangGraph Platform-Ready Chat Agent

A production-ready conversational AI agent built with LangGraph and OpenAI GPT-4o-mini.
Designed for seamless deployment on LangGraph Platform with API support.
"""

import os
import asyncio
from typing import Dict, List, Any
from dotenv import load_dotenv

# Load environment variables (for local development)
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

# Import MCP client functionality
from McpClient import MCPClient

# Global MCP client instance
mcp_client = None


async def initialize_mcp_client():
    """Initialize the MCP client connection."""
    global mcp_client
    if mcp_client is None:
        mcp_client = MCPClient()
        mcp_server_url = os.getenv("MCP_SERVER_URL")
        if mcp_server_url:
            await mcp_client.connect_to_sse_server(mcp_server_url)
    return mcp_client


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


def advanced_chat_node(state: AdvancedChatState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Advanced chat node with session management and MCP integration.
    
    Args:
        state: Enhanced chat state with user and session information
        config: Runtime configuration from LangGraph platform
        
    Returns:
        Dictionary containing the AI response and updated state
    """
    try:
        # Get the latest user message
        messages = state["messages"]
        conversation_count = state.get("conversation_count", 0)
        
        # Extract the latest user query
        user_query = ""
        for msg in reversed(messages):
            if isinstance(msg, HumanMessage):
                user_query = msg.content
                break
        
        if not user_query:
            error_message = AIMessage(
                content="I didn't receive a valid query. Please try again."
            )
            return {
                "messages": [error_message],
                "conversation_count": conversation_count
            }
        
        # Process query using MCP client (async operation in sync context)
        try:
            # Try to run async MCP operations in a new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Initialize MCP client if not already done
            loop.run_until_complete(initialize_mcp_client())
            
            # Process query using MCP client
            if mcp_client and mcp_client.session:
                response_content = loop.run_until_complete(mcp_client.process_query(user_query))
            else:
                raise Exception("MCP client not available")
                
        except Exception as mcp_error:
            # Fallback to regular LLM if MCP is not available
            llm = create_llm()
            if conversation_count == 0:
                system_context = AIMessage(
                    content="Hello! I'm your advanced AI assistant. I can help you with questions, analysis, and conversation. How can I help you today?"
                )
                messages = [system_context] + messages
            
            response = llm.invoke(messages)
            response_content = response.content
        
        # Create AI response message
        ai_response = AIMessage(content=response_content)
        
        return {
            "messages": [ai_response],
            "conversation_count": conversation_count + 1
        }
        
    except Exception as e:
        # Handle errors gracefully with session context
        user_id = state.get("user_id", "unknown")
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
        )
        return {
            "messages": [error_message],
            "conversation_count": state.get("conversation_count", 0)
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


async def cleanup_mcp_client():
    """Clean up MCP client resources."""
    global mcp_client
    if mcp_client:
        await mcp_client.cleanup()
        mcp_client = None


async def main():
    """
    Local testing function - not used in platform deployment.
    Run this file directly to test the agent locally.
    """
    print("Testing Advanced Chat Agent with MCP integration...")
    
    # Test the advanced graph
    test_state = {
        "messages": [HumanMessage(content="Hello! Can you explain what you do?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0
    }
    
    try:
        # Initialize MCP client for testing
        await initialize_mcp_client()
        
        result = await advanced_chat_node(test_state, {})
        print("Advanced Agent Response:")
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                print(f"- {msg.content}")
        print("Conversation Count:", result["conversation_count"])
    except Exception as e:
        print(f"Test failed: {e}")
    finally:
        await cleanup_mcp_client()


if __name__ == "__main__":
    asyncio.run(main())