# Running Rhea on Supercomputer (No Docker)

This guide explains how to run Rhea on a supercomputer where Docker is not available.

## Prerequisites

- Python 3.10+
- PostgreSQL with pgvector extension
- Redis server
- MinIO server (or S3-compatible storage)
- Embedding service (Hugging Face TEI or OpenAI-compatible endpoint)

## Step 1: Install Dependencies

```bash
# Install uv (if not already installed)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env

# Install Rhea dependencies
cd /path/to/rhea
uv sync
```

## Step 2: Set Up Services

### Option A: Use Existing HPC Services

Many supercomputers provide PostgreSQL, Redis, and S3 storage as services. Check with your HPC documentation.

### Option B: Run Services Locally (Development)

If you're testing locally first, you can run services without Docker:

#### PostgreSQL with pgvector

```bash
# Install PostgreSQL (if not available)
# On macOS:
brew install postgresql@17

# Start PostgreSQL
brew services start postgresql@17

# Create database
createdb rhea

# Install pgvector extension
# Download from: https://github.com/pgvector/pgvector
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
make install  # May need sudo

# Enable extension
psql rhea -c "CREATE EXTENSION vector;"
```

#### Redis

```bash
# On macOS:
brew install redis
brew services start redis

# On Linux (from source):
wget https://download.redis.io/redis-stable.tar.gz
tar -xzvf redis-stable.tar.gz
cd redis-stable
make
src/redis-server &
```

#### MinIO

```bash
# Download MinIO
wget https://dl.min.io/server/minio/release/darwin-arm64/minio
chmod +x minio

# Start MinIO
./minio server /path/to/data --console-address ":9001" &

# Default credentials:
# Access Key: minioadmin
# Secret Key: minioadmin
```

#### Embedding Service (Hugging Face TEI)

For supercomputers, you'll likely want to use a remote embedding service or run it on a GPU node:

```bash
# If you have access to a GPU node, you can run TEI:
# Download the binary from: https://github.com/huggingface/text-embeddings-inference

# Or use a Python-based alternative:
pip install sentence-transformers

# Then create a simple FastAPI server (see embedding_server.py below)
```

## Step 3: Configure Environment

Create a `.env` file in the rhea directory:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/rhea

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Embedding Service
EMBEDDING_URL=http://localhost:8000/v1
EMBEDDING_KEY=
MODEL=Qwen/Qwen3-Embedding-0.6B

# Agent Configuration (for Parsl)
AGENT_REDIS_HOST=localhost
AGENT_REDIS_PORT=6379

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# Parsl Configuration
PARSL_CONTAINER_BACKEND=podman  # Use 'podman' if available, or configure for HPC
PARSL_PROVIDER=local  # Change to 'pbs' or 'k8' for HPC
PARSL_MAX_BLOCKS=5
```

### For PBS/Slurm Supercomputers

If your supercomputer uses PBS or Slurm, create additional config files:

**`.env_pbs`** (for PBS):
```bash
ACCOUNT=your_account
QUEUE=your_queue
WALLTIME=01:00:00
SCHEDULER_OPTIONS=#PBS -l select=1:ncpus=4:mem=16GB
SELECT_OPTIONS=
WORKER_INIT=module load python/3.10
CPUS_PER_NODE=4
```

Then update `.env`:
```bash
PARSL_PROVIDER=pbs
```

## Step 4: Initialize Database

```bash
# Activate virtual environment
source .venv/bin/activate

# Create custom tools table
python -m rhea.preprocess.create_custom_tools_table

# Register peptide design tools
python -m rhea.preprocess.register_peptide_tools
```

## Step 5: Run Rhea Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Run server
python -m rhea.server.mcp_server
```

The server will start on `http://localhost:3001` by default.

## Step 6: Test the Setup

Create a test script `test_rhea.py`:

```python
import asyncio
from rhea.client import RheaClient

async def test():
    async with RheaClient('localhost', 3001) as client:
        # Test tool discovery
        print("Testing tool discovery...")
        await client.find_tools("peptide design")
        
        # List tools
        tools = await client.list_tools()
        print(f"Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.get('name', 'Unknown')}")

if __name__ == "__main__":
    asyncio.run(test())
```

