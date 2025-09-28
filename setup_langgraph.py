#!/usr/bin/env python3
"""
Setup script for LangGraph Cloud integration.

This script installs all required dependencies and sets up the environment
for LangGraph Cloud deployment.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command: str, description: str) -> bool:
    """Run a command and return success status."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 13):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("Please upgrade to Python 3.13 or higher")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True


def install_dependencies():
    """Install all required dependencies."""
    print("📦 Installing dependencies...")
    
    # Update dependencies using uv
    if not run_command("uv sync", "Installing dependencies with uv"):
        return False
    
    # Install additional LangGraph dependencies if needed
    additional_deps = [
        "langchain-core",
        "langchain-community",
        "langsmith"
    ]
    
    for dep in additional_deps:
        if not run_command(f"uv add {dep}", f"Installing {dep}"):
            print(f"⚠️ Failed to install {dep}, continuing...")
    
    return True


def create_env_file():
    """Create .env file from template if it doesn't exist."""
    print("📝 Setting up environment file...")
    
    env_file = Path(".env")
    template_file = Path("env.template")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if template_file.exists():
        # Copy template to .env
        with open(template_file, 'r') as src, open(env_file, 'w') as dst:
            dst.write(src.read())
        print("✅ Created .env file from template")
        print("⚠️ Please edit .env file with your API keys")
        return True
    else:
        print("❌ env.template file not found")
        return False


def validate_langgraph_config():
    """Validate LangGraph configuration."""
    print("🔍 Validating LangGraph configuration...")
    
    langgraph_file = Path("langgraph.json")
    if not langgraph_file.exists():
        print("❌ langgraph.json file not found")
        return False
    
    try:
        import json
        with open(langgraph_file, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["dependencies", "graphs"]
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
        
        print("✅ LangGraph configuration is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in langgraph.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error validating LangGraph config: {e}")
        return False


def test_imports():
    """Test if all required modules can be imported."""
    print("🧪 Testing imports...")
    
    required_modules = [
        "langchain",
        "langchain_openai",
        "langgraph",
        "openai",
        "mcp"
    ]
    
    failed_imports = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"❌ Failed to import: {', '.join(failed_imports)}")
        return False
    
    print("✅ All required modules imported successfully")
    return True


def show_next_steps():
    """Show next steps for the user."""
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Edit .env file with your API keys:")
    print("   - OPENAI_API_KEY=your_openai_api_key")
    print("   - MCP_SERVER_URL=your_mcp_server_url")
    print("   - LANGGRAPH_CLOUD_API_KEY=your_langgraph_api_key (optional)")
    print("\n2. Test the setup:")
    print("   python example_agent.py")
    print("\n3. Run the client:")
    print("   uv run client.py")
    print("\n4. Deploy to LangGraph Cloud (optional):")
    print("   python deploy_langgraph.py")


def main():
    """Main setup workflow."""
    print("🚀 LangGraph Cloud Setup for MCP SSE Client")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        print("❌ Failed to install dependencies")
        sys.exit(1)
    
    # Create environment file
    if not create_env_file():
        print("❌ Failed to create environment file")
        sys.exit(1)
    
    # Validate LangGraph configuration
    if not validate_langgraph_config():
        print("❌ LangGraph configuration is invalid")
        sys.exit(1)
    
    # Test imports
    if not test_imports():
        print("❌ Some required modules could not be imported")
        print("Please check the installation and try again")
        sys.exit(1)
    
    # Show next steps
    show_next_steps()


if __name__ == "__main__":
    main()
