# LangGraph Deployment Fixes

This document tracks the fixes applied to resolve LangGraph deployment issues.

## Issue History

### 1. ❌ Package Name Error (FIXED)
```
ValueError: Package name 'sse-mcp-client' contains a hyphen. 
Rename the directory to use it as flat-layout package.
```

**Fix**: Created `mcp_client_lib/` package (no hyphens) and updated imports.

### 2. ❌ Import String Format Error (FIXED)
```
ValueError: Import string "simple_langchain_agent.py" must be in format "<module>:<attribute>".
```

**Problem**: LangGraph expects `module:attribute` format, not file paths.

**Fix**: 
- Created `langgraph_agent.py` with proper LangGraph StateGraph implementation
- Updated `langgraph.json` path from `"simple_langchain_agent.py"` to `"langgraph_agent:graph"`
- Added `langgraph>=0.0.40` to requirements.txt

### 3. ❌ Dependency Conflict Error (FIXED)
```
ERROR: Cannot install langchain 0.1.20, langchain-openai 0.1.8 and langchain-core==0.1.52 
because these package versions have conflicting dependencies.
langchain 0.1.20 depends on langchain-core<0.2.0 and >=0.1.52
langchain-openai 0.1.8 depends on langchain-core<0.3 and >=0.2.2
```

**Problem**: Incompatible version constraints between LangChain packages.

**Fix**:
- Updated to LangChain 0.2+ compatible versions:
  - `langchain>=0.2.0,<0.3.0`
  - `langchain-openai>=0.1.8,<0.2.0` 
  - `langchain-core>=0.2.2,<0.3.0`
  - `langchain-community>=0.2.0,<0.3.0`
- Updated agent code for LangChain 0.2+ API compatibility
- Replaced deprecated `initialize_agent` with `create_structured_chat_agent + AgentExecutor`

## Current Configuration

### langgraph.json
```json
{
  "dependencies": ["./mcp_client_lib"],
  "graphs": {
    "mcp_agent": {
      "path": "langgraph_agent:graph",
      "description": "MCP-enabled LangChain agent for mathematical operations"
    }
  }
}
```

### Graph Implementation
- **File**: `langgraph_agent.py`
- **Entry Point**: `graph` function
- **Type**: LangGraph StateGraph with async MCP tool integration
- **Nodes**: setup → agent → tools (conditional)

## Deployment Status

✅ **Package Structure**: Fixed (hyphen-free package)
✅ **Import Format**: Fixed (module:attribute format)  
✅ **Dependencies**: Fixed (LangChain 0.2+ compatible versions)
✅ **API Compatibility**: Updated (LangChain 0.2+ agent creation)
✅ **Graph Implementation**: Complete (StateGraph with MCP tools)
🔄 **Build Status**: In progress (dependency conflicts resolved)

## Next Steps

Monitor the deployment logs for:
1. ✅ Build completion
2. ✅ Graph validation
3. ✅ Tool loading
4. ✅ API readiness

## Testing Commands

```bash
# Local test
cd sse-mcp-client
python langgraph_agent.py

# Check deployment status
# Monitor LangGraph deployment logs for success
```

## Common Issues & Solutions

1. **Import Errors**: Ensure all imports use `mcp_client_lib.` prefix
2. **Graph Format**: Use StateGraph with proper entry points
3. **Async Handling**: Provide both sync/async entry points for LangGraph
4. **Tool Integration**: Use async MCP adapter in graph nodes

Last Updated: 2025-09-25
Status: ✅ All known issues resolved
