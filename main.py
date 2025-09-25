#!/usr/bin/env python3
"""
Main application runner for OpenAI LangChain Agent
"""
import sys
import asyncio
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from config import validate_config, get_config
from langchain_agent import create_agent
from chat_interface import ChatInterface, AsyncChatInterface


console = Console()


def display_banner():
    """Display application banner"""
    banner = """
🤖 OpenAI LangChain Agent

A fully compatible LangChain AI agent with OpenAI LLM integration.
Perfect for conversational AI, chatbots, and intelligent assistance.
    """
    console.print(Panel(banner.strip(), title="🚀 AI Agent", border_style="blue"))


def display_features():
    """Display key features"""
    features_table = Table(title="🌟 Key Features", show_header=False)
    features_table.add_column("Feature", style="green", width=40)
    
    features = [
        "✅ Full LangChain compatibility",
        "✅ OpenAI GPT-4/GPT-3.5 integration", 
        "✅ Real-time streaming responses",
        "✅ Conversation memory management",
        "✅ Async/sync operation modes",
        "✅ Rich interactive chat interface",
        "✅ Conversation export/import",
        "✅ Configurable via environment variables",
        "✅ CLI with multiple options",
        "✅ Production-ready architecture"
    ]
    
    for feature in features:
        features_table.add_row(feature)
    
    console.print(features_table)


@click.group()
@click.pass_context
def cli(ctx):
    """OpenAI LangChain Agent - Conversational AI with full LangChain compatibility"""
    ctx.ensure_object(dict)
    
    # Validate configuration at startup
    if not validate_config():
        console.print("❌ Configuration validation failed. Run 'setup' command first.", style="red")
        sys.exit(1)


@cli.command()
@click.option('--async-mode', '-a', is_flag=True, help='Run in async mode')
@click.option('--no-stream', '-n', is_flag=True, help='Disable streaming responses')
@click.option('--model', '-m', help='Override OpenAI model (e.g., gpt-4, gpt-3.5-turbo)')
@click.option('--temperature', '-t', type=float, help='Set response temperature (0.0-2.0)')
def chat(async_mode: bool, no_stream: bool, model: str, temperature: float):
    """Start interactive chat with the AI agent"""
    
    console.print("🚀 Starting chat interface...\n")
    
    # Create agent with optional overrides
    agent = create_agent()
    
    if model:
        console.print(f"🔄 Using model: {model}")
        agent.config.openai_model = model
        # Recreate LLM with new model
        from langchain_openai import ChatOpenAI
        agent.llm = ChatOpenAI(
            model=model,
            temperature=temperature or agent.config.openai_temperature,
            max_tokens=agent.config.openai_max_tokens,
            openai_api_key=agent.config.openai_api_key,
            streaming=agent.config.enable_streaming and not no_stream
        )
    
    if temperature is not None:
        console.print(f"🌡️ Temperature set to: {temperature}")
        agent.config.openai_temperature = temperature
    
    if no_stream:
        console.print("📝 Streaming disabled")
        agent.config.enable_streaming = False
    
    # Launch interface
    try:
        if async_mode:
            console.print("⚡ Running in async mode")
            interface = AsyncChatInterface(agent)
            asyncio.run(interface.arun())
        else:
            interface = ChatInterface(agent)
            interface.run()
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
    except Exception as e:
        console.print(f"💥 Error: {str(e)}", style="red")
        sys.exit(1)


@cli.command()
@click.argument('message')
@click.option('--model', '-m', help='OpenAI model to use')
@click.option('--temperature', '-t', type=float, help='Response temperature')
@click.option('--stream/--no-stream', default=True, help='Enable/disable streaming')
def ask(message: str, model: str, temperature: float, stream: bool):
    """Ask the agent a single question and get a response"""
    
    agent = create_agent()
    
    # Apply overrides
    if model:
        agent.config.openai_model = model
    if temperature is not None:
        agent.config.openai_temperature = temperature
    agent.config.enable_streaming = stream
    
    console.print(f"[bold blue]Question:[/bold blue] {message}\n")
    console.print(f"[bold green]{agent.config.agent_name}:[/bold green] ", end="")
    
    try:
        response = agent.chat(message, stream=stream)
        if not stream:
            console.print(response)
    except Exception as e:
        console.print(f"❌ Error: {str(e)}", style="red")
        sys.exit(1)


@cli.command()
def setup():
    """Setup the application with environment configuration"""
    
    console.print("🔧 Setting up OpenAI LangChain Agent...\n")
    
    # Check if .env exists
    env_file = Path(".env")
    
    if env_file.exists():
        console.print("✅ Found existing .env file")
        if validate_config():
            console.print("✅ Configuration is valid!")
            return
    else:
        console.print("📝 Creating .env file...")
    
    # Interactive setup
    console.print("\n🔑 OpenAI API Configuration:")
    
    api_key = click.prompt("Enter your OpenAI API key", hide_input=True)
    model = click.prompt("OpenAI model", default="gpt-4")
    temperature = click.prompt("Temperature (0.0-2.0)", default=0.7, type=float)
    agent_name = click.prompt("Agent name", default="OpenAI Assistant")
    
    # Create .env file
    env_content = f"""# OpenAI Configuration
OPENAI_API_KEY={api_key}
OPENAI_MODEL={model}
OPENAI_TEMPERATURE={temperature}
AGENT_NAME={agent_name}

# Chat Settings
MAX_HISTORY_LENGTH=20
ENABLE_STREAMING=true

# Optional: LangSmith (for monitoring)
# LANGSMITH_API_KEY=your_langsmith_key
# LANGSMITH_PROJECT=openai-langchain-agent
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    console.print("\n✅ Configuration saved to .env file!")
    
    # Validate the new configuration
    if validate_config():
        console.print("✅ Setup completed successfully!")
        console.print("\n🚀 You can now run: python main.py chat")
    else:
        console.print("❌ Setup validation failed. Please check your configuration.")


@cli.command()
def info():
    """Display information about the agent and configuration"""
    
    display_banner()
    display_features()
    
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
    
    console.print(f"\n📖 Usage Examples:")
    examples = [
        "python main.py chat                    # Start interactive chat",
        "python main.py chat --async-mode       # Use async interface", 
        "python main.py chat --model gpt-3.5-turbo  # Use different model",
        "python main.py ask 'Hello, how are you?'   # Single question",
        "python main.py setup                   # Configure the application",
    ]
    
    for example in examples:
        console.print(f"  {example}", style="dim")


@cli.command() 
def test():
    """Test the agent with a simple interaction"""
    
    console.print("🧪 Testing agent functionality...\n")
    
    try:
        agent = create_agent()
        
        console.print(f"✅ Agent created: {agent.config.agent_name}")
        console.print(f"✅ Model: {agent.config.openai_model}")
        
        # Test a simple interaction
        test_message = "Hello! Please respond with 'Agent is working correctly.'"
        console.print(f"\n📤 Test message: {test_message}")
        
        response = agent.chat(test_message, stream=False)
        console.print(f"📥 Response: {response}")
        
        # Check history
        stats = agent.get_history_summary()
        console.print(f"\n📊 History: {stats['total_messages']} messages")
        
        console.print("\n✅ Test completed successfully!")
        
    except Exception as e:
        console.print(f"❌ Test failed: {str(e)}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    cli()
