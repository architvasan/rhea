"""
Script to register peptide design tools in the Rhea database.

This script creates CustomTool definitions for the peptide design agents
and stores them in the database with embeddings for RAG-based discovery.
"""

import os
import asyncio
import logging
from openai import OpenAI
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncEngine,
    create_async_engine,
    async_sessionmaker,
)

from rhea.utils.custom_tool_schema import (
    CustomTool,
    CustomToolParameter,
    CustomToolOutput,
    CustomToolRequirements,
)
from rhea.utils.models import CustomToolModel
from rhea.utils.embedding import generate_custom_tool_documentation_embedding

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_forward_folding_tool() -> CustomTool:
    """Create tool definition for forward folding (initial fold)."""
    return CustomTool(
        id="peptide_forward_fold_initial",
        name="Peptide Forward Folding - Initial",
        version="1.0.0",
        description="Perform initial structure prediction for target-binder complex using Chai-1",
        long_description=(
            "This tool uses Chai-1 to predict the 3D structure of a target protein "
            "bound to a peptide binder. It's the first step in the peptide design workflow."
        ),
        documentation="""# Peptide Forward Folding - Initial

## Description
Performs initial forward folding (structure prediction) on a target-binder complex using Chai-1.

## Use Cases
- Initial structure prediction for peptide design workflows
- Validating target-binder interactions
- Generating starting structures for optimization

## Inputs
- **target_sequence**: Amino acid sequence of the target protein
- **binder_sequence**: Amino acid sequence of the peptide binder
- **trial**: Trial number for tracking multiple runs

## Outputs
- **structure**: Path to the predicted PDB structure file

## Example
```python
result = await client.call_tool(
    "peptide_forward_fold_initial",
    {
        "target_sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL",
        "binder_sequence": "GSSGSSGENLYFQG",
        "trial": 0
    }
)
```

## References
- Chai-1: https://github.com/chaidiscovery/chai-lab
""",
        tool_type="academy_agent",
        agent_class="rhea.agents.peptide_design.ForwardFoldingAgent",
        action_name="fold_initial",
        parameters=[
            CustomToolParameter(
                name="target_sequence",
                type="string",
                description="Amino acid sequence of the target protein",
                required=True,
            ),
            CustomToolParameter(
                name="binder_sequence",
                type="string",
                description="Amino acid sequence of the peptide binder",
                required=True,
            ),
            CustomToolParameter(
                name="trial",
                type="integer",
                description="Trial number for tracking",
                required=True,
            ),
        ],
        outputs=[
            CustomToolOutput(
                name="structure",
                type="string",
                description="Path to the predicted PDB structure file",
            ),
        ],
        requirements=CustomToolRequirements(
            pip_packages=["chai-lab"],
            gpu_required=True,
            min_memory_gb=16,
            min_cpus=4,
        ),
        tags=["peptide-design", "structure-prediction", "chai-1", "protein-folding"],
        author="BindCraft Team",
    )


def create_inverse_folding_tool() -> CustomTool:
    """Create tool definition for inverse folding (sequence generation)."""
    return CustomTool(
        id="peptide_inverse_fold",
        name="Peptide Inverse Folding",
        version="1.0.0",
        description="Generate new peptide sequences using ProteinMPNN based on a target structure",
        long_description=(
            "This tool uses ProteinMPNN to design new peptide sequences that are likely "
            "to fold into a desired structure. It's used to generate sequence variants "
            "in the peptide design workflow."
        ),
        documentation="""# Peptide Inverse Folding

## Description
Generates new peptide sequences using ProteinMPNN based on a target structure.

## Use Cases
- Designing sequence variants for peptide binders
- Optimizing sequences for improved binding
- Exploring sequence space around a structural scaffold

## Inputs
- **fasta_in**: Path to input FASTA file with reference sequence
- **pdb_path**: Path to PDB structure file to use as template
- **fasta_out**: Path where output FASTA file will be written
- **remodel_indices**: List of residue positions to redesign

## Outputs
- **sequences**: List of generated amino acid sequences

## Example
```python
result = await client.call_tool(
    "peptide_inverse_fold",
    {
        "fasta_in": "/path/to/input.fasta",
        "pdb_path": "/path/to/structure.pdb",
        "fasta_out": "/path/to/output.fasta",
        "remodel_indices": [1, 2, 3, 4, 5]
    }
)
```

## References
- ProteinMPNN: https://github.com/dauparas/ProteinMPNN
""",
        tool_type="academy_agent",
        agent_class="rhea.agents.peptide_design.InverseFoldingAgent",
        action_name="generate_sequences",
        parameters=[
            CustomToolParameter(
                name="fasta_in",
                type="string",
                description="Path to input FASTA file",
                required=True,
            ),
            CustomToolParameter(
                name="pdb_path",
                type="string",
                description="Path to PDB structure file",
                required=True,
            ),
            CustomToolParameter(
                name="fasta_out",
                type="string",
                description="Path for output FASTA file",
                required=True,
            ),
            CustomToolParameter(
                name="remodel_indices",
                type="list",
                description="List of residue indices to redesign",
                required=True,
            ),
        ],
        outputs=[
            CustomToolOutput(
                name="sequences",
                type="list",
                description="List of generated sequences",
            ),
        ],
        requirements=CustomToolRequirements(
            pip_packages=["proteinmpnn"],
            gpu_required=True,
            min_memory_gb=8,
            min_cpus=2,
        ),
        tags=["peptide-design", "sequence-design", "proteinmpnn", "inverse-folding"],
        author="BindCraft Team",
    )


