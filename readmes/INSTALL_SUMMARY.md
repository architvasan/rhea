# Rhea HPC Installation - Complete Summary

## What We Built

You now have a **complete custom tools framework** for Rhea that allows you to:

1. ✅ Add Academy agents as MCP tools (bypassing Galaxy XML format)
2. ✅ Use RAG-based discovery to find tools with natural language
3. ✅ Run peptide design workflows (ForwardFolding, InverseFolding, QC, Analysis)
4. ✅ Deploy on supercomputers without Docker
5. ✅ Integrate with PBS/Slurm job schedulers

## Installation on Your Laptop (Prep for HPC)

```bash
cd ~/Desktop/Code/rhea

# 1. Run installation script
./INSTALL_HPC.sh

# 2. Edit configuration files
nano .env          # Update with HPC service endpoints
nano .env_pbs      # Update with PBS cluster settings
nano submit_rhea.pbs  # Update job requirements

# 3. Transfer to supercomputer
scp -r ~/Desktop/Code/rhea/ username@your-hpc.edu:~/
```

## Installation on Supercomputer

```bash
# SSH to HPC
ssh username@your-hpc.edu
cd ~/rhea

# Activate environment
./activate_rhea.sh

# Initialize database (first time only)
./init_database.sh

# Start server
./start_server.sh

# OR submit as batch job
qsub submit_rhea.pbs
```

## Configuration Files to Edit

### `.env` - Service Endpoints

Replace these with your HPC service endpoints:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@hpc-postgres:5432/rhea

# Redis
REDIS_HOST=hpc-redis
REDIS_PORT=6379

# Embedding Service
EMBEDDING_URL=http://hpc-embedding:8000/v1

# MinIO/S3
MINIO_ENDPOINT=hpc-minio:9000
MINIO_ACCESS_KEY=your-key
MINIO_SECRET_KEY=your-secret

# Parsl (for HPC)
PARSL_PROVIDER=pbs
PARSL_CONTAINER_BACKEND=podman
```

### `.env_pbs` - PBS Settings

Replace with your cluster settings:

```bash
ACCOUNT=your_account_name
QUEUE=your_queue_name
WALLTIME=01:00:00
SCHEDULER_OPTIONS=#PBS -l select=1:ncpus=4:mem=16GB
WORKER_INIT=module load python/3.10
CPUS_PER_NODE=4
```

### `submit_rhea.pbs` - Batch Job

Replace with your job requirements:

```bash
#PBS -N rhea-server
#PBS -l select=1:ncpus=8:mem=32GB
#PBS -l walltime=24:00:00
#PBS -q your_queue
#PBS -A your_account
```

## What Gets Installed

### Python Packages (via `uv sync`)
- `academy-py` - Academy agent framework
- `fastapi` - MCP server
- `sqlalchemy` + `asyncpg` - Database
- `redis` - Caching and agent communication
- `parsl` - HPC job execution
- `proxystore` - File transfer
- `openai` - Embedding client
- All other dependencies

### Helper Scripts
- `activate_rhea.sh` - Activate Python environment
- `init_database.sh` - Create tables and register tools
- `start_server.sh` - Start Rhea server
- `submit_rhea.pbs` - PBS batch job template

### Custom Tools Framework
- `rhea/utils/custom_tool_schema.py` - Tool schema
- `rhea/utils/models.py` - Database models (CustomToolModel)
- `rhea/server/custom_tool_utils.py` - MCP tool builder
- `rhea/utils/embedding.py` - RAG search (combined Galaxy + custom tools)
- `rhea/server/mcp_server.py` - Updated to search both tool types

### Peptide Design Agents
- `rhea/agents/peptide_design.py` - Agent implementations
- `rhea/preprocess/register_peptide_tools.py` - Tool registration

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Rhea MCP Server                         │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  find_tools(query) - RAG-based Discovery              │  │
│  │    ↓                                                   │  │
│  │  Embed query → Search PostgreSQL (pgvector)           │  │
│  │    ↓                                                   │  │
│  │  Return: Galaxy Tools + Custom Tools                  │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │  Galaxy Tools    │  │  Custom Tools (Academy)      │    │
│  │  (galaxytools)   │  │  (customtools)               │    │
│  │                  │  │                              │    │
│  │  - XML format    │  │  - CustomTool schema         │    │
│  │  - Conda envs    │  │  - @action methods           │    │
│  │  - Containers    │  │  - Direct execution          │    │
│  └──────────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                     │
│  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │  galaxytools     │  │  customtools                 │    │
│  │  - id            │  │  - id                        │    │
│  │  - name          │  │  - name                      │    │
│  │  - definition    │  │  - tool_type                 │    │
│  │  - embedding     │  │  - definition (JSONB)        │    │
│  │                  │  │  - embedding (vector 1024)   │    │
│  └──────────────────┘  └──────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────┐
│                    Parsl Execution Layer                     │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  PBS Provider → Submit jobs to HPC scheduler          │  │
│  │  Podman Backend → Run containerized tools             │  │
│  │  ProxyStore → Transfer files via Redis                │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Testing the Installation

### 1. Test Embedding Service

```bash
source activate_rhea.sh

