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
from langgraph.prebuilt import ToolNode
from langchain_core.tools import tool
from typing_extensions import Annotated, TypedDict

# Import MCP client (only for local development)
try:
    from client import MCPClient
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    MCPClient = None


def create_llm(bind_tools: bool = False) -> ChatOpenAI:
    """Create and configure the OpenAI LLM instance."""
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )
    
    if bind_tools:
        # Bind MCP tools if available
        tools = get_mcp_tools()
        if tools:
            llm = llm.bind_tools(tools)
    
    return llm


# Global MCP client instance for tool access
_mcp_client = None

async def get_real_mcp_tools():
    """Get real MCP tools from connected server."""
    global _mcp_client
    if not _mcp_client or not _mcp_client.session:
        return []
    
    try:
        response = await _mcp_client.session.list_tools()
        tools = []
        
        for tool in response.tools:
            @tool
            def create_tool_func(tool_name, tool_description, tool_schema):
                async def tool_func(**kwargs) -> str:
                    try:
                        result = await _mcp_client.session.call_tool(tool_name, kwargs)
                        return result.content
                    except Exception as e:
                        return f"Error calling {tool_name}: {str(e)}"
                
                tool_func.__name__ = tool_name
                tool_func.__doc__ = tool_description
                return tool_func
            
            tool_func = create_tool_func(tool.name, tool.description, tool.inputSchema)
            tools.append(tool_func)
        
        return tools
    except Exception as e:
        print(f"Error getting MCP tools: {e}")
        return []

