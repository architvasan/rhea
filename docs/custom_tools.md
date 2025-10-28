# Custom Tools in Rhea

This guide explains how to add custom tools (non-Galaxy tools) to Rhea, including Academy agents for specialized workflows like peptide design.

## Overview

Rhea supports two types of tools:

1. **Galaxy Tools**: Traditional bioinformatics tools from the Galaxy ToolShed
2. **Custom Tools**: Academy agents and other custom executors for specialized workflows

Custom tools are stored in a separate database table (`customtools`) and are discoverable via the same RAG-based `find_tools()` mechanism.

## Architecture

### Components

1. **CustomTool Schema** (`rhea/utils/custom_tool_schema.py`)
   - Lightweight tool definition without Galaxy XML complexity
   - Supports Academy agents, Python functions, and custom executors

2. **Database Model** (`rhea/utils/models.py::CustomToolModel`)
   - PostgreSQL table with pgvector embeddings
   - Stores tool metadata and full definitions as JSONB

3. **Agent Implementations** (`rhea/agents/`)
   - Academy agents that implement the actual functionality
   - Example: Peptide design agents (folding, inverse folding, QC, analysis)

4. **MCP Tool Builders** (`rhea/server/custom_tool_utils.py`)
   - Converts CustomTool definitions into MCP-compatible tools
   - Handles parameter validation and agent execution

5. **RAG Integration** (`rhea/utils/embedding.py`)
   - Generates embeddings for custom tools
   - Searches both Galaxy and custom tools simultaneously

## Adding Custom Tools

### Step 1: Define Your Academy Agent

Create your agent in `rhea/agents/`:

```python
from academy.agent import Agent, action

class MyCustomAgent(Agent):
    def __init__(self, config: dict) -> None:
        super().__init__()
        self.config = config
    
    @action
    async def my_action(self, param1: str, param2: int) -> dict:
        """Your agent action implementation."""
        # Your logic here
        return {"result": "success"}
```

### Step 2: Create Tool Definition

Create a script to define your tool (see `rhea/preprocess/register_peptide_tools.py` for examples):

```python
from rhea.utils.custom_tool_schema import (
    CustomTool,
    CustomToolParameter,
    CustomToolOutput,
    CustomToolRequirements,
)

def create_my_tool() -> CustomTool:
    return CustomTool(
        id="my_custom_tool",
        name="My Custom Tool",
        version="1.0.0",
        description="Short description of what the tool does",
        long_description="Detailed description...",
        documentation="""# My Custom Tool
        
## Description
Full markdown documentation here...

## Example
\`\`\`python
result = await client.call_tool("my_custom_tool", {...})
\`\`\`
""",
        tool_type="academy_agent",
        agent_class="rhea.agents.my_module.MyCustomAgent",
        action_name="my_action",
        parameters=[
            CustomToolParameter(
                name="param1",
                type="string",
                description="First parameter",
                required=True,
            ),
            CustomToolParameter(
                name="param2",
                type="integer",
                description="Second parameter",
                required=False,
                default=10,
            ),
        ],
        outputs=[
            CustomToolOutput(
                name="result",
                type="dict",
                description="Result dictionary",
            ),
        ],
        requirements=CustomToolRequirements(
            pip_packages=["some-package"],
            gpu_required=False,
            min_memory_gb=4,
        ),
        tags=["custom", "example"],
    )
```

### Step 3: Register Tool in Database

```python
import asyncio
from openai import OpenAI
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from rhea.utils.models import CustomToolModel
from rhea.utils.embedding import generate_custom_tool_documentation_embedding

async def register_my_tool():
    # Setup database connection
    engine = create_async_engine("postgresql+asyncpg://...")
    SessionLocal = async_sessionmaker(bind=engine, ...)
    
    # Setup embedding client
    embedding_client = OpenAI(base_url="http://localhost:8000/v1", api_key="")
    
    # Create tool definition
    tool = create_my_tool()
    
    # Generate embedding
    embedding = generate_custom_tool_documentation_embedding(
        tool, embedding_client, "Qwen/Qwen3-Embedding-0.6B"
    )
    
    # Save to database
    async with SessionLocal() as session:
        tool_model = CustomToolModel(
            id=tool.id,
            name=tool.name,
            description=tool.description,
            long_description=tool.long_description,
            documentation=tool.documentation,
            tool_type=tool.tool_type,
            embedding=embedding,
        )
        tool_model.definition = tool
        session.add(tool_model)
        await session.commit()

asyncio.run(register_my_tool())
```

