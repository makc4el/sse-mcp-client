#!/usr/bin/env python3
"""
LangGraph Chat-Compatible MCP Agent

This module provides a LangGraph-compatible graph that works with
LangGraph Studio's Chat interface and accepts the same input format
as the langchain_project AI agent.
"""

import logging
import os
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI

# Import ToolNode with fallback for compatibility
try:
    from langgraph.prebuilt import ToolNode
    TOOLNODE_AVAILABLE = True
except ImportError:
    logger.warning("⚠️ ToolNode not available, using fallback implementation")
    TOOLNODE_AVAILABLE = False

# Import MCP integration
from mcp_client_lib.langchain_integration import MCPToolAdapter
from mcp_client_lib.config import MCPClientConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """State for the chat-enabled MCP agent graph - matches langchain_project format"""
    messages: Annotated[List[BaseMessage], add_messages]


# Global cache for MCP tools (for async contexts)
_mcp_tools_cache = []

def initialize_mcp_tools():
    """Initialize MCP tools with proper integration"""
    global _mcp_tools_cache
    
    if _mcp_tools_cache:
        logger.info(f"📋 Using cached {len(_mcp_tools_cache)} MCP tools")
        return _mcp_tools_cache  # Already initialized
    
    # Create MCP tools using the adapter
    logger.info("🔧 Initializing MCP tools...")
    try:
        import asyncio
        from mcp_client_lib.langchain_integration import MCPToolAdapter
        from mcp_client_lib.config import MCPClientConfig
        
        # Get MCP server URL
        server_url = MCPClientConfig.get_server_url()
        logger.info(f"🌐 Connecting to MCP server at: {server_url}")
        
        # Try to get event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # In async context - create basic tools synchronously
                logger.warning("⚠️ In async context - cannot run dynamic discovery, using fallback tools")
                _mcp_tools_cache = create_fallback_mcp_tools()
            else:
                # Not in async context - safe to run async
                _mcp_tools_cache = asyncio.run(load_mcp_tools_async(server_url))
        except RuntimeError:
            # No event loop - safe to run async
            _mcp_tools_cache = asyncio.run(load_mcp_tools_async(server_url))
            
    except Exception as e:
        logger.error(f"❌ MCP tool initialization failed: {e}")
        logger.info("🔄 Falling back to basic MCP tools")
        _mcp_tools_cache = create_fallback_mcp_tools()
    
    logger.info(f"✅ Initialized {len(_mcp_tools_cache)} MCP tools")
    return _mcp_tools_cache

async def load_mcp_tools_async(server_url: str):
    """Load MCP tools asynchronously"""
    try:
        from mcp_client_lib.langchain_integration import MCPToolAdapter
        
        # Create adapter and connect
        adapter = MCPToolAdapter(server_url)
        await adapter.connect()
        tools = await adapter.load_tools()
        
        logger.info(f"✅ Loaded {len(tools)} tools from MCP server")
        return tools
        
    except Exception as e:
        logger.error(f"❌ Failed to load MCP tools: {e}")
        return create_fallback_mcp_tools()

def create_fallback_mcp_tools():
    """Create fallback MCP tools for mathematical operations"""
    from langchain_core.tools import StructuredTool
    try:
        from pydantic import BaseModel, Field
    except ImportError:
        from langchain_core.pydantic_v1 import BaseModel, Field
    
    class AddNumbersInput(BaseModel):
        a: float = Field(description="First number to add")
        b: float = Field(description="Second number to add")
    
    class FindMaxInput(BaseModel):
        numbers: list = Field(description="List of numbers to find maximum from")
    
    def add_numbers_func(a: float, b: float) -> str:
        """Add two numbers together"""
        try:
            result = a + b
            return f"✅ {a} + {b} = {result}"
        except Exception as e:
            return f"❌ Addition Error: {str(e)}"
    
    def find_max_func(numbers: list) -> str:
        """Find the maximum number from a list"""
        try:
            if not numbers:
                return "❌ No numbers provided"
            max_num = max(numbers)
            return f"✅ Maximum of {numbers} is {max_num}"
        except Exception as e:
            return f"❌ Find Max Error: {str(e)}"
    
    tools = []
    try:
        tools.append(StructuredTool.from_function(
            func=add_numbers_func,
            name="add_numbers",
            description="Add two numbers together",
            args_schema=AddNumbersInput
        ))
        tools.append(StructuredTool.from_function(
            func=find_max_func,
            name="find_max", 
            description="Find the maximum number from a list of numbers",
            args_schema=FindMaxInput
        ))
        logger.info(f"✅ Created {len(tools)} fallback MCP tools")
    except Exception as e:
        logger.error(f"❌ Failed to create fallback MCP tools: {e}")
    
    return tools