async def get_real_mcp_tools_from_server():
    """Get real MCP tools from the connected server, just like client.py does."""
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    if not mcp_server_url or not MCP_AVAILABLE:
        return []
    
    client = None
    try:
        # Create MCP client and connect (same as client.py)
        client = MCPClient()
        await client.connect_to_sse_server(server_url=mcp_server_url)
        
        # List available tools (same as client.py)
        response = await client.session.list_tools()
        tools = []
        
        # Create LangChain tools from MCP tools (same approach as client.py)
        for mcp_tool in response.tools:
            def create_dynamic_tool(tool_name, tool_description, tool_schema, mcp_client, mcp_session):
                def tool_func(**kwargs) -> str:
                    print(f"🔧 Tool function {tool_name} called with kwargs: {kwargs}")
                    try:
                        import asyncio
                        
                        async def call_tool():
                            try:
                                # Create a new client for each tool call to avoid context issues
                                new_client = MCPClient()
                                await new_client.connect_to_sse_server(server_url=mcp_server_url)
                                print(f"🔧 Calling MCP tool {tool_name} with args: {kwargs}")
                                result = await new_client.session.call_tool(tool_name, kwargs)
                                await new_client.cleanup()
                                print(f"✅ MCP tool {tool_name} result: {result.content}")
                                return result.content
                            except Exception as e:
                                print(f"❌ Error in MCP tool call {tool_name}: {e}")
                                return f"Error calling {tool_name}: {str(e)}"
                        
                        # Handle async call in sync context
                        try:
                            loop = asyncio.get_event_loop()
                            if loop.is_running():
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, call_tool())
                                    return future.result(timeout=15)
                            else:
                                return loop.run_until_complete(call_tool())
                        except Exception as e:
                            print(f"Error in async handling for {tool_name}: {e}")
                            try:
                                return asyncio.run(call_tool())
                            except Exception as e2:
                                return f"Error calling {tool_name}: {str(e2)}"
                            
                    except Exception as e:
                        print(f"Error in tool function {tool_name}: {e}")
                        return f"Error calling {tool_name}: {str(e)}"
                
                tool_func.__name__ = tool_name
                tool_func.__doc__ = tool_description
                return tool_func
            
            tool_func = create_dynamic_tool(mcp_tool.name, mcp_tool.description, mcp_tool.inputSchema, client, client.session)
            
            # Create a proper tool function that handles arguments correctly
            def create_proper_tool(tool_name, tool_description, mcp_server_url, tool_schema):
                if tool_schema and 'properties' in tool_schema:
                    # Create function with explicit parameters based on schema
                    properties = tool_schema['properties']
                    
                    # Build function signature dynamically
                    def create_tool_with_explicit_params():
                        # Create a function with explicit parameters
                        def tool_func(**kwargs) -> str:
                            print(f"🔧 Tool function {tool_name} called with kwargs: {kwargs}")
                            try:
                                import asyncio
                                
                                async def call_tool():
                                    try:
                                        new_client = MCPClient()
                                        await new_client.connect_to_sse_server(server_url=mcp_server_url)
                                        print(f"🔧 Calling MCP tool {tool_name} with args: {kwargs}")
                                        result = await new_client.session.call_tool(tool_name, kwargs)
                                        await new_client.cleanup()
                                        print(f"✅ MCP tool {tool_name} result: {result.content}")
                                        return result.content
                                    except Exception as e:
                                        print(f"❌ Error in MCP tool call {tool_name}: {e}")
                                        return f"Error calling {tool_name}: {str(e)}"
                                
                                try:
                                    loop = asyncio.get_event_loop()
                                    if loop.is_running():
                                        import concurrent.futures
                                        with concurrent.futures.ThreadPoolExecutor() as executor:
                                            future = executor.submit(asyncio.run, call_tool())
                                            return future.result(timeout=15)
                                    else:
                                        return loop.run_until_complete(call_tool())
                                except Exception as e:
                                    print(f"Error in async handling for {tool_name}: {e}")
                                    try:
                                        return asyncio.run(call_tool())
                                    except Exception as e2:
                                        return f"Error calling {tool_name}: {str(e2)}"
                                    
                            except Exception as e:
                                print(f"Error in tool function {tool_name}: {e}")
                                return f"Error calling {tool_name}: {str(e)}"
                        
                        tool_func.__name__ = tool_name
                        tool_func.__doc__ = tool_description
                        return tool_func
                    
                    return create_tool_with_explicit_params()
                else:
                    # Fallback to kwargs approach
                    def tool_func(**kwargs) -> str:
                        print(f"🔧 Tool function {tool_name} called with kwargs: {kwargs}")
                        try:
                            import asyncio
                            
                            async def call_tool():
                                try:
                                    new_client = MCPClient()
                                    await new_client.connect_to_sse_server(server_url=mcp_server_url)
                                    print(f"🔧 Calling MCP tool {tool_name} with args: {kwargs}")
                                    result = await new_client.session.call_tool(tool_name, kwargs)
                                    await new_client.cleanup()
                                    print(f"✅ MCP tool {tool_name} result: {result.content}")
                                    return result.content
                                except Exception as e:
                                    print(f"❌ Error in MCP tool call {tool_name}: {e}")
                                    return f"Error calling {tool_name}: {str(e)}"
                            
                            try:
                                loop = asyncio.get_event_loop()
                                if loop.is_running():
                                    import concurrent.futures
                                    with concurrent.futures.ThreadPoolExecutor() as executor:
                                        future = executor.submit(asyncio.run, call_tool())
                                        return future.result(timeout=15)
                                else:
                                    return loop.run_until_complete(call_tool())
                            except Exception as e:
                                print(f"Error in async handling for {tool_name}: {e}")
                                try:
                                    return asyncio.run(call_tool())
                                except Exception as e2:
                                    return f"Error calling {tool_name}: {str(e2)}"
                                
                        except Exception as e:
                            print(f"Error in tool function {tool_name}: {e}")
                            return f"Error calling {tool_name}: {str(e)}"
                    
                    tool_func.__name__ = tool_name
                    tool_func.__doc__ = tool_description
                    return tool_func
            
            # Create the tool function
            proper_tool_func = create_proper_tool(mcp_tool.name, mcp_tool.description, mcp_server_url, mcp_tool.inputSchema)
            
            # Create LangChain tool with proper argument handling
            if mcp_tool.inputSchema and 'properties' in mcp_tool.inputSchema:
                # Create a Pydantic model for the arguments
                from pydantic import BaseModel, create_model
                
                properties = mcp_tool.inputSchema['properties']
                required = mcp_tool.inputSchema.get('required', [])
                
                # Create fields for the Pydantic model
                fields = {}
                for prop_name, prop_info in properties.items():
                    field_type = str  # Default to string, could be enhanced
                    if prop_info.get('type') == 'number':
                        field_type = float
                    elif prop_info.get('type') == 'integer':
                        field_type = int
                    elif prop_info.get('type') == 'boolean':
                        field_type = bool
                    
                    fields[prop_name] = (field_type, ... if prop_name in required else None)
                
                # Create the Pydantic model
                args_model = create_model(f"{mcp_tool.name}Arguments", **fields)
                
                # Create the tool with the proper model
                proper_tool_func.args_schema = args_model
                langchain_tool = tool(proper_tool_func)
            else:
                # Fallback to basic tool
                langchain_tool = tool(proper_tool_func)
            
            tools.append(langchain_tool)
        
        return tools
        
    except Exception as e:
        print(f"Error getting MCP tools from server: {e}")
        return []
    finally:
        if client:
            try:
                await client.cleanup()
            except Exception as e:
                print(f"Error cleaning up client: {e}")

