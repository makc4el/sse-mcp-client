# LangChain + MCP Integration Setup

This guide explains how to use the SSE MCP client with LangChain agents.

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LangChain     │    │   MCP Client    │    │   MCP Server    │
│     Agent       │───▶│   Integration   │───▶│   (Your Tools)  │
│                 │    │                 │    │                 │
│ • OpenAI/etc    │    │ • Tool Wrapper  │    │ • add_numbers   │
│ • ReAct         │    │ • SSE Transport │    │ • find_max      │
│ • Tool Calling  │    │ • Async Support │    │ • Custom Tools  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📦 Installation

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up OpenAI API key** (for LLM):
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

## 🚀 Quick Start

### Option 1: Use the Integration (Recommended)

```python
from langchain_integration import MCPToolAdapter
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI

# Create MCP tool adapter
async with MCPToolAdapter("http://localhost:8000") as adapter:
    tools = adapter.get_tools()
    
    # Create LangChain agent
    llm = ChatOpenAI(model="gpt-3.5-turbo")
    agent = create_react_agent(llm, tools, prompt)
    
    # Execute queries
    executor = AgentExecutor(agent=agent, tools=tools)
    result = await executor.ainvoke({"input": "What is 25 + 37?"})
```

### Option 2: Use the Complete Example

```python
from langchain_agent_example import MCPLangChainAgent

agent = MCPLangChainAgent("http://localhost:8000")
await agent.initialize()

result = await agent.run("Find the maximum of 42 and 17")
print(result)
```

## 🧪 Running Examples

### 1. Start the MCP Server
```bash
cd ../sse-mcp-server
python main.py
```

### 2. Run the LangChain Demo
```bash
python langchain_agent_example.py
```

Choose from:
- **Option 1**: Direct MCP tools (no LLM required)
- **Option 2**: Basic agent demo (requires OpenAI API key)
- **Option 3**: Interactive mode (requires OpenAI API key)

## 🔧 Integration Approaches

### Approach 1: Repository Combination (Recommended)

**Structure:**
```
your-ai-project/
├── mcp_client/          # MCP client code
├── langchain_integration/# LangChain wrappers
├── agents/              # Your AI agents
├── requirements.txt     # Combined dependencies
└── main.py             # Your application
```

**Pros:**
- ✅ Single codebase
- ✅ Easy to maintain
- ✅ Simple deployment
- ✅ Shared configuration

**Cons:**
- ❌ Larger repository
- ❌ Mixed concerns

### Approach 2: Microservices Architecture

**Structure:**
```
mcp-server/         # Your MCP tools
mcp-client/         # Standalone MCP client
ai-agent-service/   # LangChain agents
api-gateway/        # Route requests
```

**Pros:**
- ✅ Separation of concerns
- ✅ Independent scaling
- ✅ Technology flexibility

**Cons:**
- ❌ More complex deployment
- ❌ Network overhead
- ❌ Service coordination

### Approach 3: Official LangChain MCP Adapters (Future)

```python
# When available:
from langchain_mcp_adapters import MultiServerMCPClient

client = MultiServerMCPClient([
    {"url": "http://localhost:8000", "transport": "sse"}
])
tools = client.get_tools()
```

## 🏗️ Recommended Project Structure

For most use cases, we recommend **Approach 1** - combining repositories:

```
your-ai-project/
├── src/
│   ├── mcp/
│   │   ├── __init__.py
│   │   ├── client.py          # MCP client
│   │   └── langchain_tools.py # LangChain integration
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── math_agent.py      # Your agents
│   │   └── base_agent.py
│   └── config/
│       ├── __init__.py
│       └── settings.py
├── tests/
├── requirements.txt
├── README.md
└── main.py
```

## 🔌 Extending the Integration

### Adding Custom MCP Tools

1. **Add tools to your MCP server:**
```python
# In your MCP server
TOOLS.append(Tool(
    name="your_custom_tool",
    description="Your tool description",
    inputSchema={...}
))
```

2. **Tools automatically become available in LangChain:**
```python
# No code changes needed!
# The integration automatically discovers new tools
```

### Customizing Tool Behavior

```python
class CustomMCPToolWrapper(MCPToolWrapper):
    """Custom wrapper with additional functionality"""
    
    async def _arun(self, **kwargs):
        # Add pre-processing
        kwargs = self.preprocess_args(kwargs)
        
        # Call parent
        result = await super()._arun(**kwargs)
        
        # Add post-processing
        return self.postprocess_result(result)
```

## 🐛 Troubleshooting

### Common Issues

**1. "Cannot connect to MCP server"**
- Ensure MCP server is running: `curl http://localhost:8000/health`
- Check server logs for errors

**2. "No tools found"**
- Verify server has tools: `curl http://localhost:8000/`
- Check MCP client logs

**3. "OpenAI API errors"**
- Set `OPENAI_API_KEY` environment variable
- Check API key permissions
- Verify sufficient credits

**4. "Tool schema errors"**
- Check MCP tool input schemas
- Ensure required parameters are provided

### Debug Mode

Enable verbose logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 Production Considerations

### Performance
- Use connection pooling for MCP clients
- Cache tool schemas
- Implement request rate limiting

### Reliability
- Add retry logic for MCP calls
- Implement circuit breakers
- Monitor tool execution times

### Security
- Validate all tool inputs
- Implement authentication for MCP server
- Use HTTPS in production

### Monitoring
- Log all tool executions
- Track success/failure rates
- Monitor response times

## 📚 Next Steps

1. **Explore advanced agent patterns**: Multi-agent systems, tool chaining
2. **Add more MCP tools**: Database access, API integrations, file operations
3. **Implement custom prompts**: Specialized agent behaviors
4. **Add memory**: Conversation history, context persistence
5. **Deploy to production**: Containerization, scaling, monitoring
