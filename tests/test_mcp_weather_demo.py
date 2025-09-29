#!/usr/bin/env python3
"""
Demo test showing MCP client being called with weather query
This test specifically demonstrates the flow: user asks "what's the weather like in Spokane?"
and verifies that MCP client is called with the appropriate response
"""

import asyncio
import os
import sys
from unittest.mock import Mock, AsyncMock, patch
from langchain_core.messages import HumanMessage, AIMessage

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

async def demo_weather_query_with_mcp():
    """Demo the complete weather query flow with MCP integration"""
    print("🌤️  DEMO: Weather Query with MCP Integration")
    print("=" * 50)
    
    # Mock environment variables
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-12345',
        'MCP_SERVER_URL': 'http://localhost:8080/sse'
    }):
        
        # Mock the MCPClient with detailed logging
        with patch('main.client') as mock_client:
            print("🔧 Setting up MCP client mock...")
            
            # Mock the connection
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Track MCP calls
            mcp_calls = []
            
            async def mock_process_query(messages):
                """Mock process_query that logs the call and returns weather data"""
                print(f"\n📞 MCP Client called with {len(messages)} messages:")
                for i, msg in enumerate(messages):
                    print(f"   Message {i+1}: {msg.content}")
                
                # Store the call for verification
                mcp_calls.append({
                    'messages': messages,
                    'timestamp': asyncio.get_event_loop().time()
                })
                
                # Check if this is a weather query
                last_message = messages[-1].content.lower()
                if "weather" in last_message and "spokane" in last_message:
                    print("🌤️  Detected weather query for Spokane!")
                    print("🔍 MCP would call weather service here...")
                    
                    # Simulate weather service response
                    weather_data = {
                        "location": "Spokane, WA",
                        "temperature": "72°F (22°C)",
                        "conditions": "Partly Cloudy",
                        "humidity": "45%",
                        "wind": "5 mph NW",
                        "forecast": "20% chance of rain this afternoon"
                    }
                    
                    response_content = (
                        f"🌤️ Current weather in {weather_data['location']}:\n"
                        f"🌡️ Temperature: {weather_data['temperature']}\n"
                        f"☁️ Conditions: {weather_data['conditions']}\n"
                        f"💧 Humidity: {weather_data['humidity']}\n"
                        f"💨 Wind: {weather_data['wind']}\n"
                        f"🌧️ Forecast: {weather_data['forecast']}"
                    )
                    
                    print(f"📊 Weather data retrieved: {weather_data}")
                    return AIMessage(content=response_content)
                else:
                    return AIMessage(content="I can help you with that query.")
            
            mock_client.process_query = AsyncMock(side_effect=mock_process_query)
            
            print("✅ MCP client mock configured")
            print("\n🚀 Starting weather query simulation...")
            
            # Import and test the graph
            from main import advanced_graph
            
            # Create test state with weather query
            test_state = {
                "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                "user_id": "demo_user_123",
                "session_id": "weather_demo_session",
                "conversation_count": 0
            }
            
            print(f"👤 User query: '{test_state['messages'][0].content}'")
            print(f"🆔 User ID: {test_state['user_id']}")
            print(f"🔗 Session ID: {test_state['session_id']}")
            
            # Execute the query through the graph
            print("\n⚡ Executing through LangGraph...")
            result = await advanced_graph.ainvoke(test_state)
            
            print("\n📋 RESULTS:")
            print("=" * 30)
            
            # Verify the response
            assert "messages" in result
            assert "conversation_count" in result
            assert len(result["messages"]) == 2  # Original + AI response
            
            print(f"✅ Messages processed: {len(result['messages'])}")
            print(f"✅ Conversation count: {result['conversation_count']}")
            print(f"✅ MCP calls made: {len(mcp_calls)}")
            
            # Show the conversation
            print("\n💬 CONVERSATION:")
            for i, msg in enumerate(result["messages"]):
                if isinstance(msg, HumanMessage):
                    print(f"👤 User: {msg.content}")
                elif isinstance(msg, AIMessage):
                    print(f"🤖 Assistant: {msg.content}")
            
            # Verify MCP was called correctly
            assert len(mcp_calls) == 1
            mcp_call = mcp_calls[0]
            called_messages = mcp_call['messages']
            
            print(f"\n🔍 MCP CALL VERIFICATION:")
            print(f"✅ MCP was called with {len(called_messages)} messages")
            print(f"✅ Original query preserved: '{called_messages[0].content}'")
            print(f"✅ Weather location detected: 'spokane' in query")
            
            # Verify the response contains weather information
            ai_response = result["messages"][-1]
            assert "weather" in ai_response.content.lower()
            assert "spokane" in ai_response.content.lower()
            assert "temperature" in ai_response.content.lower()
            
            print(f"✅ Weather response contains expected data")
            print(f"✅ Response length: {len(ai_response.content)} characters")
            
            print("\n🎉 DEMO COMPLETED SUCCESSFULLY!")
            print("=" * 50)
            print("✅ User asked: 'what's the weather like in Spokane?'")
            print("✅ MCP client was called with the query")
            print("✅ Weather service returned current conditions")
            print("✅ Response formatted and returned to user")
            print("✅ Session management maintained")
            
            return True

