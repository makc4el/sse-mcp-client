# 🤖 OpenAI LangChain Agent

A fully compatible LangChain AI agent with OpenAI LLM integration, providing conversational AI capabilities with streaming responses, memory management, and rich interactive interfaces.

## ✨ Features

- 🔗 **Full LangChain Compatibility** - Built on LangChain for maximum ecosystem integration
- 🧠 **OpenAI GPT Integration** - Supports GPT-4, GPT-3.5-turbo, and other OpenAI models
- ⚡ **Real-time Streaming** - Live token-by-token response streaming
- 💭 **Conversation Memory** - Intelligent conversation history management
- 🎨 **Rich Chat Interface** - Beautiful terminal interface with syntax highlighting
- 🔄 **Async/Sync Support** - Both synchronous and asynchronous operation modes
- 📁 **Export/Import** - Save and load conversation histories
- ⚙️ **Highly Configurable** - Environment-based configuration system
- 🛠️ **CLI Tool** - Command-line interface with multiple operation modes
- 🏗️ **Production Ready** - Robust error handling and logging

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd sse-mcp-client

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Run the setup command for interactive configuration
python main.py setup

# Or manually create .env file from template
cp .env.example .env
# Edit .env with your OpenAI API key
```

Required environment variables:
- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `OPENAI_MODEL` - Model to use (default: gpt-4)

### 3. Start Chatting

```bash
# Interactive chat mode
python main.py chat

# Single question mode
python main.py ask "What is the meaning of life?"

# Test the setup
python main.py test
```

## 📖 Usage

### Interactive Chat

Start an interactive chat session:

```bash
python main.py chat
```

Available commands in chat:
- `/help` - Show help message
- `/clear` - Clear conversation history
- `/history` - Show conversation statistics
- `/export` - Export conversation to JSON
- `/config` - Show current configuration
- `/quit` or `/exit` - Exit chat

### Command Line Options

```bash
# Use different model
python main.py chat --model gpt-3.5-turbo

# Disable streaming
python main.py chat --no-stream

# Set custom temperature
python main.py chat --temperature 0.9

# Async mode
python main.py chat --async-mode

# Single question
python main.py ask "Explain quantum computing" --model gpt-4
```

### Programmatic Usage

```python
from langchain_agent import create_agent
from config import get_config

# Create agent
agent = create_agent()

# Simple chat
response = agent.chat("Hello! How can you help me?")
print(response)

# Streaming chat
agent.chat("Tell me a story", stream=True)

# Async usage
import asyncio

async def async_chat():
    response = await agent.achat("What's the weather like?")
    print(response)

asyncio.run(async_chat())

# Get LangChain runnable for advanced usage
chain = agent.get_langchain_runnable()
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `OPENAI_MODEL` | OpenAI model to use | `gpt-4` |
| `OPENAI_TEMPERATURE` | Response creativity (0.0-2.0) | `0.7` |
| `OPENAI_MAX_TOKENS` | Max response tokens | `None` |
| `AGENT_NAME` | Display name for agent | `OpenAI Assistant` |
| `SYSTEM_MESSAGE` | System prompt for agent | Default helpful assistant |
| `MAX_HISTORY_LENGTH` | Max conversation history | `20` |
| `ENABLE_STREAMING` | Enable streaming responses | `true` |
| `LANGSMITH_API_KEY` | LangSmith monitoring (optional) | - |
| `LANGSMITH_PROJECT` | LangSmith project name | `openai-langchain-agent` |

### Custom Configuration

```python
from config import AgentConfig
from langchain_agent import OpenAILangChainAgent

# Custom configuration
config = AgentConfig(
    openai_api_key="your-key",
    openai_model="gpt-3.5-turbo",
    temperature=0.5,
    agent_name="My Custom Agent",
    system_message="You are a specialized assistant for..."
)

agent = OpenAILangChainAgent(config=config)
```

## 🏗️ Architecture

### Core Components

1. **`config.py`** - Configuration management with Pydantic validation
2. **`langchain_agent.py`** - Main agent implementation with LangChain integration
3. **`chat_interface.py`** - Rich interactive chat interface
4. **`main.py`** - CLI application with multiple commands

### LangChain Integration

The agent is built as a LangChain `Runnable` chain:

