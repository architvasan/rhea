"""
Custom tool schema for non-Galaxy tools (e.g., Academy agents).

This module defines a lightweight schema for tools that don't follow the Galaxy XML format,
such as custom Academy agents for peptide design, protein analysis, etc.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field


class CustomToolParameter(BaseModel):
    """Parameter definition for a custom tool."""
    
    name: str = Field(..., description="Parameter name")
    type: Literal["string", "integer", "float", "boolean", "file", "list"] = Field(
        ..., description="Parameter type"
    )
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=True, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value")


class CustomToolOutput(BaseModel):
    """Output definition for a custom tool."""
    
    name: str = Field(..., description="Output name")
    type: Literal["string", "integer", "float", "file", "dict", "list"] = Field(
        ..., description="Output type"
    )
    description: str = Field(..., description="Output description")


class CustomToolRequirements(BaseModel):
    """Requirements for running a custom tool."""
    
    conda_packages: List[str] = Field(
        default_factory=list, description="Conda packages to install"
    )
    pip_packages: List[str] = Field(
        default_factory=list, description="Pip packages to install"
    )
    container_image: Optional[str] = Field(
        default=None, description="Docker/Podman container image"
    )
    gpu_required: bool = Field(default=False, description="Whether GPU is required")
    min_memory_gb: Optional[int] = Field(
        default=None, description="Minimum memory in GB"
    )
    min_cpus: Optional[int] = Field(default=None, description="Minimum CPU cores")


class CustomTool(BaseModel):
    """
    Custom tool definition for non-Galaxy tools.
    
    This is a lightweight alternative to the Galaxy Tool schema for tools
    that are implemented as Academy agents or other custom executors.
    """
    
    id: str = Field(..., description="Unique tool identifier")
    name: str = Field(..., description="Human-readable tool name")
    version: str = Field(default="1.0.0", description="Tool version")
    description: str = Field(..., description="Short description of the tool")
    long_description: Optional[str] = Field(
        default=None, description="Detailed description of the tool"
    )
    documentation: Optional[str] = Field(
        default=None, description="Full documentation in Markdown format"
    )
    
    # Tool type and execution
    tool_type: Literal["academy_agent", "python_function", "custom"] = Field(
        ..., description="Type of tool executor"
    )
    agent_class: Optional[str] = Field(
        default=None,
        description="Fully qualified class name for Academy agent (e.g., 'rhea.agents.peptide.ForwardFoldingAgent')"
    )
    action_name: Optional[str] = Field(
        default=None,
        description="Name of the agent action to call (e.g., 'fold_initial')"
    )
    
    # Parameters and outputs
    parameters: List[CustomToolParameter] = Field(
        default_factory=list, description="Tool input parameters"
    )
    outputs: List[CustomToolOutput] = Field(
        default_factory=list, description="Tool outputs"
    )
    
    # Requirements
    requirements: CustomToolRequirements = Field(
        default_factory=CustomToolRequirements,
        description="Tool execution requirements"
    )
    
    # Metadata
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorization and search"
    )
    citations: Optional[List[str]] = Field(
        default=None, description="Citations or references"
    )
    author: Optional[str] = Field(default=None, description="Tool author")
    
    # Configuration
    config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional configuration for the tool"
    )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: dict) -> "CustomTool":
        """Create from dictionary."""
        return cls.model_validate(data)

