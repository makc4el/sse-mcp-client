#!/usr/bin/env python3
"""
Configuration for SSE MCP Client

This module handles environment variables and configuration settings
for both local development and production deployment.
"""

import os
from typing import Optional


class MCPClientConfig:
    """Configuration class for MCP Client"""
    
    # Server URLs
    LOCAL_SERVER_URL = "http://localhost:8000"
    RAILWAY_SERVER_URL = "https://web-production-b40eb.up.railway.app"
    
    @classmethod
    def get_server_url(cls) -> str:
        """
        Get the MCP server URL based on environment configuration
        
        Priority:
        1. MCP_SERVER_URL environment variable
        2. ENVIRONMENT-based selection (production = Railway, development = local)
        3. Default to local server
        """
        # Check for explicit URL override
        explicit_url = os.getenv("MCP_SERVER_URL")
        if explicit_url:
            return explicit_url
        
        # Check environment setting
        environment = os.getenv("ENVIRONMENT", "development").lower()
        
        if environment == "production":
            return cls.RAILWAY_SERVER_URL
        else:
            return cls.LOCAL_SERVER_URL
    
    @classmethod
    def get_openai_api_key(cls) -> Optional[str]:
        """Get OpenAI API key from environment"""
        return os.getenv("OPENAI_API_KEY")
    
    @classmethod
    def get_timeout(cls) -> int:
        """Get client timeout from environment"""
        return int(os.getenv("MCP_CLIENT_TIMEOUT", 30))
    
    @classmethod
    def is_verbose(cls) -> bool:
        """Check if verbose logging is enabled"""
        return os.getenv("MCP_CLIENT_VERBOSE", "false").lower() == "true"
    
    @classmethod
    def is_production(cls) -> bool:
        """Check if running in production environment"""
        return os.getenv("ENVIRONMENT", "development").lower() == "production"
    
    @classmethod
    def print_config(cls):
        """Print current configuration (for debugging)"""
        print("🔧 MCP Client Configuration:")
        print(f"   Server URL: {cls.get_server_url()}")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"   Timeout: {cls.get_timeout()}s")
        print(f"   Verbose: {cls.is_verbose()}")
        print(f"   OpenAI API Key: {'✅ Set' if cls.get_openai_api_key() else '❌ Not Set'}")


# Convenience functions for backward compatibility
def get_server_url() -> str:
    """Get the configured MCP server URL"""
    return MCPClientConfig.get_server_url()

def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key"""
    return MCPClientConfig.get_openai_api_key()

def is_production() -> bool:
    """Check if in production mode"""
    return MCPClientConfig.is_production()


# Environment variable examples and documentation
ENVIRONMENT_DOCS = """
🌍 Environment Variable Configuration:

For LOCAL development:
export ENVIRONMENT=development
export MCP_SERVER_URL=http://localhost:8000

For RAILWAY production:
export ENVIRONMENT=production
export MCP_SERVER_URL=https://web-production-b40eb.up.railway.app

For OpenAI integration:
export OPENAI_API_KEY=your-openai-api-key-here

For custom settings:
export MCP_CLIENT_TIMEOUT=60
export MCP_CLIENT_VERBOSE=true

Quick setup commands:

# Use Railway server
export ENVIRONMENT=production

# Use local server  
export ENVIRONMENT=development

# Override with specific URL
export MCP_SERVER_URL=https://web-production-b40eb.up.railway.app

# Enable verbose logging
export MCP_CLIENT_VERBOSE=true
"""


if __name__ == "__main__":
    print(ENVIRONMENT_DOCS)
    print()
    MCPClientConfig.print_config()

