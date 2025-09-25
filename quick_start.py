#!/usr/bin/env python3
"""
Quick start script for OpenAI LangChain Agent
"""
import os
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    os.system("pip install -r requirements.txt")
    print("✅ Dependencies installed")

def setup_environment():
    """Setup environment file"""
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if not example_file.exists():
        print("❌ .env.example not found")
        return False
    
    print("📝 Creating .env file from example...")
    
    # Copy example to .env
    with open(example_file, 'r') as f:
        content = f.read()
    
    # Prompt for API key
    api_key = input("Enter your OpenAI API key: ").strip()
    if not api_key:
        print("❌ API key is required")
        return False
    
    # Replace placeholder with actual key
    content = content.replace("your_openai_api_key_here", api_key)
    
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ .env file created")
    return True

def test_setup():
    """Test the setup"""
    print("🧪 Testing setup...")
    try:
        from config import validate_config
        if validate_config():
            print("✅ Configuration is valid")
            
            # Quick agent test
            from langchain_agent import create_agent
            agent = create_agent()
            print(f"✅ Agent created: {agent.config.agent_name}")
            print("🎉 Setup completed successfully!")
            return True
        else:
            print("❌ Configuration validation failed")
            return False
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False

def main():
    """Main setup routine"""
    print("🚀 OpenAI LangChain Agent - Quick Start")
    print("=" * 50)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install dependencies
    install_dependencies()
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Test setup
    if not test_setup():
        sys.exit(1)
    
    print("\n🎯 Next Steps:")
    print("1. Start interactive chat: python main.py chat")
    print("2. Ask a single question: python main.py ask 'Hello!'")
    print("3. View examples: python example_usage.py")
    print("4. Get help: python main.py --help")

if __name__ == "__main__":
    main()
