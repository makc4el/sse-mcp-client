#!/usr/bin/env python3
"""
LangGraph-compatible MCP Agent (Fixed Version)

This module provides a simplified LangGraph-compatible graph definition 
that should work properly with LangGraph Studio.
"""

import logging
from typing import TypedDict, Annotated, Optional, Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AgentState(TypedDict):
    """State for the MCP agent graph"""
    messages: Annotated[list[BaseMessage], add_messages]
    config: Optional[Dict[str, Any]]


def setup_llm(state: AgentState) -> AgentState:
    """Set up the language model"""
    try:
        config = state.get('config', {})
        model = config.get('llm_model', 'gpt-3.5-turbo')
        
        # For now, just add a setup message
        setup_msg = AIMessage(content=f"Setting up agent with model: {model}")
        state['messages'].append(setup_msg)
        
        logger.info(f"LLM setup complete with model: {model}")
        return state
        
    except Exception as e:
        logger.error(f"LLM setup failed: {e}")
        error_msg = AIMessage(content=f"Setup failed: {str(e)}")
        state['messages'].append(error_msg)
        return state


def call_model(state: AgentState) -> AgentState:
    """Call the language model to respond"""
    try:
        messages = state['messages']
        config = state.get('config', {})
        model = config.get('llm_model', 'gpt-3.5-turbo')
        
        # Get the latest human message
        human_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        if not human_messages:
            response = AIMessage(content="Hello! I'm ready to help with mathematical operations.")
        else:
            last_question = human_messages[-1].content
            
            # Simple response for now (without actual LLM call to avoid API key issues in Studio)
            if any(word in last_question.lower() for word in ['add', '+', 'plus', 'sum']):
                response = AIMessage(content="I can help you add numbers! Please provide the numbers you'd like to add.")
            elif any(word in last_question.lower() for word in ['max', 'maximum', 'larger', 'biggest']):
                response = AIMessage(content="I can help you find the maximum of numbers! Please provide the numbers to compare.")
            else:
                response = AIMessage(content=f"I received your message: '{last_question}'. I'm set up to help with mathematical operations like addition and finding maximums.")
        
        state['messages'].append(response)
        return state
        
    except Exception as e:
        logger.error(f"Model call failed: {e}")
        error_msg = AIMessage(content=f"I encountered an error: {str(e)}")
        state['messages'].append(error_msg)
        return state


def should_continue(state: AgentState) -> str:
    """Determine if we should continue or end"""
    messages = state['messages']
    
    # Simple logic: end after model responds
    if len(messages) >= 3:  # setup + human + ai response
        return END
    
    return "model"


def create_mcp_graph():
    """Create the MCP agent graph"""
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("setup", setup_llm)
    workflow.add_node("model", call_model)
    
    # Add edges
    workflow.set_entry_point("setup")
    workflow.add_edge("setup", "model")
    workflow.add_conditional_edges(
        "model",
        should_continue,
        {
            "model": "model",
            END: END
        }
    )
    
    return workflow.compile()


# This is the main entry point for LangGraph
graph = create_mcp_graph()


if __name__ == "__main__":
    # Test the graph locally
    print("🔧 Testing Simplified LangGraph MCP Agent")
    
    try:
        # Test with a simple input
        initial_state = {
            "messages": [HumanMessage(content="What is 25 + 37?")],
            "config": {"llm_model": "gpt-3.5-turbo"}
        }
        
        result = graph.invoke(initial_state)
        
        print("Graph execution result:")
        for msg in result['messages']:
            print(f"- {type(msg).__name__}: {msg.content}")
            
    except Exception as e:
        print(f"❌ Graph test failed: {e}")
        import traceback
        traceback.print_exc()