def get_mcp_tools():
    """Get MCP tools as LangChain tools for platform deployment."""
    # Try to get real MCP tools from server
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    print(f"🔍 Checking for MCP server: {mcp_server_url}")
    print(f"🔍 MCP_AVAILABLE: {MCP_AVAILABLE}")
    
    if mcp_server_url and MCP_AVAILABLE:
        try:
            import asyncio
            print("🚀 Attempting to get real MCP tools...")
            
            # Try to get existing event loop or create new one
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    print("⚠️ Event loop is running, using thread pool...")
                    # If loop is running, we need to use a different approach
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, get_real_mcp_tools_from_server())
                        tools = future.result(timeout=15)
                        if tools:
                            print(f"✅ Got {len(tools)} real MCP tools")
                            return tools
                else:
                    print("🔄 Using existing event loop...")
                    tools = loop.run_until_complete(get_real_mcp_tools_from_server())
                    if tools:
                        print(f"✅ Got {len(tools)} real MCP tools")
                        return tools
            except Exception as e:
                print(f"⚠️ Error with existing loop: {e}")
                # Fallback: create new event loop
                print("🔄 Creating new event loop...")
                tools = asyncio.run(get_real_mcp_tools_from_server())
                if tools:
                    print(f"✅ Got {len(tools)} real MCP tools")
                    return tools
                    
        except Exception as e:
            print(f"❌ Failed to get real MCP tools: {e}")
    else:
        print("⚠️ No MCP server URL or MCP not available, using placeholder tools")
    
    # Fallback to placeholder tools if MCP server not available
    print("🔄 Using placeholder tools...")
    
    @tool
    def get_weather(location: str) -> str:
        """Get current weather for a location. This represents an MCP tool."""
        return f"Weather for {location}: This is a placeholder response from an MCP weather tool."

    @tool
    def search_web(query: str) -> str:
        """Search the web for information. This represents an MCP search tool."""
        return f"Search results for '{query}': This is a placeholder response from an MCP search tool."

    @tool
    def get_news(topic: str) -> str:
        """Get latest news about a topic. This represents an MCP news tool."""
        return f"Latest news about '{topic}': This is a placeholder response from an MCP news tool."

    return [get_weather, search_web, get_news]


