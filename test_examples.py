#!/usr/bin/env python3
"""
Test script to validate the MCP server works with pysimplicityhl examples
"""

import asyncio
import sys
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_example(session, name: str, source_file: str, witness_file: str):
    """Test a single example"""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    
    # Read files
    source_code = Path(source_file).read_text()
    witness_data = Path(witness_file).read_text() if Path(witness_file).exists() else ""
    
    print(f"\n[Source] {len(source_code)} chars:")
    print(source_code[:200] + "..." if len(source_code) > 200 else source_code)
    
    if witness_data:
        print(f"\n[Witness] {len(witness_data)} chars:")
        print(witness_data[:100] + "..." if len(witness_data) > 100 else witness_data)
    
    # Call compilation
    try:
        result = await session.call_tool(
            "compile_simplicity",
            arguments={
                "source_code": source_code,
                "witness_data": witness_data
            }
        )
        
        content = result.content[0].text if result.content else "No content"
        # Remove unicode for Windows
        content_safe = content.encode('ascii', 'ignore').decode('ascii')
        print(f"\n[Result]:")
        print(content_safe)
        
        return "Compilation successful!" in content_safe
        
    except Exception as e:
        print(f"\n[Error] {e}")
        return False

async def main():
    """Run all example tests"""
    
    # Check if we should use docker or local
    use_docker = "--docker" in sys.argv
    
    if use_docker:
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcp-simplicity-server", "python", "server.py"]
        )
    else:
        # Run server locally
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"]
        )
    
    print("Starting MCP Server tests...")
    print(f"Mode: {'Docker' if use_docker else 'Local'}")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n[OK] Server initialized!")
            
            # Test getting pysimplicityhl info
            print("\n" + "="*60)
            print("Getting pysimplicityhl info...")
            print("="*60)
            
            try:
                info = await session.call_tool("get_pysimplicityhl_info", arguments={})
                print(info.content[0].text if info.content else "No info")
            except Exception as e:
                print(f"[Error] Could not get info: {e}")
            
            # Define test cases
            examples = [
                ("Arithmetic", "examples/arithmetic.simf", "examples/arithmetic.wit"),
                ("Scoping", "examples/scoping.simf", "examples/scoping.wit"),
                ("Witness Equality", "examples/witness_equality.simf", "examples/witness_equality.wit"),
                ("Witness Computation", "examples/witness_computation.simf", "examples/witness_computation.wit"),
            ]
            
            results = {}
            for name, source, witness in examples:
                success = await test_example(session, name, source, witness)
                results[name] = success
            
            # Summary
            print("\n" + "="*60)
            print("TEST SUMMARY")
            print("="*60)
            
            for name, success in results.items():
                status = "[PASS]" if success else "[FAIL]"
                print(f"{status}: {name}")
            
            total = len(results)
            passed = sum(results.values())
            print(f"\nTotal: {passed}/{total} passed")
            
            if passed == total:
                print("\n[SUCCESS] All tests passed!")
                return 0
            else:
                print(f"\n[Warning] {total - passed} test(s) failed")
                return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
