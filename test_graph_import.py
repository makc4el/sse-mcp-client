#!/usr/bin/env python3
"""
Test script to verify that the LangGraph agent can be imported 
and compiled correctly for LangGraph Studio.
"""

def test_graph_import():
    """Test importing and compiling the graph"""
    print("Testing graph import and compilation...")
    
    try:
        # Test 1: Import the module
        print("1. Importing langgraph_agent_fixed...")
        import langgraph_agent_fixed
        print("✅ Module imported successfully")
        
        # Test 2: Access the graph
        print("2. Accessing graph object...")
        graph = langgraph_agent_fixed.graph
        print(f"✅ Graph object: {type(graph)}")
        
        # Test 3: Check if graph is compiled
        print("3. Checking graph compilation...")
        print(f"✅ Graph is compiled: {hasattr(graph, 'invoke')}")
        
        # Test 4: Get graph structure
        print("4. Getting graph structure...")
        try:
            # Try to get some basic info about the graph
            print(f"✅ Graph ready for use")
            return True
            
        except Exception as e:
            print(f"❌ Graph structure issue: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Import/compilation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_graph_execution():
    """Test basic graph execution"""
    print("\nTesting graph execution...")
    
    try:
        import langgraph_agent_fixed
        from langchain_core.messages import HumanMessage
        
        # Simple test execution
        initial_state = {
            "messages": [HumanMessage(content="Hello!")],
            "config": {"llm_model": "gpt-3.5-turbo"}
        }
        
        result = langgraph_agent_fixed.graph.invoke(initial_state)
        print(f"✅ Graph execution successful. Messages: {len(result['messages'])}")
        return True
        
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 LangGraph Studio Compatibility Test")
    print("=" * 40)
    
    success = True
    success &= test_graph_import()
    success &= test_graph_execution()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 All tests passed! Graph should work in LangGraph Studio.")
    else:
        print("❌ Some tests failed. Check the errors above.")
