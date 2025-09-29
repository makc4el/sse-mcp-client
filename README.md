# SSE-based MCP Client with LangChain Agent

An advanced MCP (Model Context Protocol) client that connects to SSE-based MCP servers with integrated LangChain agent capabilities. This client provides intelligent conversation processing, tool integration, and LangGraph Cloud compatibility.

## Features

- **SSE-based connection**: Connects to MCP servers via Server-Sent Events
- **LangChain Agent**: Advanced AI agent with conversation memory and reasoning
- **LangGraph Cloud Integration**: Deploy and manage agents on LangGraph Cloud platform
- **OpenAI integration**: Uses OpenAI's API for natural language processing and tool calling
- **Tool Integration**: Automatically discovers and uses MCP server tools
- **Conversation Memory**: Maintains context across multiple interactions
- **Agent Management**: Built-in commands for agent status, memory management, and export
- **Robust error handling**: Graceful handling of connection issues and cleanup
- **Interactive chat interface**: Enhanced command-line interface with agent controls

## Usage

**Note**: Make sure to supply `OPENAI_API_KEY` in `.env` or as an environment variable.

### Option 1: Command Line Argument
```bash
uv run client.py <SSE_MCP_SERVER_URL>
```

### Option 2: Environment Variable (Recommended)
```bash
export MCP_SERVER_URL=http://localhost:8080/sse
uv run client.py
```

### Example

```bash
uv run client.py http://localhost:8080/sse
```

```
Initialized SSE client...
Listing tools...

Connected to server with tools: ['get_alerts', 'get_forecast']
✅ LangChain agent initialized
✅ MCP tools integrated with LangChain agent

MCP Client Started!
Type your queries or 'quit' to exit.
Special commands: 'status', 'clear', 'export', 'help'

Query: whats the weather like in Spokane?

🤖 Using LangChain agent for processing...
[Calling tool get_forecast with args {'latitude': 47.6587, 'longitude': -117.426}]
Based on the current forecast for Spokane:

Right now it's sunny and cold with a temperature of 37°F and ...
```

### Agent Management Commands

The client includes built-in commands for managing the LangChain agent:

- `status` - Show agent status and configuration
- `clear` - Clear conversation memory
- `export` - Export conversation to JSON file
- `help` - Show available commands
- `quit` - Exit the application

## How it works

This client demonstrates how to connect to SSE-based MCP servers, which allows for decoupled client-server architectures. The client can connect to any running MCP server that supports SSE transport, use its tools, and disconnect cleanly.

## Requirements

- Python 3.13+
- OpenAI API key
- An SSE-based MCP server to connect to

## Installation

```bash
uv sync
```

## Configuration

### Basic Configuration

Set your API keys and server URL in a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
MCP_SERVER_URL=http://localhost:8080/sse
```

Or export them as environment variables:

```bash
export OPENAI_API_KEY=your_api_key_here
export MCP_SERVER_URL=http://localhost:8080/sse
```

### LangChain Agent Configuration

Configure the LangChain agent with these environment variables:

```bash
# LangChain Agent Settings
LANGCHAIN_MODEL=gpt-4o
LANGCHAIN_TEMPERATURE=0.7

# LangGraph Cloud Integration (Optional)
LANGGRAPH_CLOUD_ENABLED=false
LANGGRAPH_CLOUD_API_KEY=your_langgraph_api_key
LANGGRAPH_CLOUD_DEPLOYMENT_ID=your_deployment_id
LANGGRAPH_CLOUD_BASE_URL=https://api.langgraph.cloud
```

### LangGraph Cloud Setup

To use LangGraph Cloud integration:

1. **Get API Key**: Sign up at [LangGraph Cloud](https://langchain-ai.github.io/langgraph/cloud/reference/api/api_ref.html)
2. **Create Deployment**: Deploy your agent configuration
3. **Configure Environment**:
   ```bash
   export LANGGRAPH_CLOUD_ENABLED=true
   export LANGGRAPH_CLOUD_API_KEY=your_api_key
   export LANGGRAPH_CLOUD_DEPLOYMENT_ID=your_deployment_id
   ```

### Advanced Configuration

For advanced users, you can customize the agent behavior:

```bash
# Model Configuration
LANGCHAIN_MODEL=gpt-4o
LANGCHAIN_TEMPERATURE=0.7

