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


def get_mcp_tools():
    """Get MCP tools as LangChain tools for platform deployment."""
    # This would be populated with actual MCP tools in a real deployment
    # For now, we'll create some example tools that represent MCP capabilities
    
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


async def main():
    """
    Main function with MCP client integration.
    Run this file directly to start the interactive chat with MCP tools.
    """
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
    
    client = MCPClient()
    try:
        # Connect to MCP server
        await client.connect_to_sse_server(server_url=mcp_server_url)
        
        # Start interactive chat loop
        print("\n🤖 LangGraph Agent with MCP Tools Ready!")
        print("Type your queries or 'quit' to exit.")
        print("Special commands: 'test_agent', 'status', 'help'")
        
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
                elif query.lower() == 'status':
                    print("📊 Status: LangGraph Agent with MCP Client active")
                    print(f"🔗 MCP Server: {mcp_server_url}")
                    continue
                elif query.lower() == 'help':
                    print("\n📋 Available Commands:")
                    print("- Ask any question (will use MCP tools if needed)")
                    print("- 'test_agent' - Test the LangGraph agent directly")
                    print("- 'status' - Show current status")
                    print("- 'help' - Show this help")
                    print("- 'quit' - Exit the application")
                    continue
                    
                # Process query using MCP client
                print("\n🤖 Processing with MCP tools...")
                response = await client.process_query(query)
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
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())