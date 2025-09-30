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

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


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
    Advanced chat node with session management and enhanced context.
    
    Args:
        state: Enhanced chat state with user and session information
        config: Runtime configuration from LangGraph platform
        
    Returns:
        Dictionary containing the AI response and updated state
    """
    try:
        llm = create_llm()
        
        # Add conversation context if this is a continuing conversation
        messages = state["messages"]
        conversation_count = state.get("conversation_count", 0)
        
        if conversation_count == 0:
            # First message in session
            system_context = AIMessage(
                content="Hello! I'm your advanced AI assistant. I can help you with questions, analysis, and conversation. How can I help you today?"
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