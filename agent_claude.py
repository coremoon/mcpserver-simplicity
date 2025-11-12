#!/usr/bin/env python3
"""
Advanced agent with Anthropic Claude integration for fixing SimplicityHL code
"""

import asyncio
import sys
import os
import json
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Try to import Anthropic
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("⚠️  anthropic package not installed. Run: pip install anthropic")

class SimplicityFixAgent:
    """Agent that fixes SimplicityHL compilation errors using Claude"""
    
    def __init__(self, api_key: str = None, model: str = "claude-sonnet-4-20250514"):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.model = model
        self.client = None
        
        if ANTHROPIC_AVAILABLE and self.api_key:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            print(f"✅ Claude API initialized (model: {model})")
        else:
            print("⚠️  Claude API not available. Using rule-based fixes only.")
    
    async def analyze_and_fix(self, source_code: str, error_message: str, attempt: int) -> dict:
        """
        Analyzes error and generates fixed code using Claude
        
        Returns:
            {
                "fixed_code": str,
                "explanation": str,
                "confidence": float
            }
        """
        
        if not self.client:
            # Fallback to rule-based
            fixed = self.apply_rule_based_fixes(source_code, error_message)
            return {
                "fixed_code": fixed,
                "explanation": "Rule-based fix applied (no LLM available)",
                "confidence": 0.5
            }
        
        prompt = f"""You are an expert in SimplicityHL, a functional programming language for Bitcoin smart contracts.

The following SimplicityHL code failed to compile with this error:

```
{error_message}
```

Current code:
```
{source_code}
```

Please analyze the error and provide a fixed version of the code. SimplicityHL has specific syntax rules:

1. Variable declarations use pattern matching: `let (var,) = expression;`
2. Jets (built-in functions) are called like: `jet::add_32(a, b)`
3. There may not be a `fn main()` wrapper - code might be top-level
4. Assertions use `jet::verify(condition)`
5. Witness data is accessed with specific syntax

Respond with a JSON object:
{{
    "fixed_code": "the corrected code",
    "explanation": "what was wrong and how you fixed it",
    "confidence": 0.0-1.0
}}

Only respond with valid JSON, no other text."""

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # Parse response
            response_text = response.content[0].text
            
            # Try to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                response_text = response_text[json_start:json_end].strip()
            
            result = json.loads(response_text)
            
            print(f"\n🤖 Claude's analysis:")
            print(f"   Explanation: {result.get('explanation', 'N/A')[:150]}...")
            print(f"   Confidence: {result.get('confidence', 0.0):.0%}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error calling Claude API: {e}")
            # Fallback to rule-based
            fixed = self.apply_rule_based_fixes(source_code, error_message)
            return {
                "fixed_code": fixed,
                "explanation": f"API error, used rule-based fix: {str(e)}",
                "confidence": 0.3
            }
    
    def apply_rule_based_fixes(self, source_code: str, error_message: str) -> str:
        """Apply simple rule-based fixes"""
        import re
        
        fixed_code = source_code
        
        # Remove fn main() wrapper if present
        if "fn main()" in fixed_code:
            fixed_code = re.sub(
                r'fn\s+main\(\)\s*\{(.*)\}',
                r'\1',
                fixed_code,
                flags=re.DOTALL
            )
        
        # Fix let patterns: let var = ... -> let (var,) = ...
        fixed_code = re.sub(
            r'let\s+(\w+)\s*=\s*(jet::\w+\([^)]+\));',
            r'let (\1,) = \2;',
            fixed_code
        )
        
        # Fix assert! to jet::verify
        fixed_code = re.sub(
            r'assert!\(([^)]+)\);',
            r'jet::verify(\1);',
            fixed_code
        )
        
        return fixed_code