### Step 4: Use Your Tool

Once registered, your tool is discoverable via RAG:

```python
from rhea.client import RheaClient

async with RheaClient('localhost', 3001) as client:
    # Find your tool
    await client.find_tools("I need to do custom processing")
    
    # List available tools
    tools = await client.list_tools()
    
    # Call your tool
    result = await client.call_tool("my_custom_tool", {
        "param1": "value",
        "param2": 42
    })
```

## Peptide Design Example

The peptide design agents demonstrate a complete multi-agent workflow:

### Agents

1. **ForwardFoldingAgent**: Structure prediction using Chai-1
2. **InverseFoldingAgent**: Sequence generation using ProteinMPNN
3. **QualityControlAgent**: Sequence filtering
4. **AnalysisAgent**: Structure evaluation
5. **PeptideDesignCoordinator**: Workflow orchestration

### Tools Registered

- `peptide_forward_fold_initial`: Initial structure prediction
- `peptide_inverse_fold`: Sequence generation
- `peptide_quality_control`: Sequence filtering

### Usage

```python
# Find peptide design tools
await client.find_tools("I need to design peptide binders")

# Use forward folding
result = await client.call_tool("peptide_forward_fold_initial", {
    "target_sequence": "MKTAYIAK...",
    "binder_sequence": "GSSGSSG...",
    "trial": 0
})

# Use inverse folding
sequences = await client.call_tool("peptide_inverse_fold", {
    "fasta_in": "/path/to/input.fasta",
    "pdb_path": "/path/to/structure.pdb",
    "fasta_out": "/path/to/output.fasta",
    "remodel_indices": [1, 2, 3, 4, 5]
})
```

## Database Setup

### Create Custom Tools Table

```bash
# Run migration to create the table
python -m rhea.preprocess.create_custom_tools_table
```

### Register Peptide Design Tools

```bash
# Register the peptide design tools
python -m rhea.preprocess.register_peptide_tools
```

## Parameter Types

Custom tools support the following parameter types:

- `string`: Text input
- `integer`: Whole numbers
- `float`: Decimal numbers
- `boolean`: True/False
- `file`: File handle (RheaFileHandle)
- `list`: List of values

## Requirements

Custom tools can specify:

- `conda_packages`: Conda packages to install
- `pip_packages`: Pip packages to install
- `container_image`: Docker/Podman image
- `gpu_required`: Whether GPU is needed
- `min_memory_gb`: Minimum memory
- `min_cpus`: Minimum CPU cores

## Best Practices

1. **Clear Documentation**: Provide comprehensive markdown documentation
2. **Good Descriptions**: Write clear, searchable descriptions for RAG
3. **Meaningful Tags**: Use tags to categorize tools
4. **Version Control**: Use semantic versioning
5. **Error Handling**: Implement robust error handling in agents
6. **Testing**: Test tools thoroughly before registration

## Troubleshooting

### Tool Not Found in RAG

- Check that embeddings were generated correctly
- Verify tool is in database: `SELECT * FROM customtools;`
- Try more specific search queries

### Tool Execution Fails

- Check agent class path is correct
- Verify action name matches agent method
- Check parameter types match expectations
- Review agent logs for errors

## Future Enhancements

- [ ] Automatic agent launching and lifecycle management
- [ ] Support for multi-agent workflows
- [ ] Tool composition and chaining
- [ ] Performance monitoring and metrics
- [ ] Tool versioning and updates

