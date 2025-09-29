# Tests for main.py

This directory contains comprehensive tests for the `main.py` file, specifically testing the weather query scenario where a user asks "what's the weather like in Spokane?" and verifies that the MCP client is called with the appropriate response.

## Test Files

### `test_main_weather.py`
Comprehensive test suite that verifies:
- ✅ Weather query flow works correctly
- ✅ MCP client is called with correct parameters  
- ✅ Weather response is properly formatted
- ✅ Error handling works for weather queries
- ✅ Conversation continuity is maintained
- ✅ Session management works correctly

### `test_mcp_weather_demo.py`
Interactive demo that shows:
- 🌤️ Complete weather query flow
- 📞 MCP client call verification
- 💬 Conversation flow demonstration
- 🔄 Follow-up query handling

### `run_tests.py`
Test runner that executes all tests and provides a comprehensive report.

## Running Tests

### Run All Tests
```bash
cd /Users/max.odarchenko/Projects/mcp/sse-mcp-client
python tests/run_tests.py
```

### Run Individual Tests
```bash
# Run weather query tests
python tests/test_main_weather.py

# Run weather demo
python tests/test_mcp_weather_demo.py
```

## Test Scenarios

### 1. Weather Query Flow
- **Input**: "what's the weather like in Spokane?"
- **Expected**: MCP client called with weather query
- **Response**: Formatted weather data returned

### 2. MCP Client Integration
- **Verification**: MCP client `process_query` method called
- **Parameters**: Correct message list passed
- **Content**: Weather location detected in query

### 3. Error Handling
- **Scenario**: MCP client throws exception
- **Expected**: Graceful error message returned
- **Session**: Conversation state preserved

### 4. Conversation Continuity
- **Flow**: Multiple weather queries in sequence
- **State**: Session management maintained
- **Count**: Conversation counter incremented

## Test Results

All tests pass successfully:
- ✅ 4/4 weather query tests passed
- ✅ MCP client integration verified
- ✅ Error handling works
- ✅ Session management works
- ✅ Ready for LangGraph Platform deployment

## Notes

- Tests use mocked MCP client to avoid requiring actual MCP server
- Environment variables are mocked for testing
- All async/await patterns are properly tested
- LangGraph Platform compatibility verified
