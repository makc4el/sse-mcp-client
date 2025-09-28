#!/usr/bin/env python3
"""
LangGraph Cloud Configuration for MCP SSE Client.

This module provides configuration management for LangGraph Cloud integration,
including deployment settings, API keys, and environment-specific configurations.
"""

import os
from typing import Dict, Optional, Any
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class LangGraphCloudConfig:
    """Configuration for LangGraph Cloud integration."""
    
    # API Configuration
    api_key: Optional[str] = None
    base_url: str = "https://api.langgraph.cloud"
    
    # Deployment Configuration
    deployment_id: Optional[str] = None
    deployment_name: Optional[str] = None
    
    # Model Configuration
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 4000
    
    # Advanced Configuration
    enable_streaming: bool = True
    timeout_seconds: int = 30
    retry_attempts: int = 3
    
    # Environment Configuration
    environment: str = "development"
    debug_mode: bool = False
    
    @classmethod
    def from_env(cls) -> 'LangGraphCloudConfig':
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv("LANGGRAPH_CLOUD_API_KEY"),
            base_url=os.getenv("LANGGRAPH_CLOUD_BASE_URL", "https://api.langgraph.cloud"),
            deployment_id=os.getenv("LANGGRAPH_CLOUD_DEPLOYMENT_ID"),
            deployment_name=os.getenv("LANGGRAPH_CLOUD_DEPLOYMENT_NAME"),
            model_name=os.getenv("LANGGRAPH_CLOUD_MODEL", "gpt-4o"),
            temperature=float(os.getenv("LANGGRAPH_CLOUD_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LANGGRAPH_CLOUD_MAX_TOKENS", "4000")),
            enable_streaming=os.getenv("LANGGRAPH_CLOUD_STREAMING", "true").lower() == "true",
            timeout_seconds=int(os.getenv("LANGGRAPH_CLOUD_TIMEOUT", "30")),
            retry_attempts=int(os.getenv("LANGGRAPH_CLOUD_RETRIES", "3")),
            environment=os.getenv("LANGGRAPH_CLOUD_ENVIRONMENT", "development"),
            debug_mode=os.getenv("LANGGRAPH_CLOUD_DEBUG", "false").lower() == "true"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "api_key": self.api_key,
            "base_url": self.base_url,
            "deployment_id": self.deployment_id,
            "deployment_name": self.deployment_name,
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "enable_streaming": self.enable_streaming,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
            "environment": self.environment,
            "debug_mode": self.debug_mode
        }
    
    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return (
            self.api_key is not None and
            self.deployment_id is not None
        )
    
    def get_headers(self) -> Dict[str, str]:
        """Get HTTP headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": "MCP-SSE-Client/1.0"
        }


class LangGraphCloudManager:
    """Manager for LangGraph Cloud operations."""
    
    def __init__(self, config: Optional[LangGraphCloudConfig] = None):
        """Initialize with configuration."""
        self.config = config or LangGraphCloudConfig.from_env()
        self._validate_config()
    
    def _validate_config(self):
        """Validate the configuration."""
        if not self.config.is_valid():
            raise ValueError(
                "Invalid LangGraph Cloud configuration. "
                "Please set LANGGRAPH_CLOUD_API_KEY and LANGGRAPH_CLOUD_DEPLOYMENT_ID"
            )
    
    async def deploy_graph(self, graph_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy a graph to LangGraph Cloud.
        
        Args:
            graph_definition: Graph definition dictionary
            
        Returns:
            Deployment information
        """
        # This would implement the actual deployment logic
        # For now, return a mock response
        return {
            "deployment_id": self.config.deployment_id,
            "status": "deployed",
            "url": f"{self.config.base_url}/deployments/{self.config.deployment_id}",
            "created_at": "2024-01-01T00:00:00Z"
        }
    
    async def invoke_graph(self, 
                          input_data: Dict[str, Any], 
                          stream: bool = False) -> Dict[str, Any]:
        """
        Invoke a deployed graph.
        
        Args:
            input_data: Input data for the graph
            stream: Whether to stream the response
            
        Returns:
            Graph execution result
        """
        # This would implement the actual invocation logic
        # For now, return a mock response
        return {
            "result": f"Processed: {input_data}",
            "execution_id": "exec_123",
            "status": "completed"
        }
    
    async def get_deployment_status(self) -> Dict[str, Any]:
        """Get the status of the deployment."""
        return {
            "deployment_id": self.config.deployment_id,
            "status": "active",
            "last_updated": "2024-01-01T00:00:00Z",
            "version": "1.0.0"
        }


# Example usage and configuration templates
def create_env_template() -> str:
    """Create a template .env file for LangGraph Cloud configuration."""
    return """
# LangGraph Cloud Configuration
LANGGRAPH_CLOUD_API_KEY=your_api_key_here
LANGGRAPH_CLOUD_BASE_URL=https://api.langgraph.cloud
LANGGRAPH_CLOUD_DEPLOYMENT_ID=your_deployment_id_here
LANGGRAPH_CLOUD_DEPLOYMENT_NAME=your_deployment_name_here

# Model Configuration
LANGGRAPH_CLOUD_MODEL=gpt-4o
LANGGRAPH_CLOUD_TEMPERATURE=0.7
LANGGRAPH_CLOUD_MAX_TOKENS=4000

# Advanced Configuration
LANGGRAPH_CLOUD_STREAMING=true
LANGGRAPH_CLOUD_TIMEOUT=30
LANGGRAPH_CLOUD_RETRIES=3
LANGGRAPH_CLOUD_ENVIRONMENT=development
LANGGRAPH_CLOUD_DEBUG=false

# LangChain Configuration
LANGCHAIN_MODEL=gpt-4o
LANGCHAIN_TEMPERATURE=0.7
LANGGRAPH_CLOUD_ENABLED=true
"""


def create_deployment_config() -> Dict[str, Any]:
    """Create a sample deployment configuration."""
    return {
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
                            }
                        }
                    }
                },
                {
                    "id": "agent",
                    "type": "agent",
                    "config": {
                        "model": "gpt-4o",
                        "temperature": 0.7,
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
            "MCP_SERVER_URL": "${MCP_SERVER_URL}"
        }
    }


if __name__ == "__main__":
    # Example usage
    config = LangGraphCloudConfig.from_env()
    print("LangGraph Cloud Configuration:")
    print(f"API Key: {'*' * 8 if config.api_key else 'Not set'}")
    print(f"Deployment ID: {config.deployment_id}")
    print(f"Model: {config.model_name}")
    print(f"Valid: {config.is_valid()}")
    
    # Create environment template
    env_template = create_env_template()
    print("\nEnvironment Template:")
    print(env_template)