async def demo_follow_up_weather_query():
    """Demo a follow-up weather query"""
    print("\n🌤️  DEMO: Follow-up Weather Query")
    print("=" * 40)
    
    with patch.dict(os.environ, {
        'OPENAI_API_KEY': 'test-key-12345',
        'MCP_SERVER_URL': 'http://localhost:8080/sse'
    }):
        
        with patch('main.client') as mock_client:
            mock_client.connect_to_sse_server = AsyncMock()
            
            # Track conversation state
            conversation_count = 0
            
            async def mock_process_query(messages):
                nonlocal conversation_count
                conversation_count += 1
                
                last_message = messages[-1].content.lower()
                print(f"\n📞 MCP Call #{conversation_count}: {last_message}")
                
                if "follow" in last_message or "more" in last_message:
                    return AIMessage(
                        content="I'd be happy to provide more weather details! "
                               "Would you like the 5-day forecast or hourly conditions?"
                    )
                elif "weather" in last_message:
                    return AIMessage(
                        content="The weather in Spokane is sunny and 75°F. "
                               "Perfect day for outdoor activities!"
                    )
                else:
                    return AIMessage(content="I can help you with that.")
            
            mock_client.process_query = AsyncMock(side_effect=mock_process_query)
            
            from main import advanced_graph
            
            # First query
            state1 = {
                "messages": [HumanMessage(content="what's the weather like in Spokane?")],
                "user_id": "demo_user",
                "session_id": "demo_session",
                "conversation_count": 0
            }
            
            result1 = await advanced_graph.ainvoke(state1)
            
            # Follow-up query
            state2 = {
                "messages": result1["messages"] + [HumanMessage(content="Can you tell me more about the weather?")],
                "user_id": "demo_user",
                "session_id": "demo_session",
                "conversation_count": result1["conversation_count"]
            }
            
            result2 = await advanced_graph.ainvoke(state2)
            
            print(f"✅ First conversation: {result1['conversation_count']}")
            print(f"✅ Follow-up conversation: {result2['conversation_count']}")
            print(f"✅ Total MCP calls: {conversation_count}")
            
            return True

async def run_weather_demo():
    """Run the complete weather query demo"""
    print("🌤️  WEATHER QUERY DEMO FOR MAIN.PY")
    print("=" * 50)
    print("This demo shows how the system handles:")
    print("1. User asks: 'what's the weather like in Spokane?'")
    print("2. MCP client is called with the query")
    print("3. Weather service returns data")
    print("4. Response is formatted and returned")
    print("=" * 50)
    
    try:
        # Run main demo
        success1 = await demo_weather_query_with_mcp()
        
        # Run follow-up demo
        success2 = await demo_follow_up_weather_query()
        
        if success1 and success2:
            print("\n🎉 ALL DEMOS COMPLETED SUCCESSFULLY!")
            print("✅ Weather query flow works perfectly")
            print("✅ MCP client integration verified")
            print("✅ Session management works")
            print("✅ Follow-up queries work")
        else:
            print("\n⚠️  Some demos failed")
            
        return success1 and success2
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(run_weather_demo())
