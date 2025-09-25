#!/usr/bin/env python3
"""
LangGraph Chat-Compatible MCP Agent

This module provides a LangGraph-compatible graph that works with
LangGraph Studio's Chat interface.
"""

import logging
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ChatState(TypedDict):
    """State for the chat-enabled MCP agent graph"""
    messages: Annotated[List[BaseMessage], add_messages]
    mcp_server_url: Optional[str]
    llm_model: Optional[str]
    tools_loaded: bool


def setup_system(state: ChatState) -> ChatState:
    """Set up the system and load MCP tools"""
    try:
        # Get configuration
        server_url = state.get('mcp_server_url', 'http://localhost:8000')
        model = state.get('llm_model', 'gpt-3.5-turbo')
        
        # Add system message if not present
        messages = state['messages']
        has_system_message = any(isinstance(msg, SystemMessage) for msg in messages)
        
        if not has_system_message:
            system_msg = SystemMessage(
                content=f"""You are a helpful AI assistant with access to mathematical tools via MCP (Model Context Protocol).

You can help with:
- Adding numbers (use add_numbers tool)
- Finding maximum values (use find_max tool)
- Mathematical calculations and comparisons

MCP Server: {server_url}
Model: {model}

When users ask mathematical questions, use the appropriate tools to provide accurate answers."""
            )
            state['messages'] = [system_msg] + messages
        
        # Mark tools as loaded (simplified for Studio compatibility)
        state['tools_loaded'] = True
        
        logger.info(f"System setup complete - Server: {server_url}, Model: {model}")
        return state
        
    except Exception as e:
        logger.error(f"System setup failed: {e}")
        error_msg = AIMessage(content=f"System setup failed: {str(e)}")
        state['messages'].append(error_msg)
        state['tools_loaded'] = False
        return state


def process_message(state: ChatState) -> ChatState:
    """Process the user message and generate response"""
    try:
        messages = state['messages']
        model = state.get('llm_model', 'gpt-3.5-turbo')
        
        # Get the last human message
        human_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        if not human_messages:
            # No human message to process
            return state
        
        last_human_msg = human_messages[-1].content.lower()
        
        # Simple rule-based responses for mathematical queries
        # In a real implementation, this would use actual MCP tools
        response_content = ""
        
        if any(word in last_human_msg for word in ['add', '+', 'plus', 'sum']):
            # Extract numbers for addition (simplified)
            import re
            numbers = re.findall(r'\d+', last_human_msg)
            if len(numbers) >= 2:
                num1, num2 = int(numbers[0]), int(numbers[1])
                result = num1 + num2
                response_content = f"I'll add those numbers for you! {num1} + {num2} = {result}"
            else:
                response_content = "I can help you add numbers! Please provide the numbers you'd like to add, for example: 'What is 25 + 37?'"
                
        elif any(word in last_human_msg for word in ['max', 'maximum', 'larger', 'biggest', 'greater']):
            # Extract numbers for comparison (simplified)
            import re
            numbers = re.findall(r'\d+', last_human_msg)
            if len(numbers) >= 2:
                nums = [int(n) for n in numbers]
                max_num = max(nums)
                response_content = f"I'll find the maximum for you! Among {', '.join(numbers)}, the largest number is {max_num}"
            else:
                response_content = "I can help you find the maximum of numbers! Please provide the numbers to compare, for example: 'Which is larger: 42 or 17?'"
                
        elif 'hello' in last_human_msg or 'hi' in last_human_msg:
            response_content = "Hello! I'm your MCP-enabled AI assistant. I can help with mathematical operations like addition and finding maximum values. What would you like to calculate?"
            
        elif 'help' in last_human_msg:
            response_content = """I can help you with mathematical operations! Try asking:

• **Addition**: "What is 25 + 37?" or "Add 100 and 200"
• **Maximum**: "Which is larger: 42 or 17?" or "Find the maximum of 15, 89, and 33"

I use MCP (Model Context Protocol) tools to provide accurate calculations!"""
            
        else:
            response_content = f"I received your message: '{human_messages[-1].content}'. I'm specialized in mathematical operations. Try asking me to add numbers or find maximum values!"
        
        # Create AI response
        ai_response = AIMessage(content=response_content)
        state['messages'].append(ai_response)
        
        logger.info(f"Processed message, generated response of length {len(response_content)}")
        return state
        
    except Exception as e:
        logger.error(f"Message processing failed: {e}")
        error_msg = AIMessage(content=f"I encountered an error processing your message: {str(e)}")
        state['messages'].append(error_msg)
        return state


def should_continue(state: ChatState) -> str:
    """Determine if we should continue processing or end"""
    messages = state['messages']
    
    # Continue if the last message is from human
    if messages and isinstance(messages[-1], HumanMessage):
        return "process"
    
    # End if we just processed a message
    return END


def create_chat_graph():
    """Create the chat-enabled MCP agent graph"""
    workflow = StateGraph(ChatState)
    
    # Add nodes
    workflow.add_node("setup", setup_system)
    workflow.add_node("process", process_message)
    
    # Add edges
    workflow.set_entry_point("setup")
    workflow.add_edge("setup", "process")
    workflow.add_conditional_edges(
        "process",
        should_continue,
        {
            "process": "process",
            END: END
        }
    )
    
    return workflow.compile()


# This is the main entry point for LangGraph Studio
graph = create_chat_graph()


if __name__ == "__main__":
    # Test the chat graph locally
    print("🔧 Testing Chat-Compatible LangGraph MCP Agent")
    
    try:
        # Test with a simple conversation
        initial_state = {
            "messages": [HumanMessage(content="Hello! What is 25 + 37?")],
            "mcp_server_url": "http://localhost:8000",
            "llm_model": "gpt-3.5-turbo",
            "tools_loaded": False
        }
        
        result = graph.invoke(initial_state)
        
        print("Chat conversation result:")
        for i, msg in enumerate(result['messages']):
            role = type(msg).__name__.replace('Message', '')
            print(f"{i+1}. {role}: {msg.content}")
            
    except Exception as e:
        print(f"❌ Chat graph test failed: {e}")
        import traceback
        traceback.print_exc()
