# Peptide Design Tools - Quick Setup Guide

This guide will walk you through setting up and using the peptide design tools in Rhea.

## Prerequisites

1. **Rhea Server Running**
   - PostgreSQL with pgvector extension
   - Redis for ProxyStore
   - Embedding service (Hugging Face TEI)
   - MinIO for object storage

2. **Dependencies Installed**
   ```bash
   # Install Rhea with custom tools support
   pip install -e .
   
   # Install peptide design dependencies
   pip install chai-lab proteinmpnn
   ```

## Setup Steps

### Step 1: Create Custom Tools Table

Run the database migration to create the `customtools` table:

```bash
# Set your database URL
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/rhea"

# Run migration
python -m rhea.preprocess.create_custom_tools_table
```

**Expected Output:**
```
INFO:__main__:Connecting to database: postgresql+asyncpg://...
INFO:__main__:Ensuring pgvector extension is enabled...
INFO:__main__:Creating customtools table...
INFO:__main__:Successfully created customtools table
INFO:__main__:Migration complete!
```

### Step 2: Register Peptide Design Tools

Register the peptide design tools in the database:

```bash
# Set environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/rhea"
export EMBEDDING_URL="http://localhost:8000/v1"
export EMBEDDING_KEY=""
export EMBEDDING_MODEL="Qwen/Qwen3-Embedding-0.6B"

# Run registration script
python -m rhea.preprocess.register_peptide_tools
```

**Expected Output:**
```
INFO:__main__:Registering tool: Peptide Forward Folding - Initial
INFO:__main__:Added Peptide Forward Folding - Initial to database
INFO:__main__:Registering tool: Peptide Inverse Folding
INFO:__main__:Added Peptide Inverse Folding to database
INFO:__main__:Registering tool: Peptide Quality Control
INFO:__main__:Added Peptide Quality Control to database
INFO:__main__:Successfully registered 3 tools
```

### Step 3: Verify Tools in Database

Check that tools were registered correctly:

```bash
# Connect to PostgreSQL
psql -U postgres -d rhea

# Query custom tools
SELECT id, name, tool_type FROM customtools;
```

**Expected Output:**
```
              id               |              name               |   tool_type   
-------------------------------+---------------------------------+---------------
 peptide_forward_fold_initial  | Peptide Forward Folding - Initial | academy_agent
 peptide_inverse_fold          | Peptide Inverse Folding         | academy_agent
 peptide_quality_control       | Peptide Quality Control         | academy_agent
```

### Step 4: Start Rhea Server

Start the Rhea MCP server:

```bash
# Start server
python -m rhea.server.mcp_server
```

### Step 5: Test Tool Discovery

Use the Rhea client to discover peptide design tools:

```python
import asyncio
from rhea.client import RheaClient

async def test_discovery():
    async with RheaClient('localhost', 3001) as client:
        # Find peptide design tools
        print("Searching for peptide design tools...")
        await client.find_tools("I need to design peptide binders")
        
        # List available tools
        tools = await client.list_tools()
        print(f"\nFound {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool['name']}")

asyncio.run(test_discovery())
```

**Expected Output:**
```
Searching for peptide design tools...

Found 3 tools:
  - Peptide Forward Folding - Initial
  - Peptide Inverse Folding
  - Peptide Quality Control
```

## Usage Examples

### Example 1: Forward Folding

Predict the structure of a target-binder complex:

```python
import asyncio
from rhea.client import RheaClient

async def forward_fold_example():
    async with RheaClient('localhost', 3001) as client:
        # Discover tools
        await client.find_tools("structure prediction")
        
        # Call forward folding
        result = await client.call_tool("peptide_forward_fold_initial", {
            "target_sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL",
            "binder_sequence": "GSSGSSGENLYFQG",
            "trial": 0
        })
        
        print(f"Structure predicted: {result['data']['structure']}")

asyncio.run(forward_fold_example())
```

