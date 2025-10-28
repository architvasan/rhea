# Custom Tools Implementation Summary

## Overview

This document summarizes the implementation of custom (non-Galaxy) tools in Rhea, specifically for integrating Academy-based peptide design agents from the BindCraft project.

## What Was Implemented

### 1. Custom Tool Schema (`rhea/utils/custom_tool_schema.py`)

Created a lightweight schema for defining custom tools without Galaxy XML complexity:

- **CustomTool**: Main tool definition with metadata, parameters, outputs, requirements
- **CustomToolParameter**: Input parameter definitions with types and validation
- **CustomToolOutput**: Output definitions
- **CustomToolRequirements**: Dependency and resource requirements

**Key Features:**
- Supports Academy agents, Python functions, and custom executors
- Flexible parameter types (string, integer, float, boolean, file, list)
- Resource requirements (GPU, memory, CPU)
- Dependency management (conda, pip, containers)
- Rich documentation support (markdown)

### 2. Database Model (`rhea/utils/models.py`)

Added `CustomToolModel` table to store custom tools:

- **Table**: `customtools`
- **Columns**: id, name, description, long_description, documentation, tool_type, definition (JSONB), embedding (Vector 1024)
- **Index**: IVFFlat index on embedding for fast L2 distance search
- **Helper Functions**: `get_customtool_by_id()`, `get_customtool_by_name()`, `get_all_customtool_ids()`

### 3. Peptide Design Agents (`rhea/agents/peptide_design.py`)

Implemented Academy agents for peptide binder design:

- **ForwardFoldingAgent**: Structure prediction using Chai-1
  - `fold_initial()`: Initial target-binder complex folding
  - `refold_sequences()`: Refold new sequences with target

- **InverseFoldingAgent**: Sequence generation using ProteinMPNN
  - `generate_sequences()`: Generate new sequences from structure

- **QualityControlAgent**: Sequence filtering
  - `filter_sequences()`: Apply QC criteria to sequences

- **AnalysisAgent**: Structure evaluation
  - `evaluate_structures()`: Calculate energies and filter

- **PeptideDesignCoordinator**: Workflow orchestration
  - `run_full_workflow()`: Complete multi-round design workflow

### 4. MCP Tool Builder (`rhea/server/custom_tool_utils.py`)

Created utilities to convert CustomTool definitions into MCP tools:

- **create_custom_tool()**: Main function to create MCP-compatible tools
- **parameter_type_to_python()**: Convert parameter types to Python annotations
- **create_custom_tool_parameters()**: Build function signatures from parameters
- **make_wrapper()**: Create async wrapper for agent execution

**Features:**
- Automatic parameter validation
- Type conversion and annotation
- Error handling and logging
- Integration with Rhea's execution infrastructure

### 5. Embedding Support (`rhea/utils/embedding.py`)

Extended embedding utilities for custom tools:

- **generate_custom_tool_documentation_embedding()**: Generate embeddings for custom tools
- **get_l2_distance_custom()**: Search custom tools by vector similarity
- **get_l2_distance_combined()**: Search both Galaxy and custom tools simultaneously

### 6. MCP Server Integration (`rhea/server/mcp_server.py`)

Updated the `find_tools()` function to support custom tools:

- Searches both `galaxytools` and `customtools` tables
- Populates both Galaxy and custom tools in MCP context
- Adds documentation resources for all tools
- Maintains backward compatibility with existing Galaxy tools

### 7. Tool Registration Script (`rhea/preprocess/register_peptide_tools.py`)

Created script to register peptide design tools in database:

**Tools Registered:**
1. `peptide_forward_fold_initial`: Initial structure prediction
2. `peptide_inverse_fold`: Sequence generation via ProteinMPNN
3. `peptide_quality_control`: Sequence filtering

**Features:**
- Automatic embedding generation
- Comprehensive documentation
- Proper tagging for discoverability
- Resource requirement specification

### 8. Database Migration (`rhea/preprocess/create_custom_tools_table.py`)

Created migration script to set up the database:

- Creates `customtools` table
- Ensures pgvector extension is enabled
- Creates IVFFlat index for vector search

### 9. Documentation (`docs/custom_tools.md`)

Comprehensive guide covering:
- Architecture overview
- Step-by-step guide for adding custom tools
- Peptide design example
- Database setup instructions
- Best practices and troubleshooting

## How It Works

### Tool Discovery Flow

```
User Query: "I need to design peptide binders"
    ↓
Embedding Generated (1024-dim vector)
    ↓
RAG Search (L2 distance)
    ├─→ Search galaxytools table
    └─→ Search customtools table
    ↓
Top 10 Results Combined
    ↓
Tools Added to MCP Context
    ├─→ Galaxy tools → create_tool()
    └─→ Custom tools → create_custom_tool()
    ↓
Tools Available for LLM
```

### Tool Execution Flow

```
LLM Calls Tool: peptide_forward_fold_initial
    ↓
MCP Server Receives Request
    ↓
custom_tool_utils.wrapper()
    ├─→ Validate parameters
    ├─→ Launch/retrieve Academy agent
    ├─→ Call agent action
    └─→ Return results
    ↓
Results Returned to LLM
```