class AdvancedChatState(TypedDict):
    """Enhanced state for advanced chat agent with session management."""
    messages: Annotated[List[BaseMessage], add_messages]
    user_id: str
    session_id: str
    conversation_count: int


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
        llm = create_llm(bind_tools=True)
        
        # Add conversation context if this is a continuing conversation
        messages = state["messages"]
        conversation_count = state.get("conversation_count", 0)
        
        if conversation_count == 0:
            # First message in session
            system_context = AIMessage(
                content="Hello! I'm your advanced AI assistant with MCP tool capabilities. I can help you with questions, analysis, and conversation. I also have access to various tools through MCP (Model Context Protocol). How can I help you today?"
            )
            messages = [system_context] + messages
        
        response = llm.invoke(messages)
        
        return {
            "messages": [response],
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


def should_continue(state: AdvancedChatState) -> str:
    """
    Determine whether to continue with tool calls or end the conversation.
    
    Args:
        state: Current advanced chat state
        
    Returns:
        Next node name or END
    """
    messages = state["messages"]
    last_message = messages[-1]
    
    # If the last message has tool calls, we should run the tools
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        return "tools"
    else:
        return END


def create_advanced_graph() -> StateGraph:
    """
    Create an advanced chat agent graph with session management and MCP tools.
    
    Returns:
        Compiled StateGraph with enhanced features
    """
    # Create the graph with advanced state
    workflow = StateGraph(AdvancedChatState)
    
    # Get MCP tools
    tools = get_mcp_tools()
    
    # Add nodes
    workflow.add_node("advanced_chat", advanced_chat_node)
    if tools:
        workflow.add_node("tools", ToolNode(tools))
    
    # Set entry point
    workflow.set_entry_point("advanced_chat")
    
    # Add conditional logic for tool usage
    if tools:
        workflow.add_conditional_edges(
            "advanced_chat",
            should_continue,
            {
                "tools": "tools",
                END: END,
            },
        )
        
        # After running tools, go back to advanced chat
        workflow.add_edge("tools", "advanced_chat")
    else:
        # No tools available, direct to end
        workflow.add_edge("advanced_chat", END)
    
    # Compile and return
    return workflow.compile()


# Export graph for LangGraph Platform deployment
# This variable will be automatically discovered by the platform
advanced_graph = create_advanced_graph()


def test_agent():
    """
    Test function for the LangGraph agent.
    """
    print("Testing Advanced Chat Agent...")
    
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


async def test_langgraph_with_mcp():
    """
    Test LangGraph agent with real MCP tools.
    """
    global _mcp_client
    
    if not _mcp_client or not _mcp_client.session:
        print("❌ MCP client not connected. Cannot test with real MCP tools.")
        return
    
    print("🧪 Testing LangGraph Agent with Real MCP Tools...")
    
    # Get real MCP tools
    real_tools = await get_real_mcp_tools()
    if not real_tools:
        print("❌ No real MCP tools available.")
        return
    
    print(f"✅ Found {len(real_tools)} real MCP tools")
    
    # Create a graph with real MCP tools
    workflow = StateGraph(AdvancedChatState)
    workflow.add_node("advanced_chat", advanced_chat_node)
    workflow.add_node("tools", ToolNode(real_tools))
    workflow.set_entry_point("advanced_chat")
    
    workflow.add_conditional_edges(
        "advanced_chat",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    workflow.add_edge("tools", "advanced_chat")
    
    test_graph = workflow.compile()
    
    # Test with weather query
    test_state = {
        "messages": [HumanMessage(content="What's the weather like in Spokane?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0
    }
    
    try:
        result = test_graph.invoke(test_state)
        print("\n🤖 LangGraph with Real MCP Tools Response:")
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                print(f"- {msg.content}")
        print("Conversation Count:", result["conversation_count"])
    except Exception as e:
        print(f"Test failed: {e}")


async def main():
    """
    Main function with MCP client integration.
    Run this file directly to start the interactive chat with MCP tools.
    """
    global _mcp_client
    
    if not MCP_AVAILABLE:
        print("❌ MCP client not available. Running in LangGraph-only mode.")
        print("🤖 Testing LangGraph Agent with built-in MCP tools...")
        test_agent()
        return
    
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    
    if not mcp_server_url:
        print("❌ MCP_SERVER_URL not set. Please set it in your .env file or environment.")
        print("Example: export MCP_SERVER_URL=http://localhost:8080/sse")
        print("🤖 Running in LangGraph-only mode with built-in MCP tools...")
        test_agent()
        return
    
    print("🚀 Starting LangGraph Agent with MCP Client Integration...")
    print(f"📡 Connecting to MCP server: {mcp_server_url}")
    
    _mcp_client = MCPClient()
    try:
        # Connect to MCP server
        await _mcp_client.connect_to_sse_server(server_url=mcp_server_url)
        
        # Start interactive chat loop
        print("\n🤖 LangGraph Agent with MCP Tools Ready!")
        print("Type your queries or 'quit' to exit.")
        print("Special commands: 'test_agent', 'status', 'help', 'test_langgraph'")
        
        while True:
            try:
                # Use asyncio to handle input in a non-blocking way
                loop = asyncio.get_event_loop()
                query = await loop.run_in_executor(None, input, "\nQuery: ")
                query = query.strip()
                
                if query.lower() == 'quit':
                    break
                elif query.lower() == 'test_agent':
                    test_agent()
                    continue
                elif query.lower() == 'test_langgraph':
                    # Test LangGraph with real MCP tools
                    await test_langgraph_with_mcp()
                    continue
                elif query.lower() == 'status':
                    print("📊 Status: LangGraph Agent with MCP Client active")
                    print(f"🔗 MCP Server: {mcp_server_url}")
                    continue
                elif query.lower() == 'help':
                    print("\n📋 Available Commands:")
                    print("- Ask any question (will use MCP tools if needed)")
                    print("- 'test_agent' - Test the LangGraph agent directly")
                    print("- 'test_langgraph' - Test LangGraph with real MCP tools")
                    print("- 'status' - Show current status")
                    print("- 'help' - Show this help")
                    print("- 'quit' - Exit the application")
                    continue
                    
                # Process query using MCP client
                print("\n🤖 Processing with MCP tools...")
                response = await _mcp_client.process_query(query)
                print("\n" + response)
                    
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except EOFError:
                print("\nInput stream closed. Exiting...")
                break
            except Exception as e:
                print(f"\nError: {str(e)}")
                
    except KeyboardInterrupt:
        print("\nShutting down...")
    except Exception as e:
        print(f"\nUnexpected error: {e}")
    finally:
        await _mcp_client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())