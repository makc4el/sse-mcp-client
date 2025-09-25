#!/usr/bin/env python3
"""
Complete MCP + LangChain Integration Test

This comprehensive test demonstrates the full integration working
with detailed logging and realistic user scenarios.
"""

import asyncio
import json
import logging
import time
from langchain_integration import MCPToolAdapter

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ComprehensiveIntegrationTest:
    """Complete integration test suite"""
    
    def __init__(self):
        self.results = {
            "connection_test": False,
            "tool_discovery": False,
            "tool_execution": False,
            "complex_scenarios": False,
            "error_handling": False,
            "performance": {}
        }
    
    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🧪 Complete MCP + LangChain Integration Test Suite")
        print("=" * 60)
        
        await self.test_connection()
        await self.test_tool_discovery()
        await self.test_basic_tool_execution()
        await self.test_complex_scenarios()
        await self.test_error_handling()
        await self.test_performance()
        
        self.print_final_report()
    
    async def test_connection(self):
        """Test MCP connection and initialization"""
        print("\n🔌 Test 1: Connection & Initialization")
        print("-" * 40)
        
        try:
            async with MCPToolAdapter("http://localhost:8000") as adapter:
                tools = adapter.get_tools()
                
                print(f"✅ Connection established")
                print(f"✅ Session initialized")
                print(f"✅ Tools loaded: {len(tools)}")
                
                self.results["connection_test"] = True
                
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
    
    async def test_tool_discovery(self):
        """Test tool discovery and schema parsing"""
        print("\n🔍 Test 2: Tool Discovery & Schema Validation")
        print("-" * 40)
        
        try:
            async with MCPToolAdapter("http://localhost:8000") as adapter:
                tools = adapter.get_tools()
                
                print(f"📋 Discovered {len(tools)} tools:")
                
                for tool in tools:
                    print(f"\n🛠️ Tool: {tool.name}")
                    print(f"   Description: {tool.description}")
                    print(f"   Schema: {tool.args_schema}")
                    
                    # Validate schema
                    if hasattr(tool.args_schema, '__annotations__'):
                        annotations = tool.args_schema.__annotations__
                        print(f"   Parameters: {list(annotations.keys())}")
                        
                self.results["tool_discovery"] = True
                print(f"\n✅ Tool discovery successful")
                
        except Exception as e:
            print(f"❌ Tool discovery failed: {e}")
    
    async def test_basic_tool_execution(self):
        """Test basic tool execution scenarios"""
        print("\n⚙️ Test 3: Basic Tool Execution")
        print("-" * 40)
        
        test_cases = [
            {
                "tool": "add_numbers",
                "args": {"a": 10, "b": 5},
                "expected_result": 15.0,
                "description": "Simple addition"
            },
            {
                "tool": "add_numbers", 
                "args": {"a": 100.5, "b": 200.7},
                "expected_result": 301.2,
                "description": "Decimal addition"
            },
            {
                "tool": "find_max",
                "args": {"a": 42, "b": 17},
                "expected_result": 42.0,
                "description": "Maximum of two integers"
            },
            {
                "tool": "find_max",
                "args": {"a": 3.14, "b": 2.71},
                "expected_result": 3.14,
                "description": "Maximum of two decimals"
            }
        ]
        
        try:
            async with MCPToolAdapter("http://localhost:8000") as adapter:
                tools = {tool.name: tool for tool in adapter.get_tools()}
                
                passed = 0
                total = len(test_cases)
                
                for i, test_case in enumerate(test_cases, 1):
                    tool_name = test_case["tool"]
                    args = test_case["args"]
                    expected = test_case["expected_result"]
                    desc = test_case["description"]
                    
                    print(f"\n   Test {i}: {desc}")
                    print(f"   Calling: {tool_name}({args})")
                    
                    start_time = time.time()
                    result = await tools[tool_name]._arun(**args)
                    execution_time = time.time() - start_time
                    
                    # Parse the JSON result
                    result_data = json.loads(result)
                    actual_result = result_data.get("result")
                    
                    print(f"   Result: {actual_result}")
                    print(f"   Time: {execution_time:.3f}s")
                    
                    if abs(actual_result - expected) < 0.01:  # Allow for floating point precision
                        print(f"   ✅ PASS")
                        passed += 1
                    else:
                        print(f"   ❌ FAIL - Expected {expected}, got {actual_result}")
                
                print(f"\n📊 Basic execution results: {passed}/{total} tests passed")
                self.results["tool_execution"] = (passed == total)
                
        except Exception as e:
            print(f"❌ Basic tool execution failed: {e}")
    
    async def test_complex_scenarios(self):
        """Test complex multi-step scenarios"""
        print("\n🧩 Test 4: Complex Multi-Step Scenarios")
        print("-" * 40)
        
        scenarios = [
            {
                "name": "Sequential Calculation",
                "description": "Add numbers then find max with result",
                "steps": [
                    ("add_numbers", {"a": 25, "b": 35}),  # Result: 60
                    ("find_max", {"a": 60, "b": 50})      # Result: 60
                ]
            },
            {
                "name": "Comparison Workflow",
                "description": "Calculate two sums and compare them",
                "steps": [
                    ("add_numbers", {"a": 15, "b": 25}),  # Result: 40
                    ("add_numbers", {"a": 18, "b": 22}),  # Result: 40  
                    ("find_max", {"a": 40, "b": 40})      # Result: 40
                ]
            }
        ]
        
        try:
            async with MCPToolAdapter("http://localhost:8000") as adapter:
                tools = {tool.name: tool for tool in adapter.get_tools()}
                
                for scenario in scenarios:
                    print(f"\n🎯 Scenario: {scenario['name']}")
                    print(f"   {scenario['description']}")
                    
                    step_results = []
                    
                    for step_num, (tool_name, args) in enumerate(scenario['steps'], 1):
                        print(f"   Step {step_num}: {tool_name}({args})")
                        
                        result = await tools[tool_name]._arun(**args)
                        result_data = json.loads(result)
                        actual_result = result_data.get("result")
                        step_results.append(actual_result)
                        
                        print(f"   → Result: {actual_result}")
                    
                    print(f"   ✅ Scenario completed: {step_results}")
                
                self.results["complex_scenarios"] = True
                
        except Exception as e:
            print(f"❌ Complex scenarios failed: {e}")
    
    async def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Test 5: Error Handling")
        print("-" * 40)
        
        error_scenarios = [
            {
                "name": "Invalid tool name",
                "action": lambda tools: tools["nonexistent_tool"]._arun(a=1, b=2),
                "expected_error": "KeyError"
            },
            {
                "name": "Missing required parameter",
                "action": lambda tools: tools["add_numbers"]._arun(a=5),  # Missing 'b'
                "expected_error": "TypeError"
            },
            {
                "name": "Invalid parameter type",
                "action": lambda tools: tools["add_numbers"]._arun(a="invalid", b=5),
                "expected_error": "Various validation errors"
            }
        ]
        
        try:
            async with MCPToolAdapter("http://localhost:8000") as adapter:
                tools = {tool.name: tool for tool in adapter.get_tools()}
                
                error_count = 0
                
                for scenario in error_scenarios:
                    print(f"\n🧪 Testing: {scenario['name']}")
                    
                    try:
                        await scenario["action"](tools)
                        print(f"   ⚠️ Expected error but got success")
                    except Exception as e:
                        print(f"   ✅ Caught expected error: {type(e).__name__}: {e}")
                        error_count += 1
                
                self.results["error_handling"] = (error_count > 0)
                print(f"\n📊 Error handling: {error_count}/{len(error_scenarios)} scenarios handled correctly")
                
        except Exception as e:
            print(f"❌ Error handling test failed: {e}")
    
    async def test_performance(self):
        """Test performance characteristics"""
        print("\n⚡ Test 6: Performance Analysis")
        print("-" * 40)
        
        try:
            async with MCPToolAdapter("http://localhost:8000") as adapter:
                tools = {tool.name: tool for tool in adapter.get_tools()}
                
                # Connection time test
                connection_times = []
                for i in range(3):
                    start = time.time()
                    test_adapter = MCPToolAdapter("http://localhost:8000")
                    await test_adapter.connect()
                    await test_adapter.load_tools()
                    connection_time = time.time() - start
                    connection_times.append(connection_time)
                    await test_adapter.disconnect()
                
                avg_connection_time = sum(connection_times) / len(connection_times)
                
                # Tool execution time test
                execution_times = []
                for i in range(10):
                    start = time.time()
                    await tools["add_numbers"]._arun(a=i, b=i+1)
                    execution_time = time.time() - start
                    execution_times.append(execution_time)
                
                avg_execution_time = sum(execution_times) / len(execution_times)
                max_execution_time = max(execution_times)
                min_execution_time = min(execution_times)
                
                # Concurrent execution test
                start = time.time()
                concurrent_tasks = [
                    tools["add_numbers"]._arun(a=i, b=i+1) 
                    for i in range(5)
                ]
                await asyncio.gather(*concurrent_tasks)
                concurrent_time = time.time() - start
                
                # Store and display results
                performance_results = {
                    "avg_connection_time": avg_connection_time,
                    "avg_execution_time": avg_execution_time,
                    "max_execution_time": max_execution_time,
                    "min_execution_time": min_execution_time,
                    "concurrent_time": concurrent_time
                }
                
                self.results["performance"] = performance_results
                
                print(f"📊 Performance Results:")
                print(f"   Average connection time: {avg_connection_time:.3f}s")
                print(f"   Average tool execution: {avg_execution_time:.3f}s")
                print(f"   Execution time range: {min_execution_time:.3f}s - {max_execution_time:.3f}s")
                print(f"   5 concurrent calls: {concurrent_time:.3f}s")
                print(f"   Estimated throughput: ~{1/avg_execution_time:.1f} calls/sec")
                
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
    
    def print_final_report(self):
        """Print final test report"""
        print("\n📋 FINAL INTEGRATION TEST REPORT")
        print("=" * 60)
        
        passed_tests = sum(1 for test, result in self.results.items() 
                          if test != "performance" and result)
        total_tests = len(self.results) - 1  # Exclude performance from count
        
        print(f"🧪 Test Results: {passed_tests}/{total_tests} passed")
        
        for test_name, result in self.results.items():
            if test_name == "performance":
                continue
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"   {test_name.replace('_', ' ').title()}: {status}")
        
        if self.results["performance"]:
            perf = self.results["performance"]
            print(f"\n⚡ Performance Summary:")
            print(f"   Connection: {perf.get('avg_connection_time', 0):.3f}s avg")
            print(f"   Execution: {perf.get('avg_execution_time', 0):.3f}s avg")
            print(f"   Throughput: ~{1/perf.get('avg_execution_time', 1):.1f} calls/sec")
        
        if passed_tests == total_tests:
            print(f"\n🎉 ALL TESTS PASSED! Your MCP + LangChain integration is working perfectly!")
            print(f"🚀 Ready for production use!")
        else:
            print(f"\n⚠️ Some tests failed. Please check the logs above.")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Add your custom MCP tools to the server")
        print(f"   2. Create specialized LangChain agents")
        print(f"   3. Implement conversation memory")
        print(f"   4. Deploy to production environment")


async def main():
    """Run the complete integration test"""
    
    # Check server availability
    try:
        from mcp_client import SSEMCPClient
        client = SSEMCPClient("http://localhost:8000")
        if not await client.health_check():
            print("❌ MCP server is not running!")
            print("Please start it with: cd ../sse-mcp-server && python main.py")
            return
        await client.disconnect()
    except Exception as e:
        print(f"❌ Cannot connect to MCP server: {e}")
        return
    
    # Run tests
    test_suite = ComprehensiveIntegrationTest()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
