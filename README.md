# SSE-based MCP Client

A standalone MCP (Model Context Protocol) client that connects to SSE-based MCP servers. This client can connect to any SSE-based MCP server and use its tools through OpenAI's API.

## Features

- **SSE-based connection**: Connects to MCP servers via Server-Sent Events
- **OpenAI integration**: Uses OpenAI's API for natural language processing and tool calling
- **Robust error handling**: Graceful handling of connection issues and cleanup
- **Interactive chat interface**: Simple command-line interface for querying

## Usage

**Note**: Make sure to supply `OPENAI_API_KEY` in `.env` or as an environment variable.

```bash
uv run client.py <SSE_MCP_SERVER_URL>
```

### Example

```bash
uv run client.py http://localhost:8080/sse
```

```
Initialized SSE client...
Listing tools...

Connected to server with tools: ['get_alerts', 'get_forecast']

MCP Client Started!
Type your queries or 'quit' to exit.

Query: whats the weather like in Spokane?

[Calling tool get_forecast with args {'latitude': 47.6587, 'longitude': -117.426}]
Based on the current forecast for Spokane:

Right now it's sunny and cold with a temperature of 37°F and ...
```

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

Set your OpenAI API key in a `.env` file:

```
OPENAI_API_KEY=your_api_key_here
```

Or export it as an environment variable:

```bash
export OPENAI_API_KEY=your_api_key_here
```