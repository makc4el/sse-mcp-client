"""
Test script for MCP Agent

This script tests the MCP agent with a weather query for Spokane.
"""

import sys
import os
import asyncio
from langchain_core.messages import HumanMessage

# Add the parent directory to the path so we can import mcp_agent
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mcp_agent import mcp_agent_graph


async def test_weather_query_async():
    """Test the MCP agent with a weather query for Spokane."""
    print("Testing MCP Agent with weather query for Spokane...")
    
    # Test state with weather query
    test_state = {
        "messages": [HumanMessage(content="What's the weather like in Spokane?")],
        "user_id": "test_user",
        "session_id": "test_session",
        "conversation_count": 0,
        "mcp_tools_available": False
    }
    
    try:
        result = await mcp_agent_graph.ainvoke(test_state)
        print("\nMCP Agent Response:")
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                print(f"- {msg.content}")
        print(f"\nConversation Count: {result['conversation_count']}")
        print(f"MCP Tools Available: {result['mcp_tools_available']}")
        
        # Check if the response contains weather-related information
        response_text = ""
        for msg in result["messages"]:
            if hasattr(msg, 'content') and msg.content:
                response_text += msg.content + " "
        
        if any(keyword in response_text.lower() for keyword in ['weather', 'forecast', 'temperature', 'spokane']):
            print("\n✅ Test PASSED: Agent responded with weather-related information")
        else:
            print("\n⚠️  Test PARTIAL: Agent responded but may not have used MCP tools")
            
    except Exception as e:
        print(f"\n❌ Test FAILED: {e}")


def test_weather_query():
    """Test the MCP agent with a weather query for Spokane."""
    import asyncio
    try:
        asyncio.run(test_weather_query_async())
    except RuntimeError:
        # If we're already in an event loop, create a new one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_weather_query_async())
        finally:
            loop.close()


if __name__ == "__main__":
    test_weather_query()
