#!/usr/bin/env python3
"""
MCP Server for SimplicityHL Compilation using pysimplicityhl
Provides tools for compiling SimplicityHL code with witness files
"""

import asyncio
import json
import traceback
import tempfile
import os
from pathlib import Path
from typing import Optional
from mcp.server import Server
from mcp.types import Tool, TextContent, ImageContent, EmbeddedResource
from mcp.server.stdio import stdio_server

# Import pysimplicityhl
try:
    import pysimplicityhl
    PYSIMPLICITYHL_AVAILABLE = True
except ImportError:
    PYSIMPLICITYHL_AVAILABLE = False
    print("Warning: pysimplicityhl not installed. Install with: pip install pysimplicityhl")

# Initialize MCP server
app = Server("simplicity-compiler")

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools"""
    return [
        Tool(
            name="compile_simplicity",
            description="""
            Compiles SimplicityHL source code with a witness file using pysimplicityhl.
            Returns compilation results including success status, output, and error messages.
            The agent can use error messages to fix the code iteratively.
            
            This tool accepts either:
            - source_code + witness_data as strings (will create temporary files)
            - source_file + witness_file as file paths (will use existing files)
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "source_code": {
                        "type": "string",
                        "description": "The SimplicityHL source code to compile (if not using source_file)"
                    },
                    "witness_data": {
                        "type": "string",
                        "description": "The witness file content (if not using witness_file)",
                        "default": ""
                    },
                    "source_file": {
                        "type": "string",
                        "description": "Path to existing .simf file (alternative to source_code)"
                    },
                    "witness_file": {
                        "type": "string",
                        "description": "Path to existing .wit file (alternative to witness_data)"
                    },
                    "additional_params": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional parameters to pass to pysimplicityhl",
                        "default": []
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="compile_simplicity_from_files",
            description="""
            Compiles SimplicityHL from existing files on disk.
            Faster if files already exist, no need to pass content as strings.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "source_file": {
                        "type": "string",
                        "description": "Path to the .simf source file"
                    },
                    "witness_file": {
                        "type": "string",
                        "description": "Path to the .wit witness file (optional)"
                    },
                    "additional_params": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional parameters",
                        "default": []
                    }
                },
                "required": ["source_file"]
            }
        ),
        Tool(
            name="get_compilation_history",
            description="""
            Returns the history of compilation attempts for debugging.
            Useful for the agent to understand what has been tried.
            """,
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of history entries to return",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="get_pysimplicityhl_info",
            description="""
            Returns information about the installed pysimplicityhl library.
            Useful for debugging and understanding available features.
            """,
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        )
    ]

# Store compilation history
compilation_history = []

def add_to_history(source_code: str, witness_data: str, success: bool, output: str, errors: str):
    """Add compilation attempt to history"""
    compilation_history.append({
        "timestamp": asyncio.get_event_loop().time(),
        "source_code": source_code[:500] + "..." if len(source_code) > 500 else source_code,
        "witness_data": witness_data[:200] + "..." if len(witness_data) > 200 else witness_data,
        "success": success,
        "output": output,
        "errors": errors
    })
    # Keep only last 50 entries
    if len(compilation_history) > 50:
        compilation_history.pop(0)

def compile_with_pysimplicityhl(source_file_path: str, witness_file_path: Optional[str] = None, additional_params: list = None) -> dict:
    """
    Compile using pysimplicityhl with file paths
    
    Args:
        source_file_path: Path to .simf file (will be quoted)
        witness_file_path: Optional path to .wit file (will be quoted)
        additional_params: Additional parameters to pass
    
    Returns:
        dict with success, output, errors, result_json
    """
    try:
        # Build parameter list
        parameter = [f"'{source_file_path}'"]
        
        if witness_file_path:
            parameter.append(f"'{witness_file_path}'")
        
        if additional_params:
            parameter.extend(additional_params)
        
        # Create parameter string with quoted filenames
        parameter_str = " ".join(parameter)
        
        print(f"Running pysimplicityhl with: {parameter_str}")
        
        # Call pysimplicityhl
        result_json = pysimplicityhl.run_from_python(parameter_str)
        
        # Parse result
        if isinstance(result_json, str):
            result_data = json.loads(result_json)
        else:
            result_data = result_json
        
        # Check if successful
        success = result_data.get("success", False) or result_data.get("status") == "success"
        
        return {
            "success": success,
            "output": json.dumps(result_data, indent=2),
            "errors": result_data.get("error", "") or result_data.get("errors", ""),
            "result_json": result_data
        }
        
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "output": str(result_json) if 'result_json' in locals() else "",
            "errors": f"JSON decode error: {str(e)}",
            "result_json": None
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "errors": f"{str(e)}\n{traceback.format_exc()}",
            "result_json": None
        }

@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls"""
    
    if not PYSIMPLICITYHL_AVAILABLE:
        return [TextContent(
            type="text",
            text="❌ pysimplicityhl is not installed. Please install it with: pip install pysimplicityhl"
        )]
    
    if name == "compile_simplicity":
        source_code = arguments.get("source_code", "")
        witness_data = arguments.get("witness_data", "")
        source_file = arguments.get("source_file", "")
        witness_file = arguments.get("witness_file", "")
        additional_params = arguments.get("additional_params", [])
        
        # Determine if we need to create temp files
        use_temp_files = not source_file and source_code
        
        try:
            if use_temp_files:
                # Create temporary files
                with tempfile.TemporaryDirectory() as tmp_dir:
                    # Write source file
                    source_path = Path(tmp_dir) / "source.simf"
                    source_path.write_text(source_code)
                    
                    # Write witness file if provided
                    witness_path = None
                    if witness_data:
                        witness_path = Path(tmp_dir) / "witness.wit"
                        witness_path.write_text(witness_data)
                    
                    # Compile
                    result = compile_with_pysimplicityhl(
                        str(source_path),
                        str(witness_path) if witness_path else None,
                        additional_params
                    )
            else:
                # Use provided file paths
                result = compile_with_pysimplicityhl(
                    source_file,
                    witness_file if witness_file else None,
                    additional_params
                )
            
            # Add to history
            add_to_history(
                source_code if source_code else f"[file: {source_file}]",
                witness_data if witness_data else f"[file: {witness_file}]" if witness_file else "",
                result["success"],
                result["output"],
                result["errors"]
            )
            
            # Format response
            if result["success"]:
                message = f"✅ Compilation successful!\n\nOutput:\n{result['output']}"
            else:
                message = f"❌ Compilation failed\n\nErrors:\n{result['errors']}\n\nOutput:\n{result['output']}"
            
            return [TextContent(
                type="text",
                text=f"{message}\n\n---\nFull response:\n{json.dumps(result, indent=2)}"
            )]
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            add_to_history(
                source_code if source_code else f"[file: {source_file}]",
                witness_data if witness_data else "",
                False,
                "",
                error_msg
            )
            return [TextContent(
                type="text",
                text=f"❌ Unexpected error during compilation:\n{error_msg}"
            )]
    
    elif name == "compile_simplicity_from_files":
        source_file = arguments.get("source_file")
        witness_file = arguments.get("witness_file", "")
        additional_params = arguments.get("additional_params", [])
        
        if not source_file:
            return [TextContent(
                type="text",
                text="❌ source_file is required"
            )]
        
        # Check if files exist
        if not Path(source_file).exists():
            return [TextContent(
                type="text",
                text=f"❌ Source file not found: {source_file}"
            )]
        
        if witness_file and not Path(witness_file).exists():
            return [TextContent(
                type="text",
                text=f"❌ Witness file not found: {witness_file}"
            )]
        
        try:
            result = compile_with_pysimplicityhl(
                source_file,
                witness_file if witness_file else None,
                additional_params
            )
            
            # Add to history
            add_to_history(
                f"[file: {source_file}]",
                f"[file: {witness_file}]" if witness_file else "",
                result["success"],
                result["output"],
                result["errors"]
            )
            
            # Format response
            if result["success"]:
                message = f"✅ Compilation successful!\n\nOutput:\n{result['output']}"
            else:
                message = f"❌ Compilation failed\n\nErrors:\n{result['errors']}\n\nOutput:\n{result['output']}"
            
            return [TextContent(
                type="text",
                text=f"{message}\n\n---\nFull response:\n{json.dumps(result, indent=2)}"
            )]
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
            add_to_history(
                f"[file: {source_file}]",
                f"[file: {witness_file}]" if witness_file else "",
                False,
                "",
                error_msg
            )
            return [TextContent(
                type="text",
                text=f"❌ Unexpected error:\n{error_msg}"
            )]
    
    elif name == "get_compilation_history":
        limit = arguments.get("limit", 10)
        history = compilation_history[-limit:]
        
        if not history:
            return [TextContent(
                type="text",
                text="No compilation history available yet."
            )]
        
        history_text = "Compilation History:\n" + "="*50 + "\n\n"
        for i, entry in enumerate(reversed(history), 1):
            status = "✅ SUCCESS" if entry["success"] else "❌ FAILED"
            history_text += f"{i}. {status}\n"
            if entry["errors"]:
                history_text += f"   Errors: {entry['errors'][:200]}\n"
            if entry["output"]:
                history_text += f"   Output: {entry['output'][:200]}\n"
            history_text += "\n"
        
        return [TextContent(
            type="text",
            text=history_text
        )]
    
    elif name == "get_pysimplicityhl_info":
        try:
            info = {
                "installed": PYSIMPLICITYHL_AVAILABLE,
                "version": getattr(pysimplicityhl, '__version__', 'unknown'),
                "available_functions": [m for m in dir(pysimplicityhl) if not m.startswith('_')],
                "module_path": pysimplicityhl.__file__ if hasattr(pysimplicityhl, '__file__') else 'unknown'
            }
            
            return [TextContent(
                type="text",
                text=f"pysimplicityhl Information:\n{json.dumps(info, indent=2)}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error getting pysimplicityhl info: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

async def main():
    """Main entry point"""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