class FallbackToolNode:
    """Fallback ToolNode implementation for compatibility"""
    
    def __init__(self, tools):
        self.tools = {tool.name: tool for tool in tools}
        logger.info(f"🔧 Created fallback ToolNode with {len(tools)} tools")
    
    def __call__(self, state: ChatState, config: RunnableConfig = None) -> Dict[str, Any]:
        """Execute tool calls from the last message"""
        try:
            messages = state["messages"]
            last_message = messages[-1]
            
            if not (hasattr(last_message, 'tool_calls') and last_message.tool_calls):
                logger.warning("⚠️ No tool calls found in message")
                return {"messages": []}
            
            tool_results = []
            
            for tool_call in last_message.tool_calls:
                tool_name = tool_call.get("name")
                tool_args = tool_call.get("args", {})
                tool_id = tool_call.get("id", "unknown")
                
                if tool_name in self.tools:
                    try:
                        result = self.tools[tool_name].invoke(tool_args)
                        
                        # Create a proper tool message
                        from langchain_core.messages import ToolMessage
                        tool_message = ToolMessage(
                            content=str(result),
                            tool_call_id=tool_id
                        )
                        tool_results.append(tool_message)
                        
                        logger.info(f"✅ Tool {tool_name} executed successfully")
                    except Exception as e:
                        logger.error(f"❌ Tool {tool_name} execution failed: {e}")
                        # Create error tool message
                        from langchain_core.messages import ToolMessage
                        error_message = ToolMessage(
                            content=f"Error executing {tool_name}: {str(e)}",
                            tool_call_id=tool_id
                        )
                        tool_results.append(error_message)
                else:
                    logger.error(f"❌ Tool {tool_name} not found")
                    # Create not found tool message
                    from langchain_core.messages import ToolMessage
                    not_found_message = ToolMessage(
                        content=f"Tool {tool_name} not found",
                        tool_call_id=tool_id
                    )
                    tool_results.append(not_found_message)
            
            return {"messages": tool_results}
            
        except Exception as e:
            logger.error(f"❌ FallbackToolNode execution failed: {e}")
            return {"messages": []}

def create_llm_with_tools() -> ChatOpenAI:
    """Create and configure the OpenAI LLM instance with MCP tools"""
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.3,
        openai_api_key=api_key,
    )
    
    # Get MCP tools and bind them to the LLM
    mcp_tools = initialize_mcp_tools()
    if mcp_tools:
        llm = llm.bind_tools(mcp_tools)
        logger.info(f"✅ LLM bound with {len(mcp_tools)} MCP tools")
    else:
        logger.warning("⚠️ No MCP tools available for LLM binding")
    
    return llm


