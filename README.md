# SSE-based MCP Client for [MCP](https://modelcontextprotocol.io/introduction)

A LangChain-compatible MCP client that connects to SSE-based MCP servers with intelligent tool selection and conversation memory.

## Quick Start

**Prerequisites**: Set `OPENAI_API_KEY` in your environment or `.env` file.

### Local Usage

```bash
# Interactive chat mode
uv run simple_client.py https://web-production-b40eb.up.railway.app/sse

# Single query
uv run simple_client.py https://web-production-b40eb.up.railway.app/sse "What's the weather in New York?"
```

### LangChain Platform

The client is ready for LangChain platform deployment with built-in tracing and monitoring.

**Required Environment Variables:**
```bash
OPENAI_API_KEY=your_openai_api_key_here
LANGCHAIN_API_KEY=your_langchain_api_key_here
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=mcp-sse-client
MCP_SERVER_URL=https://web-production-b40eb.up.railway.app/sse
```

**Python Requirements:** Python 3.11+ (compatible with LangChain platform)

## Features

- **LangChain Integration**: MCP tools automatically wrapped as LangChain tools
- **Intelligent Agents**: Uses LangChain agents for smart tool selection
- **Conversation Memory**: Maintains chat history across interactions
- **Interactive Chat**: Built-in chat interface with tool usage
- **Error Handling**: Robust error handling and tool execution
- **Platform Ready**: Ready for LangChain platform deployment

## Architecture

This client demonstrates how MCP servers can be decoupled processes that agents connect to via SSE, enabling cloud-native deployments where clients and servers run independently.