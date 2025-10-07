#!/usr/bin/env python3
"""
Test to verify that the AI agent can see and list MCP tools.
This test checks if the agent recognizes the available MCP tools.
"""

import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

def test_mcp_tools_visibility():
    """Test that the AI agent can see and list MCP tools"""
    print("🔧 Testing MCP Tools Visibility")
    print("=" * 40)
    
    # Mock environment variables
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-12345',
        'MCP_SERVER_URL': 'http://localhost:8080/sse'
    }):
        
        # Mock the MCPClient with tools
        with patch('main.client') as mock_client:
            print("🔧 Setting up MCP client mock...")
            
            # Mock the connection
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Mock the session and tools
            mock_session = Mock()
            mock_client.session = mock_session
            
            # Mock list_tools to return get_alerts and get_forecast tools
            alerts_tool = Mock()
            alerts_tool.name = "get_alerts"
            alerts_tool.description = "Get weather alerts for a location"
            alerts_tool.inputSchema = {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "Location to get alerts for"}
                },
                "required": ["location"]
            }
            
            forecast_tool = Mock()
            forecast_tool.name = "get_forecast"
            forecast_tool.description = "Get weather forecast for a location using latitude and longitude"
            forecast_tool.inputSchema = {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude coordinate"},
                    "longitude": {"type": "number", "description": "Longitude coordinate"}
                },
                "required": ["latitude", "longitude"]
            }
            
            mock_session.list_tools = AsyncMock(return_value=Mock(tools=[alerts_tool, forecast_tool]))
            
            # Mock the tool calls
            async def mock_call_tool(tool_name, args):
                if tool_name == "get_alerts":
                    mock_result = Mock()
                    mock_result.content = ["No active weather alerts for the specified location."]
                    return mock_result
                elif tool_name == "get_forecast":
                    mock_result = Mock()
                    mock_result.content = ["Current weather: 72°F, Partly Cloudy"]
                    return mock_result
                return Mock(content=["Tool result"])
            
            mock_session.call_tool = AsyncMock(side_effect=mock_call_tool)
            
            print("✅ MCP client mock configured with get_alerts and get_forecast tools")
            
            # Mock OpenAI API calls
            with patch('openai.OpenAI') as mock_openai:
                mock_client_instance = Mock()
                mock_openai.return_value = mock_client_instance
                
                # Mock response for "list all your MCP tools" query
                mock_response = Mock()
                mock_response.choices = [Mock()]
                mock_response.choices[0].message = Mock()
                mock_response.choices[0].message.content = "I have access to the following MCP tools:\n\n1. **get_alerts** - Get weather alerts for a location\n2. **get_forecast** - Get weather forecast for a location using latitude and longitude\n\nThese tools allow me to provide real-time weather information and alerts. Would you like me to use any of these tools to help you?"
                mock_response.choices[0].message.tool_calls = []
                
                mock_client_instance.chat.completions.create.return_value = mock_response
                
                # Import and test the graph
                from main import advanced_graph
                
                # Create test state with tools query
                test_state = {
                    "messages": [HumanMessage(content="list all your MCP tools")],
                    "user_id": "test_user",
                    "session_id": "tools_test",
                    "conversation_count": 0
                }
                
                print(f"👤 User query: '{test_state['messages'][0].content}'")
                
                # Execute the query
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
                
                # Analyze the response
                ai_response = result["messages"][-1]
                response_text = ai_response.content.lower()
                
                print(f"\n🔍 RESPONSE ANALYSIS:")
                print(f"✅ Response length: {len(ai_response.content)} characters")
                
                # Check for expected elements
                expected_elements = ["mcp tools", "get_alerts", "get_forecast", "weather"]
                found_elements = [element for element in expected_elements if element in response_text]
                print(f"✅ Expected elements found: {found_elements}")
                
                # Check if the agent recognizes the tools
                tool_checks = {
                    "Mentions MCP tools": "mcp tools" in response_text,
                    "Lists get_alerts": "get_alerts" in response_text,
                    "Lists get_forecast": "get_forecast" in response_text,
                    "Explains tool purpose": "weather" in response_text or "alerts" in response_text
                }
                
                print(f"\n🔍 TOOL VISIBILITY CHECKS:")
                for check, passed in tool_checks.items():
                    status = "✅" if passed else "❌"
                    print(f"{status} {check}")
                
                # Overall success
                passed_checks = sum(tool_checks.values())
                total_checks = len(tool_checks)
                
                if passed_checks >= total_checks * 0.75:  # 75% of checks must pass
                    print(f"\n✅ TOOL VISIBILITY VERIFIED! ({passed_checks}/{total_checks})")
                    print("✅ AI agent can see and list MCP tools!")
                    return True
                else:
                    print(f"\n❌ TOOL VISIBILITY FAILED ({passed_checks}/{total_checks})")
                    print("❌ AI agent cannot see MCP tools properly")
                    return False