async def compile_with_retries(
    session: ClientSession,
    agent: SimplicityFixAgent,
    source_code: str,
    witness_data: str,
    max_attempts: int = 5
) -> tuple[bool, str, list]:
    """
    Compile code with automatic fixing via agent
    """
    
    current_code = source_code
    history = []
    
    for attempt in range(1, max_attempts + 1):
        print(f"\n{'='*70}")
        print(f"🔄 Attempt {attempt}/{max_attempts}")
        print(f"{'='*70}")
        
        # Compile
        result = await session.call_tool(
            "compile_simplicity",
            arguments={
                "source_code": current_code,
                "witness_data": witness_data
            }
        )
        
        content = result.content[0].text if result.content else ""
        
        # Check success
        if "✅ Compilation successful!" in content:
            print("🎉 SUCCESS!")
            history.append({
                "attempt": attempt,
                "success": True,
                "code": current_code
            })
            return True, current_code, history
        
        # Extract error
        error_msg = content
        if "message\":" in content:
            try:
                json_start = content.find('{')
                json_data = json.loads(content[json_start:])
                if isinstance(json_data, dict) and "result_json" in json_data:
                    error_msg = json_data["result_json"].get("message", error_msg)
            except:
                pass
        
        print(f"❌ Compilation failed")
        print(f"Error: {error_msg[:250]}...")
        
        history.append({
            "attempt": attempt,
            "success": False,
            "error": error_msg[:200],
            "code": current_code
        })
        
        if attempt >= max_attempts:
            break
        
        # Get fix from agent
        print(f"\n🔧 Agent analyzing and fixing...")
        fix_result = await agent.analyze_and_fix(current_code, error_msg, attempt)
        
        current_code = fix_result["fixed_code"]
        
        print(f"\n📝 Fixed code preview:")
        print(current_code[:400] + "..." if len(current_code) > 400 else current_code)
    
    return False, current_code, history

async def main():
    """Main entry point"""
    
    print("="*70)
    print("SimplicityHL Auto-Fix Agent with Claude")
    print("="*70)
    
    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not set in environment")
        print("   Export it or the agent will use rule-based fixes only")
        print("   Example: export ANTHROPIC_API_KEY='your-key-here'\n")
    
    # Initialize agent
    agent = SimplicityFixAgent(api_key=api_key)
    
    # Parse args
    use_docker = "--docker" in sys.argv
    max_attempts = 5
    
    for arg in sys.argv:
        if arg.startswith("--max-attempts="):
            max_attempts = int(arg.split("=")[1])
    
    print(f"\nConfiguration:")
    print(f"  Mode: {'Docker' if use_docker else 'Local'}")
    print(f"  Max attempts: {max_attempts}")
    
    # Connect to server
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
            print("\n✅ Connected to MCP server\n")
            
            # Test files
            test_files = [
                ("Arithmetic", "examples/arithmetic.simf", "examples/arithmetic.wit"),
                ("Scoping", "examples/scoping.simf", "examples/scoping.wit"),
                ("Witness Equality", "examples/witness_equality.simf", "examples/witness_equality.wit"),
                ("Witness Computation", "examples/witness_computation.simf", "examples/witness_computation.wit"),
            ]
            
            results = {}
            
            for name, source_file, witness_file in test_files:
                print(f"\n{'='*70}")
                print(f"📝 Processing: {name}")
                print(f"{'='*70}")
                
                source_code = Path(source_file).read_text()
                witness_data = Path(witness_file).read_text()
                
                success, fixed_code, history = await compile_with_retries(
                    session,
                    agent,
                    source_code,
                    witness_data,
                    max_attempts=max_attempts
                )
                
                results[name] = success
                
                if success:
                    # Save fixed version
                    output_file = Path(source_file).parent / f"{Path(source_file).stem}_fixed.simf"
                    output_file.write_text(fixed_code)
                    print(f"\n💾 Fixed code saved to: {output_file}")
            
            # Summary
            print("\n" + "="*70)
            print("📊 FINAL RESULTS")
            print("="*70)
            
            for name, success in results.items():
                status = "✅ FIXED" if success else "❌ FAILED"
                print(f"{status}: {name}")
            
            total = len(results)
            fixed = sum(results.values())
            print(f"\n🎯 Success rate: {fixed}/{total} ({fixed/total*100:.0f}%)")
            
            return 0 if fixed == total else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
