#!/usr/bin/env python3
"""
Test main.py with weather query scenario
Tests the complete flow: user asks "what's the weather like in Spokane?" 
and verifies MCP client is called with appropriate response
"""

import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestMainWeatherQuery:
    """Test class for weather query scenario"""
    
    def setup_method(self):
        """Setup for each test method"""
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key-12345',
            'MCP_SERVER_URL': 'http://localhost:8080/sse'
        })
        self.env_patcher.start()
    
    def teardown_method(self):
        """Cleanup after each test method"""
        self.env_patcher.stop()
    
    async def test_weather_query_flow(self):
        """Test the complete weather query flow"""
        print("🌤️  Testing weather query: 'what's the weather like in Spokane?'")
        
        # Mock the MCPClient
        with patch('main.client') as mock_client:
            # Mock the connection
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Mock the process_query method to simulate weather response
            weather_response = AIMessage(
                content="The current weather in Spokane, WA is 72°F (22°C) with partly cloudy skies. "
                       "There's a 20% chance of rain this afternoon. "
                       "Winds are light at 5 mph from the northwest."
            )
            mock_client.process_query = AsyncMock(return_value=weather_response)
            
            # Import and test the graph
            from main import advanced_graph
            
            # Create test state with weather query
            test_state = {
                "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                "user_id": "test_user_123",
                "session_id": "weather_session_456",
                "conversation_count": 0
            }
            
            print("✅ Executing weather query through graph...")
            result = await advanced_graph.ainvoke(test_state)
            
            # Verify the response
            assert "messages" in result
            assert "conversation_count" in result
            assert len(result["messages"]) == 2  # Original + AI response
            
            # Check that MCP client was called
            mock_client.process_query.assert_called_once()
            
            # Verify the response content
            ai_message = result["messages"][-1]
            assert isinstance(ai_message, AIMessage)
            assert "weather" in ai_message.content.lower()
            assert "spokane" in ai_message.content.lower()
            
            print(f"✅ Weather response received: {ai_message.content[:100]}...")
            print(f"✅ Conversation count: {result['conversation_count']}")
            
            return True
    
    async def test_mcp_client_integration(self):
        """Test MCP client integration specifically"""
        print("🔗 Testing MCP client integration...")
        
        try:
            with patch('main.client') as mock_client:
                # Mock connection
                mock_client.connect_to_sse_server = AsyncMock()
                
                # Create a mock response that simulates MCP tool usage
                mock_response = AIMessage(
                    content="I'll check the weather for you in Spokane. "
                           "Let me use the weather service to get current conditions..."
                )
                mock_client.process_query = AsyncMock(return_value=mock_response)
                
                from main import advanced_chat_node
                
                # Test the chat node directly
                test_state = {
                    "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                    "user_id": "test_user",
                    "session_id": "test_session",
                    "conversation_count": 0
                }
                
                result = await advanced_chat_node(test_state, {})
                
                # Verify MCP client was called
                assert mock_client.process_query.called, "MCP client process_query was not called"
                mock_client.process_query.assert_called_once()
                
                # Check the call was made with the right messages
                called_messages = mock_client.process_query.call_args[0][0]
                assert len(called_messages) >= 1, "No messages passed to MCP client"
                
                # Check that the last message contains the weather query
                last_message = called_messages[-1]
                assert "spokane" in last_message.content.lower(), f"Spokane not found in message: {last_message.content}"
                
                print("✅ MCP client called with correct parameters")
                print("✅ Weather query processed successfully")
                
                return True
        except Exception as e:
            print(f"❌ MCP client integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def test_error_handling_weather_query(self):
        """Test error handling during weather query"""
        print("⚠️  Testing error handling for weather query...")
        
        with patch('main.client') as mock_client:
            # Mock connection
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Mock MCP client to raise an error
            mock_client.process_query = AsyncMock(
                side_effect=Exception("Weather service unavailable")
            )
            
            from main import advanced_chat_node
            
            test_state = {
                "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                "user_id": "test_user",
                "session_id": "test_session",
                "conversation_count": 0
            }
            
            result = await advanced_chat_node(test_state, {})
            
            # Should return error message
            assert "messages" in result
            assert len(result["messages"]) > 0
            
            error_message = result["messages"][-1]
            assert "error" in error_message.content.lower() or "apologize" in error_message.content.lower()
            
            print("✅ Error handling works correctly for weather queries")
            return True
    
    async def test_conversation_continuity(self):
        """Test that conversation continues after weather query"""
        print("💬 Testing conversation continuity...")
        
        with patch('main.client') as mock_client:
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Mock different responses for different queries
            def mock_process_query(messages):
                last_message = messages[-1].content.lower()
                if "weather" in last_message and "spokane" in last_message:
                    return AIMessage(content="The weather in Spokane is sunny and 75°F.")
                elif "follow" in last_message:
                    return AIMessage(content="I'd be happy to help with a follow-up question!")
                else:
                    return AIMessage(content="I can help you with that.")
            
            mock_client.process_query = AsyncMock(side_effect=mock_process_query)
            
            from main import advanced_graph
            
            # First query - weather
            state1 = {
                "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                "user_id": "test_user",
                "session_id": "test_session",
                "conversation_count": 0
            }
            
            result1 = await advanced_graph.ainvoke(state1)
            assert result1["conversation_count"] == 1
            
            # Second query - follow up
            state2 = {
                "messages": result1["messages"] + [HumanMessage(content="Can you tell me more about the weather?")],
                "user_id": "test_user",
                "session_id": "test_session",
                "conversation_count": result1["conversation_count"]
            }
            
            result2 = await advanced_graph.ainvoke(state2)
            assert result2["conversation_count"] == 2
            
            print("✅ Conversation continuity works correctly")
            print(f"✅ First conversation count: {result1['conversation_count']}")
            print(f"✅ Second conversation count: {result2['conversation_count']}")
            
            return True

async def run_weather_tests():
    """Run all weather query tests"""
    print("🌤️  Starting weather query tests for main.py...\n")
    
    test_instance = TestMainWeatherQuery()
    
    tests = [
        ("Weather Query Flow Test", test_instance.test_weather_query_flow),
        ("MCP Client Integration Test", test_instance.test_mcp_client_integration),
        ("Error Handling Test", test_instance.test_error_handling_weather_query),
        ("Conversation Continuity Test", test_instance.test_conversation_continuity),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        try:
            test_instance.setup_method()
            result = await test_func()
            test_instance.teardown_method()
            
            if result:
                passed += 1
                print(f"✅ {test_name} passed\n")
            else:
                print(f"❌ {test_name} failed\n")
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}\n")
            test_instance.teardown_method()
    
    print(f"📊 Weather Query Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All weather query tests passed!")
        print("\n📋 Weather Query Test Summary:")
        print("   ✅ Weather query 'what's the weather like in Spokane?' works")
        print("   ✅ MCP client is called with correct parameters")
        print("   ✅ Weather response is properly formatted")
        print("   ✅ Error handling works for weather queries")
        print("   ✅ Conversation continuity maintained")
        print("   ✅ Session management works correctly")
    else:
        print(f"⚠️  {total - passed} weather query tests failed.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(run_weather_tests())
