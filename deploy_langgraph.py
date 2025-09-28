#!/usr/bin/env python3
"""
LangGraph Cloud Deployment Script for MCP SSE Client.

This script helps deploy the MCP SSE agent to LangGraph Cloud
with proper configuration and environment setup.
"""

import os
import json
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv
from langgraph_config import LangGraphCloudManager, LangGraphCloudConfig

load_dotenv()


async def deploy_agent():
    """Deploy the MCP SSE agent to LangGraph Cloud."""
    print("🚀 Deploying MCP SSE Agent to LangGraph Cloud")
    print("=" * 50)
    
    # Check configuration
    config = LangGraphCloudConfig.from_env()
    
    if not config.is_valid():
        print("❌ Invalid LangGraph Cloud configuration")
        print("Please set the following environment variables:")
        print("  - LANGGRAPH_CLOUD_API_KEY")
        print("  - LANGGRAPH_CLOUD_DEPLOYMENT_ID")
        return False
    
    print("✅ Configuration valid")
    print(f"  API Key: {'*' * 8 if config.api_key else 'Not set'}")
    print(f"  Base URL: {config.base_url}")
    print(f"  Deployment ID: {config.deployment_id}")
    print(f"  Model: {config.model_name}")
    print(f"  Temperature: {config.temperature}")
    
    try:
        # Initialize the manager
        manager = LangGraphCloudManager(config)
        
        # Create deployment configuration
        deployment_config = {
            "name": "mcp-sse-agent",
            "description": "MCP SSE Client with LangChain Agent",
            "graph": {
                "nodes": [
                    {
                        "id": "input",
                        "type": "input",
                        "config": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "query": {"type": "string"},
                                    "context": {"type": "object"}
                                },
                                "required": ["query"]
                            }
                        }
                    },
                    {
                        "id": "agent",
                        "type": "agent",
                        "config": {
                            "model": config.model_name,
                            "temperature": config.temperature,
                            "max_tokens": config.max_tokens,
                            "tools": ["mcp_tools"]
                        }
                    },
                    {
                        "id": "output",
                        "type": "output",
                        "config": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "response": {"type": "string"},
                                    "metadata": {"type": "object"}
                                }
                            }
                        }
                    }
                ],
                "edges": [
                    {"from": "input", "to": "agent"},
                    {"from": "agent", "to": "output"}
                ]
            },
            "environment": {
                "OPENAI_API_KEY": "${OPENAI_API_KEY}",
                "MCP_SERVER_URL": "${MCP_SERVER_URL}",
                "LANGCHAIN_MODEL": config.model_name,
                "LANGCHAIN_TEMPERATURE": str(config.temperature)
            }
        }
        
        print("\n📦 Deploying agent...")
        result = await manager.deploy_graph(deployment_config)
        
        print("✅ Deployment successful!")
        print(f"  Deployment ID: {result.get('deployment_id')}")
        print(f"  Status: {result.get('status')}")
        print(f"  URL: {result.get('url')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        return False


async def check_deployment_status():
    """Check the status of the deployed agent."""
    print("\n📊 Checking deployment status...")
    
    try:
        config = LangGraphCloudConfig.from_env()
        manager = LangGraphCloudManager(config)
        
        status = await manager.get_deployment_status()
        
        print("✅ Deployment status retrieved")
        print(f"  Deployment ID: {status.get('deployment_id')}")
        print(f"  Status: {status.get('status')}")
        print(f"  Last Updated: {status.get('last_updated')}")
        print(f"  Version: {status.get('version')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check status: {e}")
        return False


async def test_deployment():
    """Test the deployed agent."""
    print("\n🧪 Testing deployed agent...")
    
    try:
        config = LangGraphCloudConfig.from_env()
        manager = LangGraphCloudManager(config)
        
        test_input = {
            "query": "Hello, can you help me with weather information?",
            "context": {"user_id": "test_user"}
        }
        
        result = await manager.invoke_graph(test_input)
        
        print("✅ Test successful!")
        print(f"  Result: {result.get('result')}")
        print(f"  Execution ID: {result.get('execution_id')}")
        print(f"  Status: {result.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


def validate_environment():
    """Validate the environment configuration."""
    print("🔍 Validating environment...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "LANGGRAPH_CLOUD_API_KEY",
        "LANGGRAPH_CLOUD_DEPLOYMENT_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True


def show_configuration():
    """Show the current configuration."""
    print("⚙️ Current Configuration")
    print("=" * 30)
    
    config = LangGraphCloudConfig.from_env()
    
    print(f"OpenAI API Key: {'*' * 8 if os.getenv('OPENAI_API_KEY') else 'Not set'}")
    print(f"LangGraph API Key: {'*' * 8 if config.api_key else 'Not set'}")
    print(f"Base URL: {config.base_url}")
    print(f"Deployment ID: {config.deployment_id}")
    print(f"Model: {config.model_name}")
    print(f"Temperature: {config.temperature}")
    print(f"Max Tokens: {config.max_tokens}")
    print(f"Environment: {config.environment}")
    print(f"Debug Mode: {config.debug_mode}")
    print(f"Valid: {config.is_valid()}")


async def main():
    """Main deployment workflow."""
    print("🚀 LangGraph Cloud Deployment for MCP SSE Client")
    print("=" * 60)
    
    # Validate environment
    if not validate_environment():
        print("\n❌ Environment validation failed")
        print("Please set the required environment variables and try again.")
        return
    
    # Show configuration
    show_configuration()
    
    # Deploy the agent
    success = await deploy_agent()
    
    if success:
        # Check deployment status
        await check_deployment_status()
        
        # Test the deployment
        await test_deployment()
        
        print("\n🎉 Deployment completed successfully!")
        print("\nNext steps:")
        print("1. Configure your MCP server URL")
        print("2. Test the agent with your queries")
        print("3. Monitor the deployment in LangGraph Cloud dashboard")
    else:
        print("\n❌ Deployment failed")
        print("Please check the configuration and try again.")


if __name__ == "__main__":
    asyncio.run(main())
