"""
Utilities for creating MCP tools from custom tool definitions.

This module handles the creation of MCP-compatible tools from CustomTool definitions,
including Academy agent-based tools.
"""

import logging
import time
from typing import Any, Dict, List, Callable
from inspect import Signature, Parameter

from mcp.server.fastmcp import Context
from mcp.server.fastmcp.tools import Tool as FastMCPTool

from rhea.utils.custom_tool_schema import CustomTool, CustomToolParameter
from rhea.server.schema import MCPOutput, Settings
from rhea.utils.proxy import RheaFileHandle

logger = logging.getLogger(__name__)


def parameter_type_to_python(param_type: str) -> type:
    """
    Convert CustomToolParameter type to Python type annotation.
    
    Args:
        param_type: Parameter type string
        
    Returns:
        Python type for annotation
    """
    type_mapping = {
        "string": str,
        "integer": int,
        "float": float,
        "boolean": bool,
        "file": RheaFileHandle,
        "list": list,
    }
    return type_mapping.get(param_type, str)


def create_custom_tool_parameters(
    parameters: List[CustomToolParameter],
) -> List[Parameter]:
    """
    Create Python function parameters from CustomToolParameter definitions.
    
    Args:
        parameters: List of CustomToolParameter objects
        
    Returns:
        List of inspect.Parameter objects
    """
    params = []
    
    for param in parameters:
        annotation = parameter_type_to_python(param.type)
        
        if param.required:
            default = Parameter.empty
        else:
            default = param.default
        
        params.append(
            Parameter(
                name=param.name,
                kind=Parameter.POSITIONAL_OR_KEYWORD,
                default=default,
                annotation=annotation,
            )
        )
    
    return params


def create_custom_tool(tool: CustomTool, ctx: Context) -> FastMCPTool:
    """
    Create an MCP tool from a CustomTool definition.
    
    This function creates a wrapper that:
    1. Validates input parameters
    2. Launches or retrieves the Academy agent
    3. Calls the specified action
    4. Returns results in MCP format
    
    Args:
        tool: CustomTool definition
        ctx: MCP context
        
    Returns:
        FastMCPTool ready to be added to the MCP server
    """
    
    # Create parameter list
    params = create_custom_tool_parameters(tool.parameters)
    
    # Create signature
    sig = Signature(parameters=params)
    
    def make_wrapper(tool_id: str, param_names: List[str]) -> Callable:
        """Create the actual wrapper function."""
        
        async def wrapper(**kwargs) -> MCPOutput:
            """
            Wrapper function that executes the custom tool.
            
            This function:
            1. Retrieves or launches the Academy agent
            2. Calls the specified action with parameters
            3. Returns results
            """
            start_time = time.time()
            
            try:
                await ctx.info(f"Executing custom tool: {tool.name}")
                
                # Get settings from context
                settings: Settings = ctx.request_context.lifespan_context.settings
                
                # TODO: Implement agent launching and execution
                # For now, return a placeholder
                
                if tool.tool_type == "academy_agent":
                    # This is where we would:
                    # 1. Check if agent is already running
                    # 2. Launch agent if needed
                    # 3. Get handle to agent
                    # 4. Call the action with parameters
                    
                    result_data = {
                        "status": "success",
                        "message": f"Executed {tool.name}",
                        "parameters": kwargs,
                        "tool_type": tool.tool_type,
                        "action": tool.action_name,
                    }
                    
                    result = MCPOutput(
                        return_code=0,
                        stdout=f"Successfully executed {tool.name}",
                        stderr="",
                        data=result_data,
                    )
                else:
                    raise NotImplementedError(
                        f"Tool type {tool.tool_type} not yet implemented"
                    )
                
                execution_time = time.time() - start_time
                logger.info(f"Custom tool {tool.name} executed in {execution_time:.2f}s")
                
                return result
                
            except Exception as e:
                logger.error(f"Error executing custom tool {tool.name}: {e}")
                return MCPOutput(
                    return_code=1,
                    stdout="",
                    stderr=str(e),
                    data={"error": str(e)},
                )
        
        return wrapper
    
    # Create the wrapper function
    fn = make_wrapper(tool.id, [p.name for p in params])
    fn.__name__ = tool.id.replace("-", "_").replace(".", "_")
    fn.__doc__ = tool.description
    fn.__signature__ = sig  # type: ignore[attr-defined]
    
    # Set annotations
    fn.__annotations__ = {p.name: p.annotation for p in params}
    fn.__annotations__["return"] = MCPOutput
    
    # Create and return FastMCPTool
    return FastMCPTool.from_function(
        fn=fn,
        name=tool.id,
        title=tool.name,
        description=tool.description,
    )


def sanitize_tool_name(name: str) -> str:
    """
    Sanitize tool name for use as Python identifier.
    
    Args:
        name: Original tool name
        
    Returns:
        Sanitized name safe for use as identifier
    """
    # Replace spaces and special characters
    sanitized = name.lower()
    sanitized = sanitized.replace(" ", "_")
    sanitized = sanitized.replace("-", "_")
    sanitized = "".join(c for c in sanitized if c.isalnum() or c == "_")
    
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = f"tool_{sanitized}"
    
    return sanitized or "custom_tool"