def chat_node(state: ChatState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Main chat node that processes user input and generates AI responses with MCP tools.
    Uses the same pattern as langchain_project for consistent input/output handling.
    
    Args:
        state: Current chat state containing message history
        config: Runtime configuration from LangGraph platform
        
    Returns:
        Dictionary containing the AI response message
    """
    try:
        messages = state["messages"]
        last_message = messages[-1] if messages else None
        
        # Add system message if this is the first interaction
        if len(messages) == 1 and last_message and isinstance(last_message, HumanMessage):
            system_msg = SystemMessage(
                content="""You are a helpful AI assistant with access to mathematical tools via MCP (Model Context Protocol).

🔧 **Available MCP Tools:**
• **add_numbers** - Add two numbers together
• **find_max** - Find the maximum value from a list of numbers

🎯 **How to Help:**
- For addition: "What is 25 + 37?" or "Add 100 and 200"
- For maximum: "Which is larger: 42 or 17?" or "Find the maximum of 15, 89, and 33"

When users ask mathematical questions, use the appropriate MCP tools to provide accurate answers. Always use the tools rather than calculating manually to demonstrate MCP integration."""
            )
            messages = [system_msg] + messages
        
        # Create LLM with MCP tools bound
        llm = create_llm_with_tools()
        
        # Generate response using the LLM with tools
        response = llm.invoke(messages)
        
        logger.info(f"Generated response using LLM with MCP tools")
        return {"messages": [response]}
        
    except Exception as e:
        # Handle errors gracefully
        logger.error(f"Chat processing failed: {e}")
        error_message = AIMessage(
            content=f"I apologize, but I encountered an error: {str(e)}. Please try again."
        )
        return {"messages": [error_message]}

def should_continue(state: ChatState) -> str:
    """
    Determine whether to continue with tool calls or end the conversation.
    
    Args:
        state: Current chat state
        
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


def create_chat_graph():
    """
    Create the MCP-enabled chat agent graph that matches langchain_project structure.
    
    Returns:
        Compiled StateGraph ready for deployment
    """
    # Create the graph
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("chat", chat_node)
    
    # Initialize MCP tools for the ToolNode
    mcp_tools = initialize_mcp_tools()
    
    # Use appropriate ToolNode implementation
    if TOOLNODE_AVAILABLE:
        tool_node = ToolNode(mcp_tools)
        logger.info("✅ Using official ToolNode")
    else:
        tool_node = FallbackToolNode(mcp_tools)
        logger.info("✅ Using fallback ToolNode")
    
    workflow.add_node("tools", tool_node)
    
    # Set entry point
    workflow.set_entry_point("chat")
    
    # Add conditional logic for tool usage
    workflow.add_conditional_edges(
        "chat",
        should_continue,
        {
            "tools": "tools",
            END: END,
        },
    )
    
    # After running tools, go back to chat
    workflow.add_edge("tools", "chat")
    
    # Compile and return
    return workflow.compile()


# Export graph for LangGraph Platform deployment - matches langchain_project pattern
try:
    # Initialize MCP tools on module load
    logger.info("🔄 Initializing MCP tools for graph creation...")
    initialize_mcp_tools()
    
    # Create the graph
    graph = create_chat_graph()
    logger.info("✅ MCP chat graph created successfully for platform deployment")
except Exception as e:
    logger.error(f"❌ Graph creation failed: {e}")
    # Create minimal fallback graph
    logger.info("🔧 Creating minimal fallback graph...")
    
    from langgraph.graph import StateGraph, END
    
    # Fallback graph with basic tools
    fallback_tools = create_fallback_mcp_tools()
    
    # Use appropriate ToolNode implementation for fallback too
    if TOOLNODE_AVAILABLE:
        fallback_tool_node = ToolNode(fallback_tools)
    else:
        fallback_tool_node = FallbackToolNode(fallback_tools)
    
    fallback_workflow = StateGraph(ChatState)
    fallback_workflow.add_node("chat", chat_node)
    fallback_workflow.add_node("tools", fallback_tool_node)
    fallback_workflow.set_entry_point("chat")
    fallback_workflow.add_conditional_edges("chat", should_continue, {"tools": "tools", END: END})
    fallback_workflow.add_edge("tools", "chat")
    graph = fallback_workflow.compile()
    
    logger.info("✅ Minimal fallback graph created successfully")


def main():
    """
    Local testing function - matches langchain_project pattern.
    Run this file directly to test the MCP-integrated agent locally.
    """
    print("🚀 Testing MCP AI Agent Integration...")
    print("="*60)
    
    print("1. Testing MCP Chat Agent - First Interaction...")
    
    # Test the graph - first interaction (matches langchain_project format)
    test_state = {
        "messages": [HumanMessage(content="Hello! What is 25 + 37?")]
    }
    
    try:
        result = graph.invoke(test_state)
        print("Agent Response:")
        print(result["messages"][-1].content)
        
        # Test tool usage
        if hasattr(result["messages"][-1], 'tool_calls') and result["messages"][-1].tool_calls:
            print(f"Tool calls made: {len(result['messages'][-1].tool_calls)}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("2. Testing Maximum Finding...")
    
    # Test maximum finding functionality
    max_test_state = {
        "messages": [HumanMessage(content="Which is larger: 42 or 17?")]
    }
    
    try:
        max_result = graph.invoke(max_test_state)
        print("Maximum Response:")
        print(max_result["messages"][-1].content)
        
    except Exception as e:
        print(f"❌ Maximum test failed: {e}")
    
    print("\n" + "="*60)
    print("3. Testing Help Functionality...")
    
    # Test help functionality
    help_test_state = {
        "messages": [HumanMessage(content="Help me understand what you can do")]
    }
    
    try:
        help_result = graph.invoke(help_test_state)
        print("Help Response:")
        print(help_result["messages"][-1].content)
        
    except Exception as e:
        print(f"❌ Help test failed: {e}")
    
    print("\n" + "="*60)
    print("✅ Integration Testing Complete!")
    print("\n📋 Summary:")
    print("• Agent now uses LangGraph platform message format")
    print("• Compatible with langchain_project input structure") 
    print("• Uses proper BaseMessage types (HumanMessage, AIMessage, SystemMessage)")
    print("• Integrates with MCP server for mathematical operations")
    print("• Supports tool calling with add_numbers and find_max")
    print("• Includes proper error handling and fallback mechanisms")
    
    print("\n🔗 Compatible Input Format:")
    print('{"messages": [{"type": "human", "content": "What is 25 + 37?"}]}')


if __name__ == "__main__":
    main()
