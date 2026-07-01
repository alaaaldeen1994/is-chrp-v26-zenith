import sys
import os
import json

# Reconfigure stdout to UTF-8
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

# Add SDK and config directories to path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sdks", "python"))
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config"))

# Set local server connection
os.environ["ZENITH_API_KEY"] = "zk_live_c43349c9f8f86cd9df05dcf8e45bcff0"
os.environ["ZENITH_API_URL"] = "http://127.0.0.1:9999/api/v1"

def test_langchain():
    print("=" * 70)
    print("      LANGCHAIN TOOL WRAPPERS - END-TO-END VERIFICATION")
    print("=" * 70)
    
    try:
        from langchain_examples import safety_audit_tool, lnp_optimization_tool
        print("[OK] Import LangChain examples: SUCCESS")
    except Exception as e:
        print(f"[ERROR] Import LangChain tools failed: {e}")
        return False

    # 1. Test LangChain tool description
    print("\n[STEP 1] Inspecting LangChain tools...")
    print("  - Tool Name:       ", safety_audit_tool.name)
    print("  - Tool Description:", safety_audit_tool.description)
    print("  - Tool Args Schema:", safety_audit_tool.args)

    # 2. Execute LangChain tool call (calls live API)
    print("\n[STEP 2] Executing LangChain safety_audit_tool.invoke()...")
    try:
        res = safety_audit_tool.invoke({"factors": ["GATA4", "OCT4"]})
        print("  [OK] Tool output:")
        print(f"    {res}")
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        return False
        
    return True

def test_llamaindex():
    print("\n" + "=" * 70)
    print("      LLAMAINDEX TOOL WRAPPERS - END-TO-END VERIFICATION")
    print("=" * 70)
    
    try:
        from llamaindex_examples import safety_tool, lnp_tool
        print("[OK] Import LlamaIndex examples: SUCCESS")
    except Exception as e:
        print(f"[ERROR] Import LlamaIndex tools failed: {e}")
        return False

    # 1. Test LlamaIndex tool description
    print("\n[STEP 1] Inspecting LlamaIndex tools...")
    print("  - Tool Name:       ", safety_tool.metadata.name)
    print("  - Tool Description:", safety_tool.metadata.description)
    print("  - Tool Args Schema:", safety_tool.metadata.get_parameters_dict())

    # 2. Execute LlamaIndex tool call (calls live API)
    print("\n[STEP 2] Executing LlamaIndex safety_tool.call()...")
    try:
        res = safety_tool.call(factors=["GATA4", "OCT4"])
        print("  [OK] Tool output:")
        print(f"    {res}")
    except Exception as e:
        print(f"  [ERROR] Execution failed: {e}")
        return False
        
    return True

if __name__ == "__main__":
    lc_ok = test_langchain()
    li_ok = test_llamaindex()
    if lc_ok and li_ok:
        print("\n" + "=" * 70)
        print("   [SUCCESS] ALL AGENT FRAMEWORK WRAPPERS VERIFIED SUCCESSFULLY!")
        print("=" * 70)
    else:
        sys.exit(1)