def create_quality_control_tool() -> CustomTool:
    """Create tool definition for sequence quality control."""
    return CustomTool(
        id="peptide_quality_control",
        name="Peptide Quality Control",
        version="1.0.0",
        description="Filter peptide sequences based on quality control criteria",
        long_description=(
            "This tool filters generated peptide sequences based on various quality "
            "metrics such as sequence composition, length, and physicochemical properties."
        ),
        documentation="""# Peptide Quality Control

## Description
Filters peptide sequences based on quality control criteria.

## Use Cases
- Removing sequences with undesirable properties
- Ensuring sequence diversity
- Filtering for drug-like properties

## Inputs
- **sequences**: List of peptide sequences to filter

## Outputs
- **filtered_sequences**: List of sequences that passed QC

## Example
```python
result = await client.call_tool(
    "peptide_quality_control",
    {
        "sequences": ["MKTAYIAK", "GSSGSSG", "ENLYFQG"]
    }
)
```
""",
        tool_type="academy_agent",
        agent_class="rhea.agents.peptide_design.QualityControlAgent",
        action_name="filter_sequences",
        parameters=[
            CustomToolParameter(
                name="sequences",
                type="list",
                description="List of sequences to filter",
                required=True,
            ),
        ],
        outputs=[
            CustomToolOutput(
                name="filtered_sequences",
                type="list",
                description="Sequences that passed QC",
            ),
        ],
        requirements=CustomToolRequirements(
            pip_packages=[],
            gpu_required=False,
            min_memory_gb=2,
            min_cpus=1,
        ),
        tags=["peptide-design", "quality-control", "filtering"],
        author="BindCraft Team",
    )


async def register_tools(
    db_url: str,
    embedding_url: str = "http://localhost:8000/v1",
    embedding_key: str = "",
    model: str = "Qwen/Qwen3-Embedding-0.6B",
):
    """
    Register peptide design tools in the database.
    
    Args:
        db_url: Database connection URL
        embedding_url: URL for embedding service
        embedding_key: API key for embedding service
        model: Embedding model to use
    """
    # Create database engine
    engine: AsyncEngine = create_async_engine(db_url, echo=False, future=True)
    AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    
    # Create embedding client
    embedding_client = OpenAI(base_url=embedding_url, api_key=embedding_key)
    
    # Create tool definitions
    tools = [
        create_forward_folding_tool(),
        create_inverse_folding_tool(),
        create_quality_control_tool(),
    ]
    
    async with AsyncSessionLocal() as session:
        for tool in tools:
            logger.info(f"Registering tool: {tool.name}")
            
            # Generate embedding
            embedding = generate_custom_tool_documentation_embedding(
                tool, embedding_client, model
            )
            
            # Create database model
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
            
            # Add to session
            session.add(tool_model)
            logger.info(f"Added {tool.name} to database")
        
        # Commit all tools
        await session.commit()
        logger.info(f"Successfully registered {len(tools)} tools")


async def main():
    """Main entry point."""
    DATABASE_URL = os.environ.get(
        "DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/rhea"
    )
    EMBEDDING_URL = os.environ.get("EMBEDDING_URL", "http://localhost:8000/v1")
    EMBEDDING_KEY = os.environ.get("EMBEDDING_KEY", "")
    MODEL = os.environ.get("EMBEDDING_MODEL", "Qwen/Qwen3-Embedding-0.6B")
    
    await register_tools(DATABASE_URL, EMBEDDING_URL, EMBEDDING_KEY, MODEL)


if __name__ == "__main__":
    asyncio.run(main())

