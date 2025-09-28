#!/usr/bin/env python3
"""
Example script demonstrating the LangChain agent functionality.

This script shows how to use the LangChain agent independently
and with MCP server integration.
"""

import asyncio
import os
from langchain_agent import LangChainAgent, MCPToolAdapter
from dotenv import load_dotenv

load_dotenv()


async def demo_basic_agent():
    """Demonstrate basic LangChain agent functionality."""
    print("🤖 Basic LangChain Agent Demo")
    print("=" * 40)
    
    # Initialize the agent
    agent = LangChainAgent(
        model_name="gpt-4o",
        temperature=0.7,
        use_langgraph_cloud=False
    )
    
    # Add some example tools
    def get_weather(location: str) -> str:
        """Get weather information for a location."""
        return f"Weather in {location}: Sunny, 72°F, Light winds"
    
    def calculate(expression: str) -> str:
        """Calculate mathematical expressions."""
        try:
            result = eval(expression)
            return f"Result: {result}"
        except:
            return "Error: Invalid expression"
    
    def get_time() -> str:
        """Get current time."""
        import datetime
        return f"Current time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    
    # Add tools to the agent
    agent.add_tool("get_weather", "Get weather information for a location", get_weather)
    agent.add_tool("calculate", "Calculate mathematical expressions", calculate)
    agent.add_tool("get_time", "Get current time", get_time)
    
    # Test queries
    test_queries = [
        "What's the weather like in San Francisco?",
        "Calculate 15 * 23 + 7",
        "What time is it now?",
        "Tell me about the weather and then calculate 100 / 4"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        try:
            response = await agent.process_query(query)
            print(f"🤖 Response: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Show agent status
    print(f"\n📊 Agent Status:")
    status = {
        "model": agent.model_name,
        "temperature": agent.temperature,
        "tools_available": len(agent.tools),
        "conversation_history_length": len(agent.get_conversation_history())
    }
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Export conversation
    filename = agent.export_conversation()
    print(f"\n📁 Conversation exported to: {filename}")


async def demo_mcp_integration():
    """Demonstrate MCP server integration (requires running MCP server)."""
    print("\n🔗 MCP Integration Demo")
    print("=" * 40)
    
    # Check if MCP server URL is available
    mcp_url = os.getenv('MCP_SERVER_URL')
    if not mcp_url:
        print("⚠️ MCP_SERVER_URL not set. Skipping MCP integration demo.")
        print("Set MCP_SERVER_URL environment variable to test MCP integration.")
        return
    
    try:
        from client import MCPClient
        
        # Initialize MCP client with LangChain agent
        client = MCPClient(use_langchain_agent=True)
        
        print(f"🔌 Connecting to MCP server: {mcp_url}")
        await client.connect_to_sse_server(mcp_url)
        
        # Test with MCP tools
        test_queries = [
            "What tools are available?",
            "Get the weather forecast for New York",
            "Show me weather alerts"
        ]
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            try:
                response = await client.process_query(query)
                print(f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # Show agent status
        status = client.get_agent_status()
        print(f"\n📊 Agent Status: {status}")
        
        # Cleanup
        await client.cleanup()
        
    except Exception as e:
        print(f"❌ MCP integration failed: {e}")
        print("Make sure you have a running MCP server and correct MCP_SERVER_URL")


async def demo_langgraph_cloud():
    """Demonstrate LangGraph Cloud configuration."""
    print("\n☁️ LangGraph Cloud Configuration Demo")
    print("=" * 40)
    
    from langgraph_config import LangGraphCloudConfig, create_env_template, create_deployment_config
    
    # Show configuration
    config = LangGraphCloudConfig.from_env()
    print("LangGraph Cloud Configuration:")
    for key, value in config.to_dict().items():
        if key == "api_key" and value:
            print(f"  {key}: {'*' * 8}")
        else:
            print(f"  {key}: {value}")
    
    print(f"\n✅ Configuration valid: {config.is_valid()}")
    
    # Show environment template
    print("\n📝 Environment Template:")
    env_template = create_env_template()
    print(env_template)
    
    # Show deployment configuration
    print("\n🚀 Deployment Configuration:")
    deployment_config = create_deployment_config()
    print(f"Deployment name: {deployment_config['name']}")
    print(f"Description: {deployment_config['description']}")
    print(f"Nodes: {len(deployment_config['graph']['nodes'])}")
    print(f"Edges: {len(deployment_config['graph']['edges'])}")


async def main():
    """Run all demonstrations."""
    print("🚀 LangChain Agent Demonstrations")
    print("=" * 50)
    
    # Basic agent demo
    await demo_basic_agent()
    
    # MCP integration demo
    await demo_mcp_integration()
    
    # LangGraph Cloud demo
    await demo_langgraph_cloud()
    
    print("\n✅ All demonstrations completed!")


if __name__ == "__main__":
    asyncio.run(main())