## Files Created/Modified

### Created Files
1. `rhea/utils/custom_tool_schema.py` - Custom tool schema definitions
2. `rhea/agents/__init__.py` - Agent package initialization
3. `rhea/agents/peptide_design.py` - Peptide design agents
4. `rhea/server/custom_tool_utils.py` - MCP tool builder for custom tools
5. `rhea/preprocess/register_peptide_tools.py` - Tool registration script
6. `rhea/preprocess/create_custom_tools_table.py` - Database migration
7. `docs/custom_tools.md` - Comprehensive documentation
8. `CUSTOM_TOOLS_IMPLEMENTATION.md` - This summary

### Modified Files
1. `rhea/utils/models.py` - Added CustomToolModel and helper functions
2. `rhea/utils/embedding.py` - Added custom tool embedding support
3. `rhea/server/mcp_server.py` - Updated find_tools() for custom tools

## Usage Example

### 1. Setup Database

```bash
# Create the customtools table
python -m rhea.preprocess.create_custom_tools_table

# Register peptide design tools
python -m rhea.preprocess.register_peptide_tools
```

### 2. Use Tools via MCP

```python
from rhea.client import RheaClient

async with RheaClient('localhost', 3001) as client:
    # Discover tools
    await client.find_tools("I need to design peptide binders")
    
    # Call forward folding
    result = await client.call_tool("peptide_forward_fold_initial", {
        "target_sequence": "MKTAYIAKQRQISFVKSHFSRQ...",
        "binder_sequence": "GSSGSSGENLYFQG",
        "trial": 0
    })
    
    # Call inverse folding
    sequences = await client.call_tool("peptide_inverse_fold", {
        "fasta_in": "/path/to/input.fasta",
        "pdb_path": result["structure"],
        "fasta_out": "/path/to/output.fasta",
        "remodel_indices": [1, 2, 3, 4, 5]
    })
```

## Key Design Decisions

### 1. Parallel System vs. Unified Schema

**Decision**: Create a parallel system for custom tools rather than forcing them into Galaxy schema.

**Rationale**: 
- Galaxy XML schema is complex and designed for single-command tools
- Academy agents have different execution models (actions, handles, async)
- Cleaner separation of concerns
- Easier to extend for future tool types

### 2. Separate Database Table

**Decision**: Create `customtools` table instead of adding to `galaxytools`.

**Rationale**:
- Different schema requirements
- Easier to query and manage separately
- Can optimize indexes differently
- Clear separation in codebase

### 3. Combined RAG Search

**Decision**: Search both tables and combine results in `find_tools()`.

**Rationale**:
- Seamless user experience
- LLM doesn't need to know about tool types
- Can prioritize based on relevance, not tool type
- Maintains backward compatibility

### 4. Reuse Existing Infrastructure

**Decision**: Reuse Parsl, ProxyStore, Academy agent launching infrastructure.

**Rationale**:
- Avoid code duplication
- Consistent execution model
- Leverage existing testing and reliability
- Faster implementation

## Next Steps

### Immediate (Required for Full Functionality)

1. **Implement Agent Launching in `create_custom_tool()`**
   - Currently returns placeholder results
   - Need to integrate with Parsl and Academy agent launching
   - Handle agent lifecycle (launch, retrieve, cleanup)

2. **Add File Handling**
   - Integrate RheaFileHandle for file inputs/outputs
   - Use ProxyStore for file transfer
   - Handle PDB, FASTA, and other file types

3. **Testing**
   - Unit tests for custom tool schema
   - Integration tests for tool registration
   - End-to-end tests for peptide design workflow

### Future Enhancements

1. **Tool Composition**
   - Allow chaining custom tools
   - Workflow definitions
   - Automatic data flow between tools

2. **Performance Monitoring**
   - Metrics for custom tool execution
   - Resource usage tracking
   - Success/failure rates

3. **Tool Versioning**
   - Support multiple versions of same tool
   - Version selection in queries
   - Migration between versions

4. **Advanced Agent Features**
   - Multi-agent coordination
   - Stateful agents
   - Agent pools for parallel execution

## Dependencies

### New Dependencies Required

For peptide design agents:
- `chai-lab`: Chai-1 structure prediction
- `proteinmpnn`: ProteinMPNN sequence design

### Existing Dependencies Used

- `academy`: Agent framework
- `parsl`: Parallel execution
- `proxystore`: File handling
- `pgvector`: Vector similarity search
- `openai`: Embedding generation
- `fastmcp`: MCP server framework

## Conclusion

This implementation provides a clean, extensible framework for adding custom tools to Rhea. The peptide design agents serve as a complete example of how to integrate complex multi-agent workflows into the Rhea ecosystem while maintaining the same RAG-based discovery and MCP interface that users expect.

The parallel system approach allows custom tools to coexist with Galaxy tools without compromising either system, and the combined RAG search ensures users can discover the right tool regardless of its type.

