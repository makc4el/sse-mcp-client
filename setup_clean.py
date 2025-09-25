#!/usr/bin/env python3
"""
Clean Setup Script for MCP + LangChain Integration

This script ensures a clean installation without LangGraph conflicts.
"""

import subprocess
import sys
import os


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed")
            if result.stdout.strip():
                print(f"   Output: {result.stdout.strip()}")
        else:
            print(f"❌ {description} failed")
            print(f"   Error: {result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Clean MCP + LangChain Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required for LangChain")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Uninstall potentially conflicting packages
    conflicting_packages = [
        "langgraph",
        "langgraph-sdk", 
        "langsmith",
        "langchain-experimental"
    ]
    
    for package in conflicting_packages:
        run_command(f"pip uninstall -y {package}", f"Removing {package}")
    
    # Install core dependencies first
    if not run_command("pip install httpx==0.25.2", "Installing httpx"):
        return False
    
    if not run_command("pip install 'pydantic>=2.0.0,<3.0.0'", "Installing Pydantic"):
        return False
    
    # Install specific LangChain versions
    langchain_packages = [
        "langchain-core==0.1.52",
        "langchain==0.1.20", 
        "langchain-openai==0.1.8",
        "langchain-community==0.0.38"
    ]
    
    for package in langchain_packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    
    # Install development dependencies
    if not run_command("pip install pytest>=7.0.0 pytest-asyncio>=0.21.0", "Installing dev dependencies"):
        return False
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Set OPENAI_API_KEY environment variable")
    print("2. Start MCP server: cd ../sse-mcp-server && python main.py")
    print("3. Test integration: python simple_langchain_agent.py")
    
    return True


if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)