python << EOF
import asyncio
from rhea.utils.embedding import get_embedding_client

async def test():
    client = get_embedding_client()
    result = await client.embed(["test"])
    print(f"✓ Embedding dimension: {len(result[0])}")

asyncio.run(test())
EOF
```

### 2. Test Database Connection

```bash
source activate_rhea.sh

python << EOF
from sqlalchemy import create_engine
from rhea.server.schema import settings

engine = create_engine(settings.database_url.replace('+asyncpg', ''))
with engine.connect() as conn:
    result = conn.execute("SELECT 1")
    print("✓ Database connected")
EOF
```

### 3. Test Tool Discovery

```bash
source activate_rhea.sh

python << EOF
import asyncio
from rhea.utils.embedding import get_l2_distance_combined, get_embedding_client
from rhea.utils.models import get_session

async def test():
    client = get_embedding_client()
    query_vec = (await client.embed(["peptide design"]))[0]
    
    async with get_session() as session:
        galaxy_tools, custom_tools = await get_l2_distance_combined(
            query_vec, session, limit=5
        )
        print(f"✓ Found {len(galaxy_tools)} Galaxy tools")
        print(f"✓ Found {len(custom_tools)} custom tools")
        for tool in custom_tools:
            print(f"  - {tool.name}")

asyncio.run(test())
EOF
```

## Next Steps

### 1. Connect Real BindCraft Agents

Replace placeholder implementations in `rhea/agents/peptide_design.py`:

```python
# Current: Placeholder implementations
# TODO: Import from https://github.com/msinclair-py/bindcraft/tree/agent_acad

from bindcraft.agents import (
    ForwardFoldingAgent,
    InverseFoldingAgent,
    QualityControlAgent,
    AnalysisAgent
)
```

### 2. Add More Custom Tools

Use the framework to add more tools:

```python
# rhea/preprocess/register_my_tools.py
from rhea.utils.custom_tool_schema import CustomTool, CustomToolParameter

tool = CustomTool(
    id="my_custom_tool",
    name="My Custom Tool",
    version="1.0.0",
    description="Does something amazing",
    tool_type="academy_agent",
    agent_class="rhea.agents.my_agents.MyAgent",
    action_name="my_action",
    parameters=[...],
    outputs=[...],
    requirements={...}
)

# Register it
await register_custom_tool(tool, session)
```

### 3. Configure for Production

- Adjust PBS resource requests in `submit_rhea.pbs`
- Set appropriate walltime for long-running workflows
- Configure Parsl max_blocks based on cluster limits
- Set up monitoring and logging

## Troubleshooting

### Common Issues

**Database connection failed:**
```bash
# Check PostgreSQL
psql -h $DATABASE_HOST -U $DATABASE_USER -d rhea -c "SELECT 1;"
```

**Redis connection failed:**
```bash
# Check Redis
redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
```

**Embedding service failed:**
```bash
# Test endpoint
curl $EMBEDDING_URL/embeddings -H "Content-Type: application/json" \
  -d '{"input": "test", "model": "Qwen/Qwen3-Embedding-0.6B"}'
```

**PBS job not starting:**
```bash
# Check job status
qstat -u $USER

# View logs
cat rhea-server.o*
cat rhea-server.e*
```

## Documentation

- **`README_HPC.md`** - Quick reference
- **`HPC_QUICKSTART.md`** - Step-by-step guide
- **`SUPERCOMPUTER_SETUP.md`** - Detailed HPC setup
- **`PEPTIDE_TOOLS_SETUP.md`** - Peptide design workflow
- **`docs/custom_tools.md`** - Adding custom tools
- **`WALKTHROUGH.md`** - Implementation details

## Summary

You're all set! Here's what to do:

1. ✅ Run `./INSTALL_HPC.sh` on your laptop
2. ✅ Edit `.env`, `.env_pbs`, `submit_rhea.pbs`
3. ✅ Transfer to supercomputer: `scp -r rhea/ user@hpc:~/`
4. ✅ On HPC: `./activate_rhea.sh && ./init_database.sh && ./start_server.sh`

The custom tools framework is ready to use. You can now:
- Discover tools with natural language queries
- Run peptide design workflows
- Add your own Academy agents as tools
- Deploy on HPC without Docker

Good luck! 🚀

