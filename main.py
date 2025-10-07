"""
LangGraph Platform-Ready Chat Agent

A production-ready conversational AI agent built with LangGraph and OpenAI GPT-4o-mini.
Designed for seamless deployment on LangGraph Platform with API support.
"""

import os
import json
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

from typing import Optional
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.sse import sse_client

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()

    async def connect_to_sse_server(self, server_url: str):
        """Connect to an MCP server running with SSE transport"""
        # Store the context managers so they stay alive
        self._streams_context = sse_client(url=server_url)
        streams = await self._streams_context.__aenter__()

        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # Initialize
        await self.session.initialize()

        # List available tools to verify connection
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])


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


def advanced_chat_node(state: AdvancedChatState) -> Dict[str, Any]:
    """
    Advanced chat node with session management and MCP tool integration.
    
    Args:
        state: Enhanced chat state with user and session information
        
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
        
        # Check if we have MCP client available
        global client
        available_tools = []
        if client and client.session:
            try:
                # Use asyncio to run the async MCP call
                import asyncio
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(client.session.list_tools())
                available_tools = [{
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema if tool.inputSchema else {}
                    }
                } for tool in response.tools]
                loop.close()
            except Exception as e:
                print(f"Warning: Could not get MCP tools: {e}")
        
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
        
        # Use OpenAI directly for tool calling
        from openai import OpenAI
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Make initial API call with tools if available
        if available_tools:
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=openai_messages,
                tools=available_tools,
                tool_choice="auto"
            )
            
            message = response.choices[0].message
            response_content = message.content or ""
            tool_calls = message.tool_calls or []
        else:
            # Fallback to LangChain LLM if no tools available
            llm = create_llm()
            response = llm.invoke(messages)
            response_content = response.content
            tool_calls = []
        
        # Process tool calls if any
        if tool_calls and client and client.session:
            tool_results = []
            tool_calling_messages = []
            
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # Add tool calling indication to the response
                tool_calling_messages.append(f"[Calling tool {tool_name} with args {tool_args}]")
                
                # Execute the tool using asyncio
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    result = loop.run_until_complete(client.session.call_tool(tool_name, tool_args))
                    
                    # Handle different result formats
                    if hasattr(result, 'content') and result.content:
                        if isinstance(result.content, list):
                            # Handle list of content items
                            tool_result = "\n".join([str(item) for item in result.content])
                        else:
                            tool_result = str(result.content)
                    else:
                        tool_result = str(result)
                    
                    tool_results.append(tool_result)
                    loop.close()
                except Exception as e:
                    tool_results.append(f"[Error calling tool {tool_name}: {str(e)}]")
            
            # Continue conversation with tool results
            openai_messages.append({"role": "assistant", "content": response_content or ""})
            openai_messages.append({"role": "user", "content": "\n".join(tool_results)})
            
            # Get final response using OpenAI directly
            final_response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=openai_messages,
                max_tokens=1000
            )
            
            # Build the complete response with tool calling indications
            final_content = []
            if response_content:
                final_content.append(response_content)
            
            # Add tool calling messages
            final_content.extend(tool_calling_messages)
            
            # Add the final response
            final_content.append(final_response.choices[0].message.content or "")
            
            response_content = "\n".join(final_content)
        
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


# Global MCP client instance
client = None

def initialize_mcp_client():
    """Initialize the MCP client connection synchronously."""
    global client
    if client is None:
        client = MCPClient()
        mcp_server_url = os.getenv("MCP_SERVER_URL")
        if mcp_server_url:
            # Use asyncio to run the async connection
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(client.connect_to_sse_server(server_url=mcp_server_url))
            except Exception as e:
                print(f"Warning: Could not connect to MCP server: {e}")
                client = None
            finally:
                loop.close()
    return client


# Export graph for LangGraph Platform deployment
# This variable will be automatically discovered by the platform
advanced_graph = create_advanced_graph()


def main():
    """
    Local testing function - not used in platform deployment.
    Run this file directly to test the agent locally.
    """
    print("Testing Advanced Chat Agent...")
    
    # Initialize MCP client
    print("Initializing MCP client...")
    initialize_mcp_client()

    # Test the advanced graph
    test_state = {
        "messages": [HumanMessage(content="Hello! Can you explain what you do?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0
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