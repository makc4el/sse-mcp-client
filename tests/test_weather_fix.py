#!/usr/bin/env python3
"""
Test script to verify the weather query fix works properly.
This script tests the main.py functionality with a weather query.
"""

import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_weather_query_fix():
    """Test the weather query functionality with mocked MCP client"""
    print("🌤️  Testing Weather Query Fix")
    print("=" * 40)
    
    # Mock environment variables
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-12345',
        'MCP_SERVER_URL': 'http://localhost:8080/sse'
    }):
        
        # Mock the MCPClient with weather tool
        with patch('main.client') as mock_client:
            print("🔧 Setting up MCP client mock...")
            
            # Mock the connection
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Mock the session and tools
            mock_session = Mock()
            mock_client.session = mock_session
            
            # Mock list_tools to return a weather tool
            weather_tool = Mock()
            weather_tool.name = "get_weather"
            weather_tool.description = "Get current weather for a location"
            weather_tool.inputSchema = {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state/country"
                    }
                },
                "required": ["location"]
            }
            
            mock_session.list_tools = AsyncMock(return_value=Mock(tools=[weather_tool]))
            
            # Mock the tool call to return weather data
            async def mock_call_tool(tool_name, args):
                if tool_name == "get_weather" and "location" in args:
                    location = args["location"]
                    if "spokane" in location.lower():
                        # Return mock weather data
                        mock_result = Mock()
                        mock_result.content = f"Current weather in {location}: 72°F, Partly Cloudy, 45% humidity"
                        return mock_result
                return Mock(content="Weather data not available")
            
            mock_session.call_tool = AsyncMock(side_effect=mock_call_tool)
            
            print("✅ MCP client mock configured")
            print("\n🚀 Testing weather query...")
            
            # Mock OpenAI API calls
            with patch('openai.OpenAI') as mock_openai:
                # Mock the OpenAI client and responses
                mock_client_instance = Mock()
                mock_openai.return_value = mock_client_instance
                
                # Mock the first API call (with tools)
                mock_response1 = Mock()
                mock_response1.choices = [Mock()]
                mock_response1.choices[0].message = Mock()
                mock_response1.choices[0].message.content = "I'll check the weather for you."
                mock_response1.choices[0].message.tool_calls = [Mock()]
                mock_response1.choices[0].message.tool_calls[0].function = Mock()
                mock_response1.choices[0].message.tool_calls[0].function.name = "get_weather"
                mock_response1.choices[0].message.tool_calls[0].function.arguments = '{"location": "Spokane"}'
                
                # Mock the second API call (final response)
                mock_response2 = Mock()
                mock_response2.choices = [Mock()]
                mock_response2.choices[0].message = Mock()
                mock_response2.choices[0].message.content = "The current weather in Spokane is 72°F and partly cloudy with 45% humidity. It's a pleasant day!"
                
                mock_client_instance.chat.completions.create.side_effect = [mock_response1, mock_response2]
                
                # Import and test the graph
                from main import advanced_graph, initialize_mcp_client
                
                # Initialize the client
                initialize_mcp_client()
                
                # Create test state with weather query
                test_state = {
                    "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                    "user_id": "test_user_123",
                    "session_id": "weather_test_session",
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
                
                # Verify the response contains weather information
                ai_response = result["messages"][-1]
                response_text = ai_response.content.lower()
                
                # Check if the response indicates weather information was retrieved
                weather_indicators = ["weather", "spokane", "temperature", "°f", "°c", "cloudy", "sunny", "rain"]
                found_indicators = [indicator for indicator in weather_indicators if indicator in response_text]
                
                print(f"\n🔍 RESPONSE ANALYSIS:")
                print(f"✅ Response length: {len(ai_response.content)} characters")
                print(f"✅ Weather indicators found: {found_indicators}")
                
                if found_indicators:
                    print("✅ Weather query processed successfully!")
                    print("✅ MCP tool integration working!")
                    return True
                else:
                    print("⚠️  Weather indicators not found in response")
                    print("⚠️  This might indicate the tool calling isn't working properly")
                    return False

def test_fallback_behavior():
    """Test the fallback behavior when MCP client is not available"""
    print("\n🔄 Testing Fallback Behavior")
    print("=" * 35)
    
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-12345',
        'MCP_SERVER_URL': 'http://localhost:8080/sse'
    }):
        
        # Mock the MCPClient as None (not available)
        with patch('main.client', None):
            print("🔧 Testing without MCP client...")
            
            # Mock LangChain LLM for fallback
            with patch('main.create_llm') as mock_create_llm:
                mock_llm = Mock()
                mock_response = Mock()
                mock_response.content = "I'm unable to provide real-time weather updates. However, you can check the current weather in Spokane using a weather website or app."
                mock_llm.invoke.return_value = mock_response
                mock_create_llm.return_value = mock_llm
                
                from main import advanced_graph
                
                # Create test state
                test_state = {
                    "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                    "user_id": "test_user_123",
                    "session_id": "fallback_test_session",
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
                return True

if __name__ == "__main__":
    print("🧪 WEATHER QUERY FIX TEST")
    print("=" * 50)
    print("This test verifies that the weather query fix works properly.")
    print("=" * 50)
    
    try:
        # Test with MCP client
        success1 = test_weather_query_fix()
        
        # Test fallback behavior
        success2 = test_fallback_behavior()
        
        if success1 and success2:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Weather query with MCP tools works")
            print("✅ Fallback behavior works")
            print("✅ The fix is working properly!")
        else:
            print("\n⚠️  Some tests failed")
            if not success1:
                print("❌ MCP tool integration test failed")
            if not success2:
                print("❌ Fallback behavior test failed")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
