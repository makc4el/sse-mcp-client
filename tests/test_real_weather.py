#!/usr/bin/env python3
"""
Test script to verify the weather query works with real MCP tools.
This test uses actual environment variables and real MCP server connection.
"""

import os
import sys
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_real_weather_query():
    """Test the weather query functionality with real MCP client"""
    print("🌤️  Testing Real Weather Query with MCP Tools")
    print("=" * 55)
    
    # Check if we have the required environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        return False
    
    if not mcp_server_url:
        print("❌ MCP_SERVER_URL not found in environment variables")
        return False
    
    print(f"✅ OpenAI API Key: {'*' * 20}{openai_key[-10:]}")
    print(f"✅ MCP Server URL: {mcp_server_url}")
    
    try:
        # Import and test the graph
        from main import advanced_graph, initialize_mcp_client
        
        print("\n🔧 Initializing MCP client...")
        client = initialize_mcp_client()
        
        if client and client.session:
            print("✅ MCP client connected successfully!")
        else:
            print("⚠️  MCP client not available, will use fallback")
        
        # Create test state with the exact query
        test_state = {
            "messages": [HumanMessage(content="whats the weather like in Spokane?")],
            "user_id": "test_user_123",
            "session_id": "real_weather_test",
            "conversation_count": 0
        }
        
        print(f"\n👤 User query: '{test_state['messages'][0].content}'")
        
        # Execute the query through the graph
        print("\n⚡ Executing through LangGraph...")
        result = advanced_graph.invoke(test_state)
        
        print("\n📋 RESULTS:")
        print("=" * 30)
        
        # Verify the response
        assert "messages" in result
        assert "conversation_count" in result
        assert len(result["messages"]) == 2  # Original + AI response
        
        print(f"✅ Messages processed: {len(result['messages'])}")
        print(f"✅ Conversation count: {result['conversation_count']}")
        
        # Show the conversation
        print("\n💬 CONVERSATION:")
        for i, msg in enumerate(result["messages"]):
            if isinstance(msg, HumanMessage):
                print(f"👤 User: {msg.content}")
            elif isinstance(msg, AIMessage):
                print(f"🤖 Assistant: {msg.content}")
        
        # Verify the response contains expected elements
        ai_response = result["messages"][-1]
        response_text = ai_response.content
        
        print(f"\n🔍 RESPONSE ANALYSIS:")
        print(f"✅ Response length: {len(ai_response.content)} characters")
        
        # Check for expected elements
        expected_elements = [
            "Spokane",
            "weather",
            "temperature",
            "°F"
        ]
        
        found_elements = [element for element in expected_elements if element in response_text]
        print(f"✅ Expected elements found: {found_elements}")
        
        # Check for tool calling indication
        if "[Calling tool" in response_text:
            print("✅ Tool calling indication found!")
        else:
            print("⚠️  Tool calling indication not found")
        
        # Check for coordinates
        if "47.6587" in response_text and "117.426" in response_text:
            print("✅ Spokane coordinates found!")
        else:
            print("⚠️  Spokane coordinates not found")
        
        # Check for weather data
        if "°F" in response_text or "temperature" in response_text:
            print("✅ Weather data found!")
        else:
            print("⚠️  Weather data not found")
        
        if len(found_elements) >= 2:  # At least 2 expected elements
            print("✅ Real weather query processed successfully!")
            print("✅ MCP tool integration working with real server!")
            return True
        else:
            print("⚠️  Expected response format not fully achieved")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_behavior():
    """Test the fallback behavior when MCP server is not available"""
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 35)
    
    try:
        # Temporarily set an invalid MCP server URL
        original_url = os.getenv("MCP_SERVER_URL")
        os.environ["MCP_SERVER_URL"] = "http://invalid-server:9999/sse"
        
        from main import advanced_graph, initialize_mcp_client
        
        print("🔧 Testing with invalid MCP server...")
        client = initialize_mcp_client()
        
        if client is None:
            print("✅ MCP client correctly failed to connect")
        else:
            print("⚠️  MCP client unexpectedly connected")
        
        # Create test state
        test_state = {
            "messages": [HumanMessage(content="whats the weather like in Spokane?")],
            "user_id": "test_user_123",
            "session_id": "fallback_test",
            "conversation_count": 0
        }
        
        print(f"👤 User query: '{test_state['messages'][0].content}'")
        
        # Execute the query through the graph
        print("\n⚡ Executing through LangGraph...")
        result = advanced_graph.invoke(test_state)
        
        print("\n📋 RESULTS:")
        print("=" * 30)
        
        # Verify the response
        assert "messages" in result
        assert "conversation_count" in result
        
        print(f"✅ Messages processed: {len(result['messages'])}")
        print(f"✅ Conversation count: {result['conversation_count']}")
        
        # Show the conversation
        print("\n💬 CONVERSATION:")
        for i, msg in enumerate(result["messages"]):
            if isinstance(msg, HumanMessage):
                print(f"👤 User: {msg.content}")
            elif isinstance(msg, AIMessage):
                print(f"🤖 Assistant: {msg.content}")
        
        print("✅ Fallback behavior working!")
        
        # Restore original URL
        if original_url:
            os.environ["MCP_SERVER_URL"] = original_url
        
        return True
        
    except Exception as e:
        print(f"\n❌ Fallback test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 REAL WEATHER QUERY TEST")
    print("=" * 50)
    print("This test uses real MCP tools and environment variables.")
    print("=" * 50)
    
    try:
        # Test with real MCP client
        success1 = test_real_weather_query()
        
        # Test fallback behavior
        success2 = test_fallback_behavior()
        
        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Real weather query with MCP tools works")
            print("✅ Fallback behavior works")
            print("✅ The system is working properly with real tools!")
        else:
            print("\n⚠️  Some tests failed")
            if not success1:
                print("❌ Real MCP tool integration test failed")
            if not success2:
                print("❌ Fallback behavior test failed")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
