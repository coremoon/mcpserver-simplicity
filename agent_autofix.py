#!/usr/bin/env python3
"""
Intelligent Agent that fixes SimplicityHL compilation errors automatically
Uses an LLM to understand errors and generate fixes
"""

import asyncio
import sys
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Configure your LLM here - examples for different providers
LLM_PROVIDER = "anthropic"  # Options: "anthropic", "openai", "local"

# For Anthropic Claude
ANTHROPIC_API_KEY = None  # Set your API key or use environment variable

async def fix_code_with_llm(source_code: str, error_message: str, attempt: int) -> str:
    """
    Uses an LLM to fix the code based on the error message.
    
    This is where you integrate your preferred LLM:
    - Anthropic Claude
    - OpenAI GPT
    - Local model via Ollama
    - Any other LLM API
    """
    
    print(f"\n[Agent] Analyzing error (attempt {attempt})...")
    print(f"Error: {error_message[:200]}...")
    
    if LLM_PROVIDER == "anthropic":
        print("[Warning] Anthropic API not configured. Using rule-based fixes.")
        return apply_rule_based_fixes(source_code, error_message)
    
    elif LLM_PROVIDER == "openai":
        print("[Warning] OpenAI API not configured. Using rule-based fixes.")
        return apply_rule_based_fixes(source_code, error_message)
    
    else:
        return apply_rule_based_fixes(source_code, error_message)

def apply_rule_based_fixes(source_code: str, error_message: str) -> str:
    """
    Apply rule-based fixes based on common SimplicityHL syntax errors.
    """
    import re
    
    fixed_code = source_code
    
    # Rule 1: Add 'fn main() -> ()' wrapper if missing
    if "expected program" in error_message:
        print("[Fix] Adding 'fn main() -> ()' wrapper")
        fixed_code = f"fn main() -> () {{\n{fixed_code}\n    ()\n}}"
    if "expected EOI or item" in error_message:
        print("[Fix] Removing comments (SimplicityHL may not support // comments)")
        # Remove single-line comments
        lines = fixed_code.split('\n')
        lines = [line for line in lines if not line.strip().startswith('//')]
        fixed_code = '\n'.join(lines)
    
    # Rule 2: Remove fn main() wrapper - SimplicityHL is top-level
    if "fn main()" in fixed_code or "fn main (" in fixed_code:
        print("[Fix] Removing fn main() wrapper (not needed in SimplicityHL)")
        fixed_code = re.sub(
            r'fn\s+main\s*\(\s*\)\s*\{(.*)\}',
            r'\1',
            fixed_code,
            flags=re.DOTALL
        )
        # Clean up indentation
        lines = fixed_code.split('\n')
        lines = [line[4:] if line.startswith('    ') else line for line in lines]
        fixed_code = '\n'.join(lines)
    
    # Rule 3: Remove incorrect tuple patterns
    if "let (" in fixed_code and ",)" in fixed_code:
        print("[Fix] Removing incorrect tuple patterns")
        fixed_code = re.sub(r'let\s+\((\w+),\)\s*=', r'let \1 =', fixed_code)
    
    return fixed_code.strip() + '\n'

async def compile_and_fix(
    session: ClientSession,
    source_code: str,
    witness_data: str,
    max_attempts: int = 5,
    use_llm: bool = False
) -> tuple[bool, str, list]:
    """
    Attempts to compile code and automatically fix errors.
    """
    
    current_code = source_code
    attempts_history = []
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n{'='*60}")
        print(f"[Attempt {attempt}/{max_attempts}]")
        print(f"{'='*60}")
        
        # Try to compile
        result = await session.call_tool(
            "compile_simplicity",
            arguments={
                "source_code": current_code,
                "witness_data": witness_data
            }
        )
        
        content = result.content[0].text if result.content else ""
        
        # Remove unicode for Windows compatibility
        content_safe = content.encode('ascii', 'ignore').decode('ascii')
        
        # Store attempt
        attempts_history.append({
            "attempt": attempt,
            "code": current_code,
            "success": "Compilation successful!" in content_safe,
            "result": content_safe[:500]
        })
        
        # Check if successful
        if "Compilation successful!" in content_safe:
            print("\n[SUCCESS] Code compiled successfully!")
            return True, current_code, attempts_history
        
        # Extract error message
        error_msg = content_safe
        if "message" in content_safe:
            try:
                json_start = content_safe.find('{')
                json_data = json.loads(content_safe[json_start:])
                if isinstance(json_data, dict) and "result_json" in json_data:
                    error_msg = json_data["result_json"].get("message", error_msg)
            except:
                pass
        
        print(f"\n[FAILED] Compilation failed")
        # Remove unicode chars from error message for Windows compatibility
        error_msg_safe = error_msg.encode('ascii', 'ignore').decode('ascii')
        print(f"Error: {error_msg_safe[:200]}...")
        
        # Don't try to fix on last attempt
        if attempt >= max_attempts:
            print(f"\n[Info] Max attempts ({max_attempts}) reached.")
            break
        
        # Try to fix the code
        print(f"\n[Fixing] Attempting to fix code...")
        
        if use_llm:
            current_code = await fix_code_with_llm(current_code, error_msg, attempt)
        else:
            current_code = apply_rule_based_fixes(current_code, error_msg)
        
        print(f"\n[Preview] Fixed code:")
        preview = current_code[:300] + "..." if len(current_code) > 300 else current_code
        # Remove unicode for Windows
        preview_safe = preview.encode('ascii', 'ignore').decode('ascii')
        print(preview_safe)
    
    return False, current_code, attempts_history

