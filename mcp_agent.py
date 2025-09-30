"""
MCP-Enabled AI Agent for LangGraph Platform

A conversational AI agent that integrates with MCP (Model Context Protocol) tools
and is compatible with LangGraph Platform Studio for testing.
"""

import os
import asyncio
import json
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

# Import MCP client functionality
from McpClient import MCPClient


class MCPAgentState(TypedDict):
    """State for MCP-enabled AI agent."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    session_id: str
    conversation_count: int
    mcp_tools_available: bool


# Global MCP client instance
mcp_client: Optional[MCPClient] = None


async def initialize_mcp_client() -> Optional[MCPClient]:
    """Initialize the MCP client connection."""
    global mcp_client
    if mcp_client is None:
        try:
            mcp_client = MCPClient()
            mcp_server_url = os.getenv("MCP_SERVER_URL")
            if mcp_server_url:
                await mcp_client.connect_to_sse_server(mcp_server_url)
                return mcp_client
            else:
                print("Warning: MCP_SERVER_URL not set. MCP tools will not be available.")
                return None
        except Exception as e:
            print(f"Warning: Failed to connect to MCP server: {e}")
            return None
    return mcp_client


def create_llm() -> ChatOpenAI:
    """Create and configure the OpenAI LLM instance."""
    return ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


async def get_available_mcp_tools() -> List[Dict[str, Any]]:
    """Get available MCP tools."""
    global mcp_client
    if mcp_client and mcp_client.session:
        try:
            response = await mcp_client.session.list_tools()
            return [{
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema if tool.inputSchema else {}
                }
            } for tool in response.tools]
        except Exception as e:
            print(f"Error getting MCP tools: {e}")
            return []
    return []


async def execute_mcp_tool(tool_name: str, tool_args: Dict[str, Any]) -> str:
    """Execute an MCP tool and return the result."""
    global mcp_client
    if mcp_client and mcp_client.session:
        try:
            result = await mcp_client.session.call_tool(tool_name, tool_args)
            # Handle different result types
            if hasattr(result, 'content'):
                if isinstance(result.content, list):
                    # If content is a list, join the items
                    return "\n".join(str(item) for item in result.content)
                else:
                    return str(result.content)
            else:
                return str(result)
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"
    return f"MCP client not available for tool {tool_name}"


async def mcp_agent_node_async(state: MCPAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Async MCP-enabled agent node that can use MCP tools.
    
    Args:
        state: Agent state with messages and context
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
                "conversation_count": conversation_count,
                "mcp_tools_available": state.get("mcp_tools_available", False)
            }
        
        # Initialize MCP client if not already done
        mcp_client = await initialize_mcp_client()
        
        # Get available MCP tools
        available_tools = await get_available_mcp_tools()
        
        # Create LLM
        llm = create_llm()
        
        # Prepare messages for OpenAI
        openai_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                openai_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                openai_messages.append({"role": "assistant", "content": msg.content})
        
        # Add system message if first conversation
        if conversation_count == 0:
            system_prompt = """You are a helpful AI assistant with access to various tools through MCP (Model Context Protocol). 
            When users ask questions that can be answered with available tools, use them to provide accurate information.
            Always explain what you're doing when using tools."""
            openai_messages.insert(0, {"role": "system", "content": system_prompt})
        
        # Make initial API call with tools if available
        if available_tools:
            # Use OpenAI directly for tool calling
            from openai import OpenAI
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            # Convert messages to OpenAI format
            openai_messages_formatted = []
            for msg in openai_messages:
                openai_messages_formatted.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=openai_messages_formatted,
                tools=available_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            response_content = message.content or ""
            tool_calls = message.tool_calls or []
        else:
            response = llm.invoke(openai_messages)
            response_content = response.content
            tool_calls = []
        
        # Process tool calls if any
        if tool_calls:
            tool_results = []
            final_content = [response_content] if response_content else []
            
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Execute the tool
                tool_result = await execute_mcp_tool(tool_name, tool_args)
                tool_results.append(f"[Calling tool {tool_name} with args {tool_args}]")
                tool_results.append(tool_result)
            
            # Continue conversation with tool results
            openai_messages.append({"role": "assistant", "content": response_content or ""})
            # Ensure all tool_results are strings
            tool_results_str = []
            for result in tool_results:
                if isinstance(result, list):
                    tool_results_str.append("\n".join(str(item) for item in result))
                else:
                    tool_results_str.append(str(result))
            openai_messages.append({"role": "user", "content": "\n".join(tool_results_str)})
            
            # Get final response using OpenAI directly
            final_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=openai_messages,
                max_tokens=1000
            )
            final_content.append(final_response.choices[0].message.content or "")
            
            response_content = "\n".join(final_content)
        
        # Create AI response message
        ai_response = AIMessage(content=response_content)
        
        return {
            "messages": [ai_response],
            "conversation_count": conversation_count + 1,
            "mcp_tools_available": len(available_tools) > 0
        }
        
    except Exception as e:
        # Handle errors gracefully
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
        )
        return {
            "messages": [error_message],
            "conversation_count": state.get("conversation_count", 0),
            "mcp_tools_available": state.get("mcp_tools_available", False)
        }


def mcp_agent_node(state: MCPAgentState, config: RunnableConfig) -> Dict[str, Any]:
    """
    MCP-enabled agent node that can use MCP tools.
    Wrapper to handle async operations in sync context.
    
    Args:
        state: Agent state with messages and context
        config: Runtime configuration from LangGraph platform
        
    Returns:
        Dictionary containing the AI response and updated state
    """
    try:
        # Run the async function in a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(mcp_agent_node_async(state, config))
            return result
        finally:
            loop.close()
    except Exception as e:
        # Handle errors gracefully
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
        )
        return {
            "messages": [error_message],
            "conversation_count": state.get("conversation_count", 0),
            "mcp_tools_available": state.get("mcp_tools_available", False)
        }


def create_mcp_agent_graph() -> StateGraph:
    """
    Create an MCP-enabled agent graph.
    
    Returns:
        Compiled StateGraph with MCP tool capabilities
    """
    # Create the graph with MCP agent state
    workflow = StateGraph(MCPAgentState)
    
    # Add nodes
    workflow.add_node("mcp_agent", mcp_agent_node)
    
    # Set entry point
    workflow.set_entry_point("mcp_agent")
    
    # Add edge to end
    workflow.add_edge("mcp_agent", END)
    
    # Compile and return
    return workflow.compile()


# Export graph for LangGraph Platform deployment
# This variable will be automatically discovered by the platform
mcp_agent_graph = create_mcp_agent_graph()


async def cleanup_mcp_client():
    """Clean up MCP client resources."""
    global mcp_client
    if mcp_client:
        await mcp_client.cleanup()
        mcp_client = None


def main():
    """
    Local testing function - not used in platform deployment.
    Run this file directly to test the MCP agent locally.
    """
    print("Testing MCP-Enabled AI Agent...")
    
    # Test the MCP agent graph
    test_state = {
        "messages": [HumanMessage(content="What's the weather like in Spokane?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0,
        "mcp_tools_available": False
    }
    
    try:
        result = mcp_agent_graph.invoke(test_state)
        print("MCP Agent Response:")
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                print(f"- {msg.content}")
        print("Conversation Count:", result["conversation_count"])
        print("MCP Tools Available:", result["mcp_tools_available"])
    except Exception as e:
        print(f"Test failed: {e}")


if __name__ == "__main__":
    main()
