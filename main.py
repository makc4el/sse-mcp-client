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
        
        # Create LLM with tools bound
        llm = create_llm()
        llm_with_tools = llm.bind_tools(tools)
        
        # Get messages from state
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
        
        # Get response from LLM with tools
        response = await llm_with_tools.ainvoke(messages)
        
        return {
            "messages": [response],
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


async def tool_node(state: AdvancedChatState, config: RunnableConfig) -> Dict[str, Any]:
    """Node to handle tool calls."""
    try:
        # Initialize MCP client and get tools
        mcp_client = await initialize_mcp_client()
        tools = await mcp_client.get_tools()
        
        # Get the last message which should contain tool calls
        last_message = state["messages"][-1]
        
        # Execute tool calls
        tool_results = []
        if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
            for tool_call in last_message.tool_calls:
                tool_name = tool_call["name"]
                tool_args = tool_call["args"]
                
                # Find the corresponding tool and execute it
                for tool in tools:
                    if tool.name == tool_name:
                        try:
                            result = await tool.ainvoke(tool_args)
                            tool_results.append({
                                "tool_call_id": tool_call["id"],
                                "content": str(result)
                            })
                        except Exception as e:
                            tool_results.append({
                                "tool_call_id": tool_call["id"],
                                "content": f"Error executing tool {tool_name}: {str(e)}"
                            })
                        break
        
        # Create tool message with results
        from langchain_core.messages import ToolMessage
        tool_messages = [ToolMessage(content=result["content"], tool_call_id=result["tool_call_id"]) 
                        for result in tool_results]
        
        return {"messages": tool_messages}
        
    except Exception as e:
        error_message = AIMessage(content=f"Error executing tools: {str(e)}")
        return {"messages": [error_message]}


def should_continue(state: AdvancedChatState) -> str:
    """Determine whether to continue with tool calls or end."""
    last_message = state["messages"][-1]
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    return "end"


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
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("advanced_chat")
    
    # Add conditional edges
    workflow.add_conditional_edges(
        "advanced_chat",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Add edge from tools back to chat
    workflow.add_edge("tools", "advanced_chat")
    
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