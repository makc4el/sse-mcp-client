#!/usr/bin/env python3
"""
Environment Switcher for MCP Client

This utility helps you quickly switch between local development
and Railway production environments.
"""

import os
import sys
from config import MCPClientConfig


def switch_to_local():
    """Switch to local development environment"""
    print("🔧 Switching to LOCAL development environment...")
    print("export ENVIRONMENT=development")
    print("export MCP_SERVER_URL=http://localhost:8000")
    print()
    print("To apply these settings, run:")
    print("eval $(python switch_environment.py local --export)")


def switch_to_railway():
    """Switch to Railway production environment"""
    print("🚀 Switching to RAILWAY production environment...")
    print("export ENVIRONMENT=production")
    print("export MCP_SERVER_URL=https://web-production-b40eb.up.railway.app")
    print()
    print("To apply these settings, run:")
    print("eval $(python switch_environment.py railway --export)")


def export_local():
    """Export local environment variables"""
    print("export ENVIRONMENT=development")
    print("export MCP_SERVER_URL=http://localhost:8000")


def export_railway():
    """Export Railway environment variables"""
    print("export ENVIRONMENT=production")
    print("export MCP_SERVER_URL=https://web-production-b40eb.up.railway.app")


def show_current():
    """Show current configuration"""
    print("🔍 Current MCP Client Configuration:")
    print("=" * 40)
    MCPClientConfig.print_config()


def test_connection():
    """Test connection to current configured server"""
    import asyncio
    from mcp_client import SSEMCPClient
    
    async def _test():
        server_url = MCPClientConfig.get_server_url()
        print(f"🧪 Testing connection to: {server_url}")
        
        try:
            client = SSEMCPClient(server_url)
            if await client.health_check():
                print("✅ Server is healthy and reachable")
                return True
            else:
                print("❌ Server health check failed")
                return False
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
        finally:
            if 'client' in locals():
                await client.disconnect()
    
    return asyncio.run(_test())


def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("🌍 MCP Client Environment Switcher")
        print("=" * 40)
        print()
        print("Usage:")
        print("  python switch_environment.py <command>")
        print()
        print("Commands:")
        print("  local          - Switch to local development")
        print("  railway        - Switch to Railway production")
        print("  current        - Show current configuration")
        print("  test           - Test connection to current server")
        print("  local --export - Export local environment variables")
        print("  railway --export - Export Railway environment variables")
        print()
        print("Quick setup:")
        print("  eval $(python switch_environment.py local --export)")
        print("  eval $(python switch_environment.py railway --export)")
        return
    
    command = sys.argv[1].lower()
    export_mode = "--export" in sys.argv
    
    if command == "local":
        if export_mode:
            export_local()
        else:
            switch_to_local()
    elif command == "railway":
        if export_mode:
            export_railway()
        else:
            switch_to_railway()
    elif command == "current":
        show_current()
    elif command == "test":
        if test_connection():
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()

