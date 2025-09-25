"""
Interactive chat interface for the OpenAI LangChain Agent
"""
import sys
import asyncio
from typing import Optional
from datetime import datetime

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text
from rich.live import Live
from rich.table import Table
from rich.markdown import Markdown

from langchain_agent import create_agent
from config import validate_config


class ChatInterface:
    """Interactive chat interface with rich formatting"""
    
    def __init__(self, agent=None):
        self.console = Console()
        self.agent = agent or create_agent()
        self.session_start = datetime.now()
        
    def display_welcome(self):
        """Display welcome message"""
        welcome_text = f"""
# 🤖 {self.agent.config.agent_name}

Welcome to your AI assistant! I'm powered by **{self.agent.config.openai_model}** and fully integrated with LangChain.

## Available Commands:
- `/help` - Show this help message
- `/clear` - Clear conversation history  
- `/history` - Show conversation statistics
- `/export` - Export conversation to file
- `/quit` or `/exit` - Exit the chat

## Features:
- ✅ Real-time streaming responses
- ✅ Conversation memory
- ✅ LangChain compatibility
- ✅ OpenAI GPT integration

Type your message and press Enter to start chatting!
        """
        
        self.console.print(Panel(
            Markdown(welcome_text),
            title="🚀 AI Chat Assistant",
            border_style="blue"
        ))
    
    def display_help(self):
        """Display help information"""
        help_table = Table(title="Available Commands", show_header=True)
        help_table.add_column("Command", style="cyan", width=12)
        help_table.add_column("Description", style="white")
        
        commands = [
            ("/help", "Show this help message"),
            ("/clear", "Clear conversation history"),
            ("/history", "Show conversation statistics"),
            ("/export", "Export conversation to JSON file"),
            ("/config", "Show current configuration"),
            ("/quit, /exit", "Exit the chat interface"),
        ]
        
        for cmd, desc in commands:
            help_table.add_row(cmd, desc)
        
        self.console.print(help_table)
    
    def display_history_stats(self):
        """Display conversation history statistics"""
        stats = self.agent.get_history_summary()
        session_duration = datetime.now() - self.session_start
        
        stats_table = Table(title="Conversation Statistics", show_header=True)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        
        stats_table.add_row("Session Duration", str(session_duration).split('.')[0])
        stats_table.add_row("Total Messages", str(stats['total_messages']))
        stats_table.add_row("Your Messages", str(stats['human_messages']))
        stats_table.add_row("AI Responses", str(stats['ai_messages']))
        stats_table.add_row("System Messages", str(stats['system_messages']))
        
        self.console.print(stats_table)
    
    def display_config(self):
        """Display current configuration"""
        config_table = Table(title="Current Configuration", show_header=True)
        config_table.add_column("Setting", style="cyan")
        config_table.add_column("Value", style="white")
        
        config_items = [
            ("Agent Name", self.agent.config.agent_name),
            ("OpenAI Model", self.agent.config.openai_model),
            ("Temperature", str(self.agent.config.openai_temperature)),
            ("Max History", str(self.agent.config.max_history_length)),
            ("Streaming", "✅ Enabled" if self.agent.config.enable_streaming else "❌ Disabled"),
        ]
        
        for setting, value in config_items:
            config_table.add_row(setting, value)
        
        self.console.print(config_table)
    
    def export_conversation(self):
        """Export conversation to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_export_{timestamp}.json"
        
        try:
            import json
            conversation_data = {
                "session_start": self.session_start.isoformat(),
                "export_time": datetime.now().isoformat(),
                "agent_config": {
                    "model": self.agent.config.openai_model,
                    "temperature": self.agent.config.openai_temperature,
                    "agent_name": self.agent.config.agent_name
                },
                "conversation": self.agent.export_conversation()
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, indent=2, ensure_ascii=False)
            
            self.console.print(f"✅ Conversation exported to: [bold green]{filename}[/bold green]")
            
        except Exception as e:
            self.console.print(f"❌ Export failed: {str(e)}", style="red")
    
    def handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns True if it was a command, False otherwise"""
        command = user_input.lower().strip()
        
        if command in ['/quit', '/exit']:
            self.console.print("\n👋 Thanks for chatting! Goodbye!", style="yellow")
            return True
        elif command == '/help':
            self.display_help()
        elif command == '/clear':
            self.agent.clear_history()
            self.console.print("🗑️ Conversation history cleared!", style="green")
        elif command == '/history':
            self.display_history_stats()
        elif command == '/export':
            self.export_conversation()
        elif command == '/config':
            self.display_config()
        else:
            return False
        
        return True
    
    def run(self):
        """Run the interactive chat interface"""
        self.display_welcome()
        
        try:
            while True:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]", console=self.console)
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if self.handle_command(user_input):
                        if user_input.lower().strip() in ['/quit', '/exit']:
                            break
                    continue
                
                # Process regular chat message
                try:
                    self.console.print(f"\n[bold green]{self.agent.config.agent_name}[/bold green]: ", end="")
                    
                    if self.agent.config.enable_streaming:
                        # Streaming response
                        response = self.agent.chat(user_input, stream=True)
                    else:
                        # Non-streaming response
                        response = self.agent.chat(user_input, stream=False)
                        self.console.print(response)
                
                except KeyboardInterrupt:
                    self.console.print("\n\n⚠️ Response interrupted by user", style="yellow")
                    continue
                except Exception as e:
                    self.console.print(f"\n❌ Error: {str(e)}", style="red")
                    continue
        
        except KeyboardInterrupt:
            self.console.print("\n\n👋 Chat interrupted. Goodbye!", style="yellow")
        except Exception as e:
            self.console.print(f"\n💥 Unexpected error: {str(e)}", style="red")