# LangGraph Cloud Advanced Settings
LANGGRAPH_CLOUD_MODEL=gpt-4o
LANGGRAPH_CLOUD_TEMPERATURE=0.7
LANGGRAPH_CLOUD_MAX_TOKENS=4000
LANGGRAPH_CLOUD_STREAMING=true
LANGGRAPH_CLOUD_TIMEOUT=30
LANGGRAPH_CLOUD_RETRIES=3
LANGGRAPH_CLOUD_ENVIRONMENT=development
LANGGRAPH_CLOUD_DEBUG=false
```

## LangChain Agent Features

### Conversation Memory
The agent maintains conversation context across multiple interactions, allowing for more natural and coherent conversations.

### Tool Integration
MCP server tools are automatically integrated with the LangChain agent, providing seamless access to server capabilities.

### Agent Management
Built-in commands for managing the agent:
- `status` - View agent configuration and status
- `clear` - Reset conversation memory
- `export` - Export conversation history to JSON

### LangGraph Cloud Integration
When enabled, the agent can leverage LangGraph Cloud for:
- Advanced graph-based reasoning
- Distributed processing
- Scalable deployment
- Enhanced monitoring and analytics

## Example Usage

### Basic Query
```
Query: What's the weather like in New York?

🤖 Using LangChain agent for processing...
[Calling tool get_forecast with args {'latitude': 40.7128, 'longitude': -74.0060}]
The weather in New York is currently sunny with a temperature of 72°F...
```

### Agent Status Check
```
Query: status

📊 Agent Status: {
  "enabled": true,
  "model": "gpt-4o",
  "temperature": 0.7,
  "tools_available": 2,
  "conversation_history_length": 3,
  "langgraph_cloud_enabled": false
}
```

### Conversation Export
```
Query: export

📁 Conversation exported to: conversation_20241201_143022.json
```

## Architecture

The client uses a modular architecture:

1. **MCP Client**: Handles SSE connection and tool discovery
2. **LangChain Agent**: Provides intelligent conversation processing
3. **MCP Tool Adapter**: Bridges MCP tools with LangChain agent
4. **LangGraph Cloud**: Optional cloud deployment and processing

## Development

### Adding Custom Tools
You can extend the agent with custom tools:

```python
from langchain_agent import LangChainAgent

agent = LangChainAgent()

def custom_tool(input_text: str) -> str:
    """Custom tool for processing text."""
    return f"Processed: {input_text}"

agent.add_tool("custom_tool", "Process custom text", custom_tool)
```

### LangGraph Cloud Deployment
For production deployments, you can deploy the agent to LangGraph Cloud:

```python
from langgraph_config import LangGraphCloudManager, create_deployment_config

config = LangGraphCloudManager()
deployment_config = create_deployment_config()
result = await config.deploy_graph(deployment_config)
```

### LangGraph Configuration

The project includes a properly configured `langgraph.json` file for LangGraph Cloud deployment:

```json
{
  "dependencies": ["."],
  "graphs": {
    "mcp-sse-agent": {
      "path": "client.py:create_langgraph_agent",
      "description": "MCP SSE Client with LangChain Agent",
      "config_schema": {
        "type": "object",
        "properties": {
          "model_name": {"type": "string", "default": "gpt-4o"},
          "temperature": {"type": "number", "default": 0.7},
          "max_tokens": {"type": "integer", "default": 4000},
          "memory_window": {"type": "integer", "default": 10}
        }
      }
    }
  },
  "env": ".env"
}
```

### Setup and Deployment

1. **Initial Setup**:
   ```bash
   python setup_langgraph.py
   ```

2. **Configure Environment**:
   ```bash
   cp env.template .env
   # Edit .env with your API keys
   ```

3. **Deploy to LangGraph Cloud**:
   ```bash
   python deploy_langgraph.py
   ```

4. **Test the Agent**:
   ```bash
   python example_agent.py
   ```

## Deployment Troubleshooting

If you encounter deployment issues, see [DEPLOYMENT_TROUBLESHOOTING.md](DEPLOYMENT_TROUBLESHOOTING.md) for common solutions.

### Common Issues Fixed

- ✅ **Python Version**: Updated to Python 3.11 compatibility for LangGraph Cloud
- ✅ **Dependencies**: Added missing `langchain-core` and `typing-extensions`
- ✅ **Configuration**: Added `python_version` and `image_distro` to `langgraph.json`
- ✅ **Fallback Handling**: Added error handling for missing dependencies
- ✅ **Security**: Enabled Wolfi Linux distribution for enhanced security



# LangGraph Platform AI Agent

A production-ready conversational AI agent built with LangGraph and OpenAI GPT-4o-mini, designed for seamless deployment on LangGraph Platform.

## 🚀 Features

- **Platform-Ready**: Fully compatible with LangGraph Platform deployment
- **API Integration**: RESTful API interface for prompt/response interactions
- **OpenAI GPT-4o-mini**: Latest efficient OpenAI model for optimal performance
- **Session Management**: Advanced graph with user context and session tracking
- **Production-Grade**: Clean architecture with proper error handling

## 📋 Requirements

- Python 3.11+
- OpenAI API key
- LangGraph Platform account (for cloud deployment)

## 🛠 Project Structure

```
├── main.py                 # Core agent logic and graphs
├── langgraph.json         # Platform deployment configuration
├── pyproject.toml         # Python dependencies
├── .gitignore            # Git ignore rules (includes .env)
└── README.md             # This file
```

## 🔧 Local Development

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Set Environment Variables

Create a `.env` file in the project root:

```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### 3. Test Locally