```python
# The agent chain structure
chain = (
    RunnablePassthrough.assign(history=get_history)
    | ChatPromptTemplate
    | ChatOpenAI 
    | StrOutputParser()
)
```

This ensures full compatibility with:
- LangChain LCEL (LangChain Expression Language)
- LangServe for API deployment
- LangSmith for monitoring and debugging
- Other LangChain tools and integrations

## 📊 Advanced Features

### Conversation Management

```python
# Export conversation
conversation_data = agent.export_conversation()

# Import conversation
agent.import_conversation(conversation_data)

# Get conversation statistics
stats = agent.get_history_summary()
print(f"Total messages: {stats['total_messages']}")

# Clear history
agent.clear_history()
```

### Streaming Responses

```python
# Sync streaming
response = agent.chat("Tell me a story", stream=True)

# Async streaming
async for token in agent.astream("Explain AI"):
    print(token, end="", flush=True)
```

### LangChain Ecosystem Integration

```python
# Get the underlying runnable for advanced usage
runnable = agent.get_langchain_runnable()

# Use with LangServe
from langserve import add_routes
add_routes(app, runnable, path="/agent")

# Use with other LangChain tools
from langchain.memory import ConversationBufferMemory
memory = ConversationBufferMemory()
# ... integrate with existing LangChain applications
```

## 🔍 Commands Reference

### CLI Commands

| Command | Description |
|---------|-------------|
| `python main.py chat` | Start interactive chat |
| `python main.py ask <message>` | Single question mode |
| `python main.py setup` | Interactive configuration |
| `python main.py info` | Show agent information |
| `python main.py test` | Test agent functionality |

### Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history |
| `/history` | Show conversation statistics |
| `/export` | Export conversation to JSON |
| `/config` | Show current configuration |
| `/quit`, `/exit` | Exit the chat |

## 🛠️ Development

### Requirements

- Python 3.8+
- OpenAI API key
- Dependencies listed in `requirements.txt`

### Project Structure

```
sse-mcp-client/
├── main.py                 # CLI application entry point
├── langchain_agent.py      # Core agent implementation  
├── chat_interface.py       # Interactive chat interface
├── config.py               # Configuration management
├── requirements.txt        # Python dependencies
├── .env.example           # Environment template
└── README.md              # This file
```

### Testing

```bash
# Test agent functionality
python main.py test

# Test configuration
python -m config

# Test individual components
python -m langchain_agent
python -m chat_interface
```

## 🤝 LangChain Compatibility

This agent is fully compatible with the LangChain ecosystem:

- ✅ **LangChain Core** - Built on LangChain primitives
- ✅ **LCEL** - Uses LangChain Expression Language
- ✅ **LangServe** - Can be deployed as an API
- ✅ **LangSmith** - Supports monitoring and debugging
- ✅ **Memory** - Compatible with LangChain memory systems
- ✅ **Tools** - Can be extended with LangChain tools
- ✅ **Chains** - Can be composed with other chains
- ✅ **Agents** - Compatible with LangChain agent framework

## 📝 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues and questions:

1. Check the configuration with `python main.py info`
2. Test the setup with `python main.py test`
3. Review the error messages and logs
4. Ensure your OpenAI API key is valid and has sufficient credits

## 🎯 Examples

### Basic Usage

```python
# Simple chat
from langchain_agent import create_agent

agent = create_agent()
response = agent.chat("Hello!")
print(response)
```

### Advanced Integration

```python
# Integration with existing LangChain app
from langchain_agent import create_agent
from langchain.schema import Document

agent = create_agent()

# Use as part of a larger chain
def process_documents(docs):
    summaries = []
    for doc in docs:
        summary = agent.chat(f"Summarize this: {doc.page_content}")
        summaries.append(summary)
    return summaries
```

### Custom System Message

```python
# Specialized agent
from config import AgentConfig
from langchain_agent import OpenAILangChainAgent

config = AgentConfig(
    openai_api_key="your-key",
    system_message="You are a Python coding expert. Help users write better code."
)

coding_agent = OpenAILangChainAgent(config=config)
response = coding_agent.chat("How do I implement a binary search?")
```

---

🤖 **Ready to chat with your AI assistant!** Run `python main.py chat` to get started.