### Example 2: Inverse Folding

Generate new sequences from a structure:

```python
import asyncio
from rhea.client import RheaClient

async def inverse_fold_example():
    async with RheaClient('localhost', 3001) as client:
        # Discover tools
        await client.find_tools("sequence design")
        
        # Call inverse folding
        result = await client.call_tool("peptide_inverse_fold", {
            "fasta_in": "/path/to/input.fasta",
            "pdb_path": "/path/to/structure.pdb",
            "fasta_out": "/path/to/output.fasta",
            "remodel_indices": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        })
        
        sequences = result['data']['sequences']
        print(f"Generated {len(sequences)} sequences:")
        for i, seq in enumerate(sequences[:5]):
            print(f"  {i+1}. {seq}")

asyncio.run(inverse_fold_example())
```

### Example 3: Quality Control

Filter sequences based on QC criteria:

```python
import asyncio
from rhea.client import RheaClient

async def qc_example():
    async with RheaClient('localhost', 3001) as client:
        # Discover tools
        await client.find_tools("quality control")
        
        # Call QC filter
        result = await client.call_tool("peptide_quality_control", {
            "sequences": [
                "GSSGSSGENLYFQG",
                "MKTAYIAKQRQISF",
                "VKSHFSRQLEERLG",
                "LIEVQAPILSRVGD",
            ]
        })
        
        filtered = result['data']['filtered_sequences']
        print(f"Filtered sequences: {len(filtered)} passed QC")
        for seq in filtered:
            print(f"  ✓ {seq}")

asyncio.run(qc_example())
```

## Troubleshooting

### Tools Not Found in Discovery

**Problem**: `find_tools()` doesn't return peptide design tools.

**Solutions**:
1. Check tools are in database:
   ```sql
   SELECT COUNT(*) FROM customtools;
   ```

2. Verify embeddings were generated:
   ```sql
   SELECT id, name, embedding IS NOT NULL as has_embedding FROM customtools;
   ```

3. Try more specific queries:
   ```python
   await client.find_tools("peptide binder design using ProteinMPNN")
   ```

### Database Connection Errors

**Problem**: `asyncpg.exceptions.InvalidCatalogNameError: database "rhea" does not exist`

**Solution**: Create the database:
```bash
createdb -U postgres rhea
```

### Embedding Service Not Available

**Problem**: `Connection refused` when generating embeddings.

**Solution**: Start the embedding service:
```bash
docker run -p 8000:80 \
  --gpus all \
  ghcr.io/huggingface/text-embeddings-inference:latest \
  --model-id Qwen/Qwen3-Embedding-0.6B
```

### pgvector Extension Missing

**Problem**: `ERROR: type "vector" does not exist`

**Solution**: Install pgvector:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql-15-pgvector

# macOS
brew install pgvector

# Then enable in database
psql -U postgres -d rhea -c "CREATE EXTENSION vector;"
```

## Next Steps

1. **Implement Agent Execution**: The current implementation returns placeholder results. You'll need to integrate with the actual BindCraft agents.

2. **Add File Handling**: Integrate ProxyStore for handling PDB and FASTA files.

3. **Test Full Workflow**: Run end-to-end tests with real protein sequences.

4. **Add More Tools**: Register additional tools like `refold_sequences` and `evaluate_structures`.

5. **Optimize Performance**: Add caching, parallel execution, and resource management.

## Resources

- **Full Documentation**: See `docs/custom_tools.md`
- **Implementation Details**: See `CUSTOM_TOOLS_IMPLEMENTATION.md`
- **BindCraft Repository**: https://github.com/msinclair-py/bindcraft/tree/agent_acad
- **Rhea Documentation**: See main README.md

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the full documentation in `docs/custom_tools.md`
3. Check the implementation summary in `CUSTOM_TOOLS_IMPLEMENTATION.md`
4. Open an issue on GitHub