async def test_file_with_agent(
    session: ClientSession,
    name: str,
    source_file: str,
    witness_file: str,
    max_attempts: int = 5,
    use_llm: bool = False
):
    """Test a single file with automatic fixing"""
    
    print(f"\n{'='*70}")
    print(f"[Testing] {name}")
    print(f"{'='*70}")
    
    # Read files
    source_code = Path(source_file).read_text()
    witness_data = Path(witness_file).read_text() if Path(witness_file).exists() else ""
    
    print(f"Original code length: {len(source_code)} chars")
    
    # Try to compile and fix
    success, final_code, history = await compile_and_fix(
        session,
        source_code,
        witness_data,
        max_attempts=max_attempts,
        use_llm=use_llm
    )
    
    # Save results
    if success:
        output_file = Path(source_file).parent / f"{Path(source_file).stem}_fixed.simf"
        output_file.write_text(final_code)
        print(f"\n[Saved] Fixed code saved to: {output_file}")
    
    return success, history

async def main():
    """Run the agent"""
    
    print("="*70)
    print("SimplicityHL Auto-Fix Agent")
    print("="*70)
    
    # Parse arguments
    use_docker = "--docker" in sys.argv
    use_llm = "--llm" in sys.argv
    max_attempts = 5
    
    for arg in sys.argv:
        if arg.startswith("--max-attempts="):
            max_attempts = int(arg.split("=")[1])
    
    print(f"\nConfiguration:")
    print(f"  Mode: {'Docker' if use_docker else 'Local'}")
    print(f"  LLM: {'Enabled' if use_llm else 'Rule-based only'}")
    print(f"  Max attempts: {max_attempts}")
    
    # Setup server connection
    if use_docker:
        server_params = StdioServerParameters(
            command="docker",
            args=["exec", "-i", "mcp-simplicity-server", "python", "server.py"]
        )
    else:
        server_params = StdioServerParameters(
            command="python",
            args=["server.py"]
        )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("\n[Connected] MCP server ready")
            
            # Test files
            test_files = [
                ("Arithmetic", "examples/arithmetic.simf", "examples/arithmetic.wit"),
                ("Scoping", "examples/scoping.simf", "examples/scoping.wit"),
                ("Witness Equality", "examples/witness_equality.simf", "examples/witness_equality.wit"),
                ("Witness Computation", "examples/witness_computation.simf", "examples/witness_computation.wit"),
            ]
            
            results = {}
            all_history = {}
            
            for name, source, witness in test_files:
                success, history = await test_file_with_agent(
                    session,
                    name,
                    source,
                    witness,
                    max_attempts=max_attempts,
                    use_llm=use_llm
                )
                results[name] = success
                all_history[name] = history
            
            # Final summary
            print("\n" + "="*70)
            print("[SUMMARY] Final Results")
            print("="*70)
            
            for name, success in results.items():
                status = "[OK] FIXED" if success else "[FAIL] NOT FIXED"
                attempts = len(all_history[name])
                print(f"{status}: {name} ({attempts} attempts)")
            
            total = len(results)
            fixed = sum(results.values())
            
            print(f"\n[Results] {fixed}/{total} files fixed")
            
            if fixed == total:
                print("[Success] All files successfully fixed!")
                return 0
            else:
                print(f"[Warning] {total - fixed} file(s) could not be fixed")
                print("\nNext steps:")
                print("  1. Review the error messages above")
                print("  2. Check the SimplicityHL documentation for correct syntax")
                print("  3. Enable LLM mode with --llm flag for smarter fixes")
                return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