Run it:
```bash
source .venv/bin/activate
python test_rhea.py
```

## Supercomputer-Specific Configuration

### Running Without Containers

If you can't use Docker/Podman at all, you need to configure Parsl to run tools directly:

Update `.env`:
```bash
PARSL_CONTAINER_BACKEND=none  # This will need code changes
```

**Note**: This requires modifying `rhea/manager/parsl_config.py` to support non-containerized execution. This is more complex and may require custom implementation.

### Using Conda Environments Instead of Containers

A better approach for HPC is to use conda environments:

1. Create conda environments for each tool
2. Modify the agent launcher to activate the appropriate conda environment
3. Run tools directly in those environments

This is what the `RheaToolAgent` does with the `conda-pack` functionality.

### PBS/Slurm Integration

Rhea supports PBS and Kubernetes providers through Parsl. Configure in `.env`:

```bash
# For PBS
PARSL_PROVIDER=pbs
PARSL_INIT_BLOCKS=0
PARSL_MIN_BLOCKS=0
PARSL_MAX_BLOCKS=10
PARSL_NODES_PER_BLOCK=1
```

Then create `.env_pbs` with your cluster-specific settings.

## Troubleshooting

### PostgreSQL Connection Issues

```bash
# Check PostgreSQL is running
pg_isready

# Check connection
psql -U postgres -d rhea -c "SELECT 1;"
```

### Redis Connection Issues

```bash
# Check Redis is running
redis-cli ping
# Should return: PONG
```

### MinIO Connection Issues

```bash
# Check MinIO is accessible
curl http://localhost:9000/minio/health/live
```

### Embedding Service Issues

If you don't have access to a GPU for TEI, you can create a simple embedding server:

**`embedding_server.py`**:
```python
from fastapi import FastAPI
from sentence_transformers import SentenceTransformer
from pydantic import BaseModel
from typing import List

app = FastAPI()
model = SentenceTransformer('Qwen/Qwen3-Embedding-0.6B')

class EmbeddingRequest(BaseModel):
    input: str | List[str]
    model: str = "Qwen/Qwen3-Embedding-0.6B"

@app.post("/v1/embeddings")
async def create_embedding(request: EmbeddingRequest):
    texts = [request.input] if isinstance(request.input, str) else request.input
    embeddings = model.encode(texts).tolist()
    
    return {
        "data": [
            {"embedding": emb, "index": i}
            for i, emb in enumerate(embeddings)
        ],
        "model": request.model,
        "usage": {"total_tokens": sum(len(t.split()) for t in texts)}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

Run it:
```bash
pip install sentence-transformers fastapi uvicorn
python embedding_server.py
```

## Performance Tips for HPC

1. **Use Local Storage**: Configure MinIO to use fast local storage (e.g., `/scratch`)
2. **Redis on Compute Nodes**: Run Redis on the same node as Rhea for low latency
3. **Batch Jobs**: Submit Rhea server as a batch job for long-running workflows
4. **Resource Allocation**: Request appropriate resources based on tool requirements

## Example Batch Script (PBS)

```bash
#!/bin/bash
#PBS -N rhea-server
#PBS -l select=1:ncpus=8:mem=32GB
#PBS -l walltime=24:00:00
#PBS -q your_queue

# Load modules
module load python/3.10
module load postgresql/17
module load redis

# Start services
redis-server --daemonize yes
./minio server /scratch/$USER/minio-data &

# Activate environment
cd $PBS_O_WORKDIR
source .venv/bin/activate

# Run Rhea
python -m rhea.server.mcp_server --host 0.0.0.0 --port 3001
```

## Next Steps

1. Test basic functionality with the test script
2. Register your peptide design tools
3. Configure for your specific HPC environment
4. Submit batch jobs for long-running workflows

For more details, see:
- `PEPTIDE_TOOLS_SETUP.md` - Setting up peptide design tools
- `docs/custom_tools.md` - Adding custom tools
- `docs/configuration.md` - Full configuration reference

