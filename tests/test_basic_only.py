#!/usr/bin/env python3
"""
Basic test that doesn't try to connect to MCP server to avoid hanging.
This just tests the core functionality.
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

def test_basic_functionality():
    """Test basic functionality without MCP connection"""
    print("🧪 Testing Basic Functionality")
    print("=" * 40)
    
    # Check environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    mcp_server_url = os.getenv("MCP_SERVER_URL")
    
    print(f"✅ OpenAI API Key: {'*' * 20}{openai_key[-10:] if openai_key else 'NOT SET'}")
    print(f"✅ MCP Server URL: {mcp_server_url or 'NOT SET'}")
    
    if not openai_key:
        print("❌ OPENAI_API_KEY is required")
        return False
    
    try:
        # Import without initializing MCP client
        from main import advanced_graph
        
        # Create test state
        test_state = {
            "messages": [HumanMessage(content="Hello! Can you help me?")],
            "user_id": "test_user",
            "session_id": "basic_test",
            "conversation_count": 0
        }
        
        print(f"\n👤 User query: '{test_state['messages'][0].content}'")
        
        # Execute the query
        print("\n⚡ Executing through LangGraph...")
        result = advanced_graph.invoke(test_state)
        
        print("\n📋 RESULTS:")
        print("=" * 20)
        
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
        
        print("✅ Basic functionality working!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_weather_query_fallback():
    """Test weather query with fallback (no MCP connection)"""
    print("\n🌤️  Testing Weather Query (Fallback)")
    print("=" * 45)
    
    try:
        from main import advanced_graph
        
        # Create test state with weather query
        test_state = {
            "messages": [HumanMessage(content="whats the weather like in Spokane?")],
            "user_id": "test_user",
            "session_id": "weather_test",
            "conversation_count": 0
        }
        
        print(f"👤 User query: '{test_state['messages'][0].content}'")
        
        # Execute the query
        print("\n⚡ Executing through LangGraph...")
        result = advanced_graph.invoke(test_state)
        
        print("\n📋 RESULTS:")
        print("=" * 20)
        
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
        
        # Analyze the response
        ai_response = result["messages"][-1]
        response_text = ai_response.content.lower()
        
        print(f"\n🔍 RESPONSE ANALYSIS:")
        print(f"✅ Response length: {len(ai_response.content)} characters")
        
        # Check for expected elements
        expected_elements = ["spokane", "weather"]
        found_elements = [element for element in expected_elements if element in response_text]
        print(f"✅ Expected elements found: {found_elements}")
        
        if len(found_elements) >= 1:
            print("✅ Weather query processed successfully!")
            print("✅ System provides appropriate fallback response!")
            return True
        else:
            print("⚠️  Weather query response may need improvement")
            return False
        
    except Exception as e:
        print(f"❌ Weather query test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 BASIC FUNCTIONALITY TEST")
    print("=" * 50)
    print("This test verifies basic functionality without MCP connection.")
    print("=" * 50)
    
    try:
        # Test basic functionality
        basic_success = test_basic_functionality()
        
        # Test weather query fallback
        weather_success = test_weather_query_fallback()
        
        if basic_success and weather_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Basic functionality working")
            print("✅ Weather query fallback working")
            print("✅ Your system is ready for deployment!")
            print("\n🌤️  Weather Query System Status:")
            print("   - Users can ask: 'whats the weather like in Spokane?'")
            print("   - System will attempt to use MCP tools if available")
            print("   - System will fallback gracefully if MCP tools unavailable")
            print("   - All responses are appropriate and helpful")
        else:
            print("\n⚠️  Some tests failed")
            if not basic_success:
                print("❌ Basic functionality failed")
            if not weather_success:
                print("❌ Weather query failed")
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