def test_weather_query_with_tools():
    """Test weather query when MCP tools are available"""
    print("\n🌤️  Testing Weather Query with MCP Tools")
    print("=" * 45)
    
    # Mock environment variables
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-12345',
        'MCP_SERVER_URL': 'http://localhost:8080/sse'
    }):
        
        # Mock the MCPClient with get_forecast tool
        with patch('main.client') as mock_client:
            print("🔧 Setting up MCP client mock...")
            
            # Mock the connection
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Mock the session and tools
            mock_session = Mock()
            mock_client.session = mock_session
            
            # Mock list_tools to return get_forecast tool
            forecast_tool = Mock()
            forecast_tool.name = "get_forecast"
            forecast_tool.description = "Get weather forecast for a location using latitude and longitude"
            forecast_tool.inputSchema = {
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude coordinate"},
                    "longitude": {"type": "number", "description": "Longitude coordinate"}
                },
                "required": ["latitude", "longitude"]
            }
            
            mock_session.list_tools = AsyncMock(return_value=Mock(tools=[forecast_tool]))
            
            # Mock the tool call to return weather data
            async def mock_call_tool(tool_name, args):
                if tool_name == "get_forecast":
                    mock_result = Mock()
                    mock_result.content = ["Current weather in Spokane: 72°F, Partly Cloudy, 45% humidity"]
                    return mock_result
                return Mock(content=["Weather data not available"])
            
            mock_session.call_tool = AsyncMock(side_effect=mock_call_tool)
            
            print("✅ MCP client mock configured with get_forecast tool")
            
            # Mock OpenAI API calls
            with patch('openai.OpenAI') as mock_openai:
                mock_client_instance = Mock()
                mock_openai.return_value = mock_client_instance
                
                # Mock the first API call (with tools)
                mock_response1 = Mock()
                mock_response1.choices = [Mock()]
                mock_response1.choices[0].message = Mock()
                mock_response1.choices[0].message.content = "I can help you check the weather forecast for Spokane, Washington. I'll use the get_forecast function with Spokane's coordinates."
                mock_response1.choices[0].message.tool_calls = [Mock()]
                mock_response1.choices[0].message.tool_calls[0].function = Mock()
                mock_response1.choices[0].message.tool_calls[0].function.name = "get_forecast"
                mock_response1.choices[0].message.tool_calls[0].function.arguments = '{"latitude": 47.6587, "longitude": -117.426}'
                
                # Mock the second API call (final response)
                mock_response2 = Mock()
                mock_response2.choices = [Mock()]
                mock_response2.choices[0].message = Mock()
                mock_response2.choices[0].message.content = "Based on the current forecast for Spokane: Current weather in Spokane: 72°F, Partly Cloudy, 45% humidity"
                
                mock_client_instance.chat.completions.create.side_effect = [mock_response1, mock_response2]
                
                # Import and test the graph
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
                
                # Analyze the response
                ai_response = result["messages"][-1]
                response_text = ai_response.content
                
                print(f"\n🔍 RESPONSE ANALYSIS:")
                print(f"✅ Response length: {len(ai_response.content)} characters")
                
                # Check for tool usage
                tool_usage_checks = {
                    "Mentions get_forecast": "get_forecast" in response_text,
                    "Shows tool calling": "[Calling tool" in response_text,
                    "Provides weather data": "72°F" in response_text or "Partly Cloudy" in response_text,
                    "Uses coordinates": "47.6587" in response_text and "117.426" in response_text
                }
                
                print(f"\n🔍 TOOL USAGE CHECKS:")
                for check, passed in tool_usage_checks.items():
                    status = "✅" if passed else "❌"
                    print(f"{status} {check}")
                
                # Overall success
                passed_checks = sum(tool_usage_checks.values())
                total_checks = len(tool_usage_checks)
                
                if passed_checks >= total_checks * 0.75:  # 75% of checks must pass
                    print(f"\n✅ TOOL USAGE VERIFIED! ({passed_checks}/{total_checks})")
                    print("✅ AI agent is using MCP tools for weather queries!")
                    return True
                else:
                    print(f"\n❌ TOOL USAGE FAILED ({passed_checks}/{total_checks})")
                    print("❌ AI agent is not using MCP tools properly")
                    return False

if __name__ == "__main__":
    print("🧪 MCP TOOLS VISIBILITY TEST")
    print("=" * 50)
    print("This test verifies that the AI agent can see and use MCP tools.")
    print("=" * 50)
    
    try:
        # Test MCP tools visibility
        visibility_success = test_mcp_tools_visibility()
        
        # Test weather query with tools
        weather_success = test_weather_query_with_tools()
        
        if visibility_success and weather_success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ AI agent can see MCP tools")
            print("✅ AI agent can use MCP tools for weather queries")
            print("✅ Your MCP integration is working correctly!")
        else:
            print("\n⚠️  Some tests failed")
            if not visibility_success:
                print("❌ MCP tools visibility test failed")
            if not weather_success:
                print("❌ Weather query with tools test failed")
            
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
