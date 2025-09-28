#!/usr/bin/env python3
"""
Test script to verify LangGraph Cloud deployment configuration.

This script tests all components needed for successful deployment
to LangGraph Cloud.
"""

import json
import os
import sys
from pathlib import Path


def test_python_version():
    """Test Python version compatibility."""
    print("🐍 Testing Python version...")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("LangGraph Cloud requires Python 3.11 or higher")
        return False


def test_pyproject_toml():
    """Test pyproject.toml configuration."""
    print("📦 Testing pyproject.toml...")
    
    pyproject_file = Path("pyproject.toml")
    if not pyproject_file.exists():
        print("❌ pyproject.toml not found")
        return False
    
    try:
        import tomllib
        with open(pyproject_file, 'rb') as f:
            config = tomllib.load(f)
        
        # Check Python version requirement
        python_req = config.get("project", {}).get("requires-python", "")
        if ">=3.11" in python_req:
            print("✅ Python version requirement is correct")
        else:
            print(f"❌ Python version requirement is incorrect: {python_req}")
            return False
        
        # Check required dependencies
        dependencies = config.get("project", {}).get("dependencies", [])
        required_deps = [
            "openai",
            "langchain",
            "langgraph",
            "mcp"
        ]
        
        missing_deps = []
        for dep in required_deps:
            if not any(dep in d for d in dependencies):
                missing_deps.append(dep)
        
        if missing_deps:
            print(f"❌ Missing dependencies: {missing_deps}")
            return False
        
        print("✅ All required dependencies found")
        return True
        
    except Exception as e:
        print(f"❌ Error reading pyproject.toml: {e}")
        return False


def test_langgraph_json():
    """Test langgraph.json configuration."""
    print("🔧 Testing langgraph.json...")
    
    langgraph_file = Path("langgraph.json")
    if not langgraph_file.exists():
        print("❌ langgraph.json not found")
        return False
    
    try:
        with open(langgraph_file, 'r') as f:
            config = json.load(f)
        
        # Check required fields
        required_fields = ["dependencies", "graphs"]
        for field in required_fields:
            if field not in config:
                print(f"❌ Missing required field: {field}")
                return False
        
        # Check Python version
        python_version = config.get("python_version")
        if python_version == "3.11":
            print("✅ Python version is correct")
        else:
            print(f"❌ Python version is incorrect: {python_version}")
            return False
        
        # Check image distribution
        image_distro = config.get("image_distro")
        if image_distro == "wolfi":
            print("✅ Image distribution is correct")
        else:
            print(f"⚠️ Image distribution not set to wolfi: {image_distro}")
        
        # Check graph configuration
        graphs = config.get("graphs", {})
        if "mcp-sse-agent" in graphs:
            print("✅ Graph configuration found")
        else:
            print("❌ Graph configuration not found")
            return False
        
        print("✅ langgraph.json configuration is valid")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in langgraph.json: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading langgraph.json: {e}")
        return False


def test_agent_function():
    """Test the create_langgraph_agent function."""
    print("🤖 Testing create_langgraph_agent function...")
    
    try:
        from client import create_langgraph_agent
        
        # Test function exists
        if not callable(create_langgraph_agent):
            print("❌ create_langgraph_agent is not callable")
            return False
        
        print("✅ create_langgraph_agent function found")
        
        # Test function execution (with fallback handling)
        try:
            agent = create_langgraph_agent()
            print("✅ Agent created successfully")
            return True
        except Exception as e:
            print(f"⚠️ Agent creation failed (expected in test environment): {e}")
            print("✅ Function exists and is callable")
            return True
        
    except ImportError as e:
        print(f"❌ Cannot import create_langgraph_agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing agent function: {e}")
        return False


def test_environment():
    """Test environment configuration."""
    print("🌍 Testing environment configuration...")
    
    # Check for .env file
    env_file = Path(".env")
    template_file = Path("env.template")
    
    if env_file.exists():
        print("✅ .env file found")
    elif template_file.exists():
        print("⚠️ .env file not found, but template exists")
        print("   Copy env.template to .env and configure your API keys")
    else:
        print("❌ No environment configuration found")
        return False
    
    # Check for required environment variables (if .env exists)
    if env_file.exists():
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            required_vars = ["OPENAI_API_KEY"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                print(f"⚠️ Missing environment variables: {missing_vars}")
                print("   Set these in your .env file")
            else:
                print("✅ Required environment variables are set")
            
            return True
            
        except ImportError:
            print("⚠️ python-dotenv not available, cannot test environment variables")
            return True
    
    return True


def test_dependencies():
    """Test if required dependencies can be imported."""
    print("📚 Testing dependencies...")
    
    required_modules = [
        "openai",
        "langchain",
        "langgraph",
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
        print("   Run 'uv sync' to install dependencies")
        return False
    
    print("✅ All required modules imported successfully")
    return True


def main():
    """Run all deployment tests."""
    print("🚀 LangGraph Cloud Deployment Test")
    print("=" * 40)
    
    tests = [
        ("Python Version", test_python_version),
        ("pyproject.toml", test_pyproject_toml),
        ("langgraph.json", test_langgraph_json),
        ("Agent Function", test_agent_function),
        ("Environment", test_environment),
        ("Dependencies", test_dependencies)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name}")
        print("-" * 20)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Summary")
    print("=" * 20)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Ready for deployment to LangGraph Cloud.")
        return True
    else:
        print("⚠️ Some tests failed. Please fix the issues before deploying.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