class AsyncChatInterface(ChatInterface):
    """Async version of chat interface for advanced usage"""
    
    async def arun(self):
        """Run the async chat interface"""
        self.display_welcome()
        
        try:
            while True:
                # Get user input (this would need async input in real implementation)
                user_input = Prompt.ask("\n[bold blue]You[/bold blue]", console=self.console)
                
                if not user_input.strip():
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    if self.handle_command(user_input):
                        if user_input.lower().strip() in ['/quit', '/exit']:
                            break
                    continue
                
                # Process regular chat message asynchronously
                try:
                    self.console.print(f"\n[bold green]{self.agent.config.agent_name}[/bold green]: ", end="")
                    
                    # Async streaming response
                    full_response = ""
                    async for token in self.agent.astream(user_input):
                        self.console.print(token, end="", style="white")
                        full_response += token
                    
                    self.console.print()  # New line
                
                except KeyboardInterrupt:
                    self.console.print("\n\n⚠️ Response interrupted by user", style="yellow")
                    continue
                except Exception as e:
                    self.console.print(f"\n❌ Error: {str(e)}", style="red")
                    continue
        
        except KeyboardInterrupt:
            self.console.print("\n\n👋 Chat interrupted. Goodbye!", style="yellow")


@click.command()
@click.option('--async-mode', '-a', is_flag=True, help='Run in async mode')
@click.option('--no-stream', '-n', is_flag=True, help='Disable streaming responses')
@click.option('--model', '-m', help='Override OpenAI model')
def main(async_mode: bool, no_stream: bool, model: Optional[str]):
    """Launch the interactive chat interface"""
    
    # Validate configuration
    if not validate_config():
        click.echo("❌ Configuration validation failed. Please check your .env file.")
        sys.exit(1)
    
    # Create agent with optional model override
    agent = create_agent()
    if model:
        agent.config.openai_model = model
        # Recreate LLM with new model
        from langchain_openai import ChatOpenAI
        agent.llm = ChatOpenAI(
            model=model,
            temperature=agent.config.openai_temperature,
            max_tokens=agent.config.openai_max_tokens,
            openai_api_key=agent.config.openai_api_key,
            streaming=agent.config.enable_streaming and not no_stream
        )
    
    if no_stream:
        agent.config.enable_streaming = False
    
    # Launch interface
    if async_mode:
        interface = AsyncChatInterface(agent)
        asyncio.run(interface.arun())
    else:
        interface = ChatInterface(agent)
        interface.run()


if __name__ == "__main__":
    main()
