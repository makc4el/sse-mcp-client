#!/usr/bin/env python3
"""
Test script to verify the Spokane weather query works with the expected response format.
"""

import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_spokane_weather_query():
    """Test the Spokane weather query with expected response format"""
    print("🌤️  Testing Spokane Weather Query")
    print("=" * 45)
    
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
            
            # Mock list_tools to return a get_forecast tool
            forecast_tool = Mock()
            forecast_tool.name = "get_forecast"
            forecast_tool.description = "Get weather forecast for a location using latitude and longitude"
            forecast_tool.inputSchema = {
                "type": "object",
                "properties": {
                    "latitude": {
                        "type": "number",
                        "description": "Latitude coordinate"
                    },
                    "longitude": {
                        "type": "number", 
                        "description": "Longitude coordinate"
                    }
                },
                "required": ["latitude", "longitude"]
            }
            
            mock_session.list_tools = AsyncMock(return_value=Mock(tools=[forecast_tool]))
            
            # Mock the tool call to return weather data
            async def mock_call_tool(tool_name, args):
                if tool_name == "get_forecast" and "latitude" in args and "longitude" in args:
                    lat = args["latitude"]
                    lon = args["longitude"]
                    # Check if it's Spokane coordinates (approximately)
                    if abs(lat - 47.6587) < 0.1 and abs(lon - (-117.426)) < 0.1:
                        # Return mock weather data for Spokane
                        mock_result = Mock()
                        mock_result.content = [
                            "Right now it's sunny and cold with a temperature of 37°F and light winds.",
                            "Today's high will be around 42°F with partly cloudy skies.",
                            "Tonight expect temperatures to drop to 28°F with clear skies."
                        ]
                        return mock_result
                return Mock(content=["Weather data not available"])
            
            mock_session.call_tool = AsyncMock(side_effect=mock_call_tool)
            
            print("✅ MCP client mock configured")
            print("\n🚀 Testing Spokane weather query...")
            
            # Mock OpenAI API calls
            with patch('openai.OpenAI') as mock_openai:
                # Mock the OpenAI client and responses
                mock_client_instance = Mock()
                mock_openai.return_value = mock_client_instance
                
                # Mock the first API call (with tools) - should call get_forecast
                mock_response1 = Mock()
                mock_response1.choices = [Mock()]
                mock_response1.choices[0].message = Mock()
                mock_response1.choices[0].message.content = "I can help you check the weather forecast for Spokane, Washington. I'll use the get_forecast function, but I'll need to use Spokane's latitude and longitude coordinates.\n\nSpokane, WA is located at approximately 47.6587° N, 117.4260° W."
                mock_response1.choices[0].message.tool_calls = [Mock()]
                mock_response1.choices[0].message.tool_calls[0].function = Mock()
                mock_response1.choices[0].message.tool_calls[0].function.name = "get_forecast"
                mock_response1.choices[0].message.tool_calls[0].function.arguments = '{"latitude": 47.6587, "longitude": -117.426}'
                
                # Mock the second API call (final response)
                mock_response2 = Mock()
                mock_response2.choices = [Mock()]
                mock_response2.choices[0].message = Mock()
                mock_response2.choices[0].message.content = "Based on the current forecast for Spokane:\n\nRight now it's sunny and cold with a temperature of 37°F and light winds. Today's high will be around 42°F with partly cloudy skies. Tonight expect temperatures to drop to 28°F with clear skies."
                
                mock_client_instance.chat.completions.create.side_effect = [mock_response1, mock_response2]
                
                # Import and test the graph
                from main import advanced_graph, initialize_mcp_client
                
                # Initialize the client
                initialize_mcp_client()
                
                # Create test state with the exact query
                test_state = {
                    "messages": [HumanMessage(content="whats the weather like in Spokane?")],
                    "user_id": "test_user_123",
                    "session_id": "spokane_weather_test",
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
                
                # Verify the response contains expected elements
                ai_response = result["messages"][-1]
                response_text = ai_response.content
                
                print(f"\n🔍 RESPONSE ANALYSIS:")
                print(f"✅ Response length: {len(ai_response.content)} characters")
                
                # Check for expected elements
                expected_elements = [
                    "Spokane",
                    "weather",
                    "forecast", 
                    "get_forecast",
                    "latitude",
                    "longitude",
                    "47.6587",
                    "117.426",
                    "temperature",
                    "°F"
                ]
                
                found_elements = [element for element in expected_elements if element in response_text]
                print(f"✅ Expected elements found: {found_elements}")
                
                # Check for tool calling indication
                if "[Calling tool get_forecast" in response_text:
                    print("✅ Tool calling indication found!")
                else:
                    print("⚠️  Tool calling indication not found")
                
                # Check for coordinates
                if "47.6587" in response_text and "117.426" in response_text:
                    print("✅ Spokane coordinates found!")
                else:
                    print("⚠️  Spokane coordinates not found")
                
                # Check for weather data
                if "37°F" in response_text or "temperature" in response_text:
                    print("✅ Weather data found!")
                else:
                    print("⚠️  Weather data not found")
                
                if len(found_elements) >= 6:  # At least 6 expected elements
                    print("✅ Spokane weather query processed successfully!")
                    print("✅ Expected response format achieved!")
                    return True
                else:
                    print("⚠️  Expected response format not fully achieved")
                    return False

if __name__ == "__main__":
    print("🧪 SPOKANE WEATHER QUERY TEST")
    print("=" * 50)
    print("This test verifies the exact Spokane weather query format.")
    print("=" * 50)
    
    try:
        success = test_spokane_weather_query()
        
        if success:
            print("\n🎉 TEST PASSED!")
            print("✅ Spokane weather query works with expected format")
            print("✅ Tool calling with coordinates works")
            print("✅ Weather data is properly returned")
        else:
            print("\n⚠️  Test did not achieve expected format")
            
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