```bash
python main.py
```

## 🌐 Platform Deployment

This project is configured for one-click deployment to LangGraph Platform:

### Available Graphs

1. **agent** (`main.py:graph`)
   - Simple conversational AI agent
   - Direct prompt → response API
   - Optimal for basic use cases

2. **advanced_agent** (`main.py:advanced_graph`) 
   - Enhanced with session management
   - User ID and session ID tracking
   - Perfect for multi-user applications

### Deploy to Platform

1. **Upload Project**: Upload the entire project folder to LangGraph Platform
2. **Set Environment**: Configure `OPENAI_API_KEY` in platform environment
3. **Deploy**: Platform will automatically use `langgraph.json` configuration
4. **Access API**: Get your API endpoint for integration

## 📡 API Usage

Once deployed, the agent provides a REST API:

### Basic Request
```bash
curl -X POST "https://your-deployment-url/invoke" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "messages": [
        {
          "type": "human",
          "content": "Explain quantum computing in simple terms"
        }
      ]
    }
  }'
```

### Response Format
```json
{
  "output": {
    "messages": [
      {
        "type": "human", 
        "content": "Explain quantum computing in simple terms"
      },
      {
        "type": "ai",
        "content": "Quantum computing is a revolutionary technology that..."
      }
    ]
  }
}
```

## 🔐 Security

- ✅ `.env` files are git-ignored
- ✅ No hardcoded API keys
- ✅ Platform-managed environment variables
- ✅ Clean git history (secrets removed)

## 🎯 Platform Compatibility Checklist

- ✅ **No import-time execution**: Code doesn't run when imported
- ✅ **Proper graph exports**: `graph` and `advanced_graph` variables
- ✅ **RunnableConfig support**: Compatible with platform configuration
- ✅ **Environment variables**: Uses platform-provided `OPENAI_API_KEY`
- ✅ **Valid langgraph.json**: Proper platform configuration
- ✅ **Python 3.11**: Platform-supported Python version
- ✅ **API interface**: RESTful prompt/response workflow

## 🚀 Quick Start

1. **Clone & Setup**:
   ```bash
   git clone <your-repo>
   cd langchain_project
   pip install -e .
   ```

2. **Local Test** (optional):
   ```bash
   echo "OPENAI_API_KEY=your_key" > .env
   python main.py
   ```

3. **Deploy to Platform**:
   - Upload project folder
   - Set `OPENAI_API_KEY` environment variable
   - Deploy and get API endpoint

## 🤖 Model Information

- **Model**: OpenAI GPT-4o-mini
- **Temperature**: 0.7 (balanced creativity/consistency)
- **Context**: Conversation history maintained
- **Performance**: Optimized for production use

## 📞 Support

For issues with:
- **LangGraph Platform**: Check platform documentation
- **OpenAI API**: Verify API key and quotas
- **Local Development**: Ensure Python 3.11+ and dependencies installed

---

**Ready for LangGraph Platform deployment! 🚀**