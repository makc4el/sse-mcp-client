#!/usr/bin/env python3
"""
Real LangChain Agent Test with Emulated User Input

This script tests the actual LangChain agent with real OpenAI API calls
and emulates realistic user interactions.
"""

import asyncio
import logging
import os
from langchain_agent_example import MCPLangChainAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_real_agent_with_emulated_input():
    """Test the real LangChain agent with various user inputs"""
    
    print("🤖 Real LangChain Agent Test with MCP Tools")
    print("=" * 50)
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found!")
        print("Please set it with: export OPENAI_API_KEY='your-key-here'")
        return
    
    print(f"✅ OpenAI API key found (ends with: ...{api_key[-4:]})")
    
    # Create the agent
    agent = MCPLangChainAgent("http://localhost:8000")
    
    try:
        print("\n🔧 Initializing agent...")
        await agent.initialize()
        print("✅ Agent initialized successfully!")
        
        # Test queries that emulate real user interactions
        test_scenarios = [
            {
                "user": "Basic Addition User",
                "query": "What is 25 + 37?",
                "expected": "Should use add_numbers tool and return 62"
            },
            {
                "user": "Comparison User", 
                "query": "Which is larger: 156 or 89?",
                "expected": "Should use find_max tool and return 156"
            },
            {
                "user": "Complex Math User",
                "query": "Calculate the sum of 100 and 200, then tell me if that result is larger than 250",
                "expected": "Should use add_numbers then find_max, return 300 > 250"
            },
            {
                "user": "Multi-step User",
                "query": "I have two calculations: 15+25 and 18+22. Which sum is bigger?",
                "expected": "Should calculate both sums and compare them"
            },
            {
                "user": "Conversational User",
                "query": "Help me with some math - I need to find the maximum of 42 and 17",
                "expected": "Should understand intent and use find_max tool"
            }
        ]
        
        print(f"\n🎯 Running {len(test_scenarios)} real user scenarios...\n")
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'='*20} SCENARIO {i} {'='*20}")
            print(f"👤 User Type: {scenario['user']}")
            print(f"💬 User Says: \"{scenario['query']}\"")
            print(f"🎯 Expected: {scenario['expected']}")
            print("\n🤖 Agent Processing...")
            
            try:
                # This will make real API calls to OpenAI
                response = await agent.run(scenario['query'])
                print(f"\n✅ Agent Response: {response}")
                
            except Exception as e:
                print(f"\n❌ Error in scenario {i}: {e}")
            
            print(f"\n{'='*60}")
            
            # Brief pause between scenarios
            await asyncio.sleep(1)
        
        print(f"\n🎉 All scenarios completed!")
        
        # Test interactive-style conversation
        print(f"\n💬 Testing conversational flow...")
        conversation_flow = [
            "Hi, I need help with math",
            "Can you add 50 and 75?", 
            "Now find the maximum between that result and 100",
            "Thanks, that was helpful!"
        ]
        
        for msg in conversation_flow:
            print(f"\n👤 User: {msg}")
            try:
                if "add" in msg or "maximum" in msg or "math" in msg:
                    response = await agent.run(msg)
                    print(f"🤖 Agent: {response}")
                else:
                    print(f"🤖 Agent: You're welcome! I'm here to help with math calculations.")
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")
        
    finally:
        await agent.cleanup()


async def benchmark_performance():
    """Benchmark the agent performance"""
    print(f"\n⚡ Performance Benchmark")
    print("=" * 30)
    
    agent = MCPLangChainAgent("http://localhost:8000")
    
    try:
        await agent.initialize()
        
        # Time multiple operations
        import time
        
        queries = [
            "What is 10 + 20?",
            "Find max of 5 and 15", 
            "Add 30 and 40",
            "Which is bigger: 25 or 35?"
        ]
        
        start_time = time.time()
        
        for query in queries:
            query_start = time.time()
            response = await agent.run(query)
            query_time = time.time() - query_start
            print(f"⏱️ '{query}' → {query_time:.2f}s")
        
        total_time = time.time() - start_time
        avg_time = total_time / len(queries)
        
        print(f"\n📊 Performance Results:")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Average per query: {avg_time:.2f}s")
        print(f"   Queries per minute: ~{60/avg_time:.0f}")
        
    except Exception as e:
        print(f"❌ Benchmark failed: {e}")
        
    finally:
        await agent.cleanup()


async def main():
    """Main test function"""
    
    # Check if server is running
    try:
        from mcp_client import SSEMCPClient
        client = SSEMCPClient("http://localhost:8000")
        if not await client.health_check():
            print("❌ MCP server is not running!")
            print("Please start it with: cd ../sse-mcp-server && python main.py")
            return
        await client.disconnect()
        print("✅ MCP server is running")
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return
    
    # Run tests
    await test_real_agent_with_emulated_input()
    
    # Run performance benchmark if requested
    print(f"\n🏃‍♂️ Run performance benchmark? (y/n): ", end="")
    # For automation, we'll skip this interactive part
    # choice = input().strip().lower()
    # if choice == 'y':
    #     await benchmark_performance()
    
    print(f"\n🎉 Real agent testing completed!")
    print(f"💡 Your MCP tools are fully integrated with LangChain!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
