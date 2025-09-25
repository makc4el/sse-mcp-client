#!/usr/bin/env python3
"""
LangGraph server setup and deployment utilities
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from langgraph_agent import create_langgraph_agent, create_graph
from config import validate_config, get_config


console = Console()


def display_server_info():
    """Display LangGraph server information"""
    info_text = """
🔗 LangGraph Server for OpenAI Agent

This server provides:
- REST API endpoints for the OpenAI conversational agent
- WebSocket support for real-time streaming
- Persistent conversation state management
- Thread-based conversation isolation
- Full LangGraph deployment capabilities
    """
    
    console.print(Panel(info_text.strip(), title="🚀 LangGraph Server", border_style="blue"))


@click.group()
def cli():
    """LangGraph server management for OpenAI Agent"""
    pass


@cli.command()
@click.option('--host', default='localhost', help='Host to bind the server to')
@click.option('--port', default=8123, help='Port to bind the server to')
@click.option('--reload', is_flag=True, help='Enable auto-reload for development')
def dev(host: str, port: int, reload: bool):
    """Start LangGraph server in development mode"""
    
    console.print("🔧 Starting LangGraph development server...")
    
    if not validate_config():
        console.print("❌ Configuration validation failed", style="red")
        sys.exit(1)
    
    # Show server info
    display_server_info()
    
    # Start development server
    import subprocess
    
    cmd = [
        "langgraph", "dev",
        "--host", host,
        "--port", str(port)
    ]
    
    if reload:
        cmd.append("--reload")
    
    console.print(f"🚀 Starting server on {host}:{port}")
    console.print("📖 API docs will be available at: http://{}:{}/docs".format(host, port))
    
    try:
        subprocess.run(cmd, cwd=Path.cwd())
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Server error: {e}", style="red")


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind the server to')
@click.option('--port', default=8000, help='Port to bind the server to')
@click.option('--workers', default=1, help='Number of worker processes')
def serve(host: str, port: int, workers: int):
    """Start LangGraph server in production mode"""
    
    console.print("🏭 Starting LangGraph production server...")
    
    if not validate_config():
        console.print("❌ Configuration validation failed", style="red")
        sys.exit(1)
    
    # Start production server  
    import subprocess
    
    cmd = [
        "langgraph", "serve",
        "--host", host,
        "--port", str(port),
        "--workers", str(workers)
    ]
    
    console.print(f"🚀 Starting production server on {host}:{port} with {workers} workers")
    
    try:
        subprocess.run(cmd, cwd=Path.cwd())
    except KeyboardInterrupt:
        console.print("\n👋 Server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Server error: {e}", style="red")


@cli.command()
def info():
    """Show LangGraph configuration and agent information"""
    
    display_server_info()
    
    # Show configuration
    console.print("\n📋 Current Configuration:", style="bold")
    
    try:
        config = get_config()
        
        config_table = Table(show_header=True)
        config_table.add_column("Setting", style="cyan", width=20)
        config_table.add_column("Value", style="white")
        
        config_items = [
            ("Agent Name", config.agent_name),
            ("OpenAI Model", config.openai_model),
            ("Temperature", str(config.openai_temperature)),
            ("Max History", str(config.max_history_length)),
            ("Streaming", "✅ Enabled" if config.enable_streaming else "❌ Disabled"),
            ("API Key", "✅ Configured" if config.openai_api_key else "❌ Missing"),
        ]
        
        for setting, value in config_items:
            config_table.add_row(setting, value)
        
        console.print(config_table)
        
    except Exception as e:
        console.print(f"❌ Could not load configuration: {str(e)}", style="red")
    
    # Show LangGraph info
    console.print("\n🔗 LangGraph Agent Info:", style="bold")
    
    try:
        agent = create_langgraph_agent()
        
        graph_info = Table(show_header=True)
        graph_info.add_column("Property", style="cyan", width=20)
        graph_info.add_column("Value", style="white")
        
        graph_info.add_row("Graph Type", "StateGraph")
        graph_info.add_row("Memory Backend", "MemorySaver")
        graph_info.add_row("Nodes", "conversation, update_metadata")
        graph_info.add_row("Streaming", "✅ Supported")
        graph_info.add_row("Async", "✅ Supported")
        graph_info.add_row("Checkpoints", "✅ Enabled")
        
        console.print(graph_info)
        
        # Show graph structure
        console.print("\n🏗️ Graph Structure:", style="bold")
        try:
            graph_ascii = agent.get_graph_visualization()
            console.print(graph_ascii, style="dim")
        except Exception:
            console.print("Graph visualization not available", style="dim")
        
    except Exception as e:
        console.print(f"❌ Could not load agent: {str(e)}", style="red")


@cli.command()
def test():
    """Test the LangGraph agent functionality"""
    
    console.print("🧪 Testing LangGraph agent...")
    
    if not validate_config():
        console.print("❌ Configuration validation failed", style="red")
        sys.exit(1)
    
    try:
        # Create agent
        agent = create_langgraph_agent()
        console.print(f"✅ Agent created: {agent.config.agent_name}")
        
        # Test basic conversation
        test_thread = "test_thread_123"
        console.print(f"\n📤 Testing conversation (thread: {test_thread})")
        
        response1 = agent.chat("Hello! My name is Alice.", thread_id=test_thread)
        console.print(f"📥 Response 1: {response1}")
        
        response2 = agent.chat("What's my name?", thread_id=test_thread)
        console.print(f"📥 Response 2: {response2}")
        
        # Test metadata
        metadata = agent.get_conversation_metadata(test_thread)
        console.print(f"\n📊 Conversation metadata: {metadata}")
        
        # Test history
        history = agent.get_conversation_history(test_thread)
        console.print(f"📚 History length: {len(history)} messages")
        
        # Clean up
        agent.clear_conversation(test_thread)
        console.print(f"🗑️ Test conversation cleared")
        
        console.print("\n✅ All tests passed!")
        
    except Exception as e:
        console.print(f"❌ Test failed: {str(e)}", style="red")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def validate():
    """Validate LangGraph configuration and setup"""
    
    console.print("🔍 Validating LangGraph setup...")
    
    checks = []
    
    # Check langgraph.json
    langgraph_file = Path("langgraph.json")
    if langgraph_file.exists():
        checks.append(("✅", "langgraph.json exists"))
        try:
            import json
            with open(langgraph_file) as f:
                config = json.load(f)
            checks.append(("✅", "langgraph.json is valid JSON"))
            
            if "graphs" in config:
                checks.append(("✅", "graphs configuration found"))
            else:
                checks.append(("❌", "graphs configuration missing"))
                
        except Exception as e:
            checks.append(("❌", f"langgraph.json invalid: {e}"))
    else:
        checks.append(("❌", "langgraph.json not found"))
    
    # Check agent file
    agent_file = Path("langgraph_agent.py")
    if agent_file.exists():
        checks.append(("✅", "langgraph_agent.py exists"))
        
        try:
            from langgraph_agent import create_langgraph_agent
            checks.append(("✅", "create_langgraph_agent function importable"))
        except ImportError as e:
            checks.append(("❌", f"Cannot import create_langgraph_agent: {e}"))
    else:
        checks.append(("❌", "langgraph_agent.py not found"))
    
    # Check dependencies
    try:
        import langgraph
        checks.append(("✅", f"langgraph installed (v{langgraph.__version__})"))
    except ImportError:
        checks.append(("❌", "langgraph not installed"))
    
    try:
        import langchain_openai
        checks.append(("✅", "langchain-openai available"))
    except ImportError:
        checks.append(("❌", "langchain-openai not installed"))
    
    # Check environment
    if validate_config():
        checks.append(("✅", "Environment configuration valid"))
    else:
        checks.append(("❌", "Environment configuration invalid"))
    
    # Display results
    console.print("\n📋 Validation Results:")
    
    validation_table = Table(show_header=False)
    validation_table.add_column("Status", width=3)
    validation_table.add_column("Check", style="white")
    
    all_passed = True
    for status, check in checks:
        validation_table.add_row(status, check)
        if status == "❌":
            all_passed = False
    
    console.print(validation_table)
    
    if all_passed:
        console.print("\n🎉 All validations passed! LangGraph setup is ready.", style="green")
    else:
        console.print("\n⚠️ Some validations failed. Please fix the issues above.", style="yellow")
        sys.exit(1)


if __name__ == "__main__":
    cli()
