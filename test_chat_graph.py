#!/usr/bin/env python3
"""
Test Chat Graph for LangGraph Studio Compatibility

Tests various scenarios to ensure the chat graph works properly
in LangGraph Studio's Chat interface.
"""

from langchain_core.messages import HumanMessage
from langgraph_chat_agent import graph


def test_chat_scenarios():
    """Test different chat scenarios"""
    
    test_cases = [
        {
            "name": "Simple Addition",
            "input": "What is 25 + 37?",
            "expected_keywords": ["25", "37", "62"]
        },
        {
            "name": "Maximum Finding", 
            "input": "Which is larger: 42 or 17?",
            "expected_keywords": ["42", "17", "larger", "maximum"]
        },
        {
            "name": "Greeting",
            "input": "Hello!",
            "expected_keywords": ["hello", "assistant", "mathematical"]
        },
        {
            "name": "Help Request",
            "input": "Help me",
            "expected_keywords": ["help", "addition", "maximum"]
        },
        {
            "name": "General Question",
            "input": "What can you do?",
            "expected_keywords": ["mathematical", "operations"]
        }
    ]
    
    print("🧪 Testing Chat Graph Scenarios")
    print("=" * 50)
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. Testing: {test_case['name']}")
        print(f"   Input: '{test_case['input']}'")
        
        try:
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=test_case['input'])],
                "mcp_server_url": "http://localhost:8000",
                "llm_model": "gpt-3.5-turbo", 
                "tools_loaded": False
            }
            
            # Run the graph
            result = graph.invoke(initial_state)
            
            # Get the AI response
            ai_messages = [msg for msg in result['messages'] if msg.type == 'ai']
            if ai_messages:
                response = ai_messages[-1].content.lower()
                print(f"   Response: '{ai_messages[-1].content[:100]}...'")
                
                # Check if expected keywords are present
                keywords_found = []
                for keyword in test_case['expected_keywords']:
                    if keyword.lower() in response:
                        keywords_found.append(keyword)
                
                if len(keywords_found) >= len(test_case['expected_keywords']) // 2:
                    print(f"   ✅ PASS - Found keywords: {keywords_found}")
                else:
                    print(f"   ❌ FAIL - Missing keywords. Found: {keywords_found}, Expected: {test_case['expected_keywords']}")
                    all_passed = False
            else:
                print(f"   ❌ FAIL - No AI response generated")
                all_passed = False
                
        except Exception as e:
            print(f"   ❌ ERROR - {str(e)}")
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 All tests passed! Graph is ready for LangGraph Studio Chat.")
    else:
        print("❌ Some tests failed. Check the implementation.")
    
    return all_passed


def test_message_continuity():
    """Test that the graph maintains conversation context"""
    print("\n🔄 Testing Message Continuity")
    print("-" * 30)
    
    try:
        # Start with a greeting
        initial_state = {
            "messages": [HumanMessage(content="Hello!")],
            "mcp_server_url": "http://localhost:8000",
            "llm_model": "gpt-3.5-turbo",
            "tools_loaded": False
        }
        
        result1 = graph.invoke(initial_state)
        print(f"First exchange: {len(result1['messages'])} messages")
        
        # Add a follow-up question
        result1['messages'].append(HumanMessage(content="What is 10 + 5?"))
        result2 = graph.invoke(result1)
        print(f"After follow-up: {len(result2['messages'])} messages")
        
        # Check that all messages are preserved
        human_count = sum(1 for msg in result2['messages'] if msg.type == 'human')
        ai_count = sum(1 for msg in result2['messages'] if msg.type == 'ai')
        system_count = sum(1 for msg in result2['messages'] if msg.type == 'system')
        
        print(f"Message breakdown: {human_count} human, {ai_count} AI, {system_count} system")
        
        if human_count == 2 and ai_count == 2 and system_count == 1:
            print("✅ Message continuity test passed!")
            return True
        else:
            print("❌ Message continuity test failed!")
            return False
            
    except Exception as e:
        print(f"❌ Continuity test error: {e}")
        return False


if __name__ == "__main__":
    print("🔧 LangGraph Studio Chat Compatibility Tests")
    print("=" * 60)
    
    scenario_passed = test_chat_scenarios()
    continuity_passed = test_message_continuity()
    
    print("\n" + "=" * 60)
    print("📊 FINAL RESULTS:")
    print(f"   Scenario Tests: {'✅ PASS' if scenario_passed else '❌ FAIL'}")
    print(f"   Continuity Test: {'✅ PASS' if continuity_passed else '❌ FAIL'}")
    
    if scenario_passed and continuity_passed:
        print("\n🎉 ALL TESTS PASSED!")
        print("The graph is ready for LangGraph Studio Chat interface!")
    else:
        print("\n❌ SOME TESTS FAILED!")
        print("Please check the implementation before using in LangGraph Studio.")
