# Rhea HPC Quick Start Guide

This is a streamlined guide for installing and running Rhea on your supercomputer.

## Prerequisites on HPC

Your supercomputer should have these services available:
- PostgreSQL with pgvector extension
- Redis
- MinIO or S3-compatible storage
- Embedding service endpoint
- Python 3.10+
- (Optional) Podman for containerized tools

## Installation

### On Your Laptop

1. **Clone your fork:**
   ```bash
   cd ~/Desktop/Code
   git clone https://github.com/architvasan/rhea.git
   cd rhea
   ```

2. **Run installation script:**
   ```bash
   chmod +x INSTALL_HPC.sh
   ./INSTALL_HPC.sh
   ```

3. **Edit configuration files:**
   
   **`.env`** - Update with your HPC service endpoints:
   ```bash
   DATABASE_URL=postgresql+asyncpg://user:pass@hpc-postgres:5432/rhea
   REDIS_HOST=hpc-redis
   REDIS_PORT=6379
   MINIO_ENDPOINT=hpc-minio:9000
   MINIO_ACCESS_KEY=your-key
   MINIO_SECRET_KEY=your-secret
   EMBEDDING_URL=http://hpc-embedding:8000/v1
   ```

   **`.env_pbs`** - Update with your PBS settings:
   ```bash
   ACCOUNT=your_account
   QUEUE=your_queue
   WALLTIME=01:00:00
   SCHEDULER_OPTIONS=#PBS -l select=1:ncpus=4:mem=16GB
   WORKER_INIT=module load python/3.10
   ```

   **`submit_rhea.pbs`** - Update job requirements:
   ```bash
   #PBS -q your_queue
   #PBS -A your_account
   ```

4. **Transfer to supercomputer:**
   ```bash
   # From your laptop
   cd ~/Desktop/Code
   scp -r rhea/ username@your-hpc.edu:~/
   ```

### On Your Supercomputer

1. **SSH to your HPC:**
   ```bash
   ssh username@your-hpc.edu
   cd ~/rhea
   ```

2. **Activate environment:**
   ```bash
   ./activate_rhea.sh
   ```

3. **Initialize database (first time only):**
   ```bash
   ./init_database.sh
   ```
   
   This will:
   - Create the `customtools` table in PostgreSQL
   - Register peptide design tools
   - Generate embeddings for tool discovery

4. **Start Rhea server:**
   
   **Option A: Interactive (for testing):**
   ```bash
   ./start_server.sh
   ```
   
   **Option B: Batch job (for production):**
   ```bash
   qsub submit_rhea.pbs
   ```

## Verify Installation

Once the server is running, test it:

```bash
# Activate environment
source activate_rhea.sh

# Create test script
cat > test_rhea.py << 'EOF'
import asyncio
from rhea.utils.embedding import get_embedding_client

async def test():
    print("Testing embedding service...")
    client = get_embedding_client()
    result = await client.embed(["test query"])
    print(f"✓ Embedding service working! Dimension: {len(result[0])}")

asyncio.run(test())
EOF

# Run test
python test_rhea.py
```

## Using Rhea

### Find Tools

```python
from rhea.client import RheaClient

async with RheaClient('localhost', 3001) as client:
    # Search for peptide design tools
    await client.find_tools("peptide design")
    
    # List all available tools
    tools = await client.list_tools()
```

### Run Peptide Design Workflow

```python
# Forward folding
result = await client.call_tool(
    "peptide_forward_fold_initial",
    target_sequence="MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL",
    binder_sequence="GSGSGS",
    trial=1
)

# Inverse folding
sequences = await client.call_tool(
    "peptide_inverse_fold",
    structure_path=result["structure_path"],
    num_sequences=10
)

# Quality control
filtered = await client.call_tool(
    "peptide_quality_control",
    sequences=sequences["sequences"],
    min_length=6,
    max_length=20
)
```

## Troubleshooting

### Database Connection Failed

```bash
# Check PostgreSQL is accessible
psql -h hpc-postgres -U username -d rhea -c "SELECT 1;"

# Verify pgvector extension
psql -h hpc-postgres -U username -d rhea -c "SELECT * FROM pg_extension WHERE extname='vector';"
```

### Redis Connection Failed

```bash
# Check Redis is accessible
redis-cli -h hpc-redis -p 6379 ping
```

### Embedding Service Failed

```bash
# Test embedding endpoint
curl http://hpc-embedding:8000/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"input": "test", "model": "Qwen/Qwen3-Embedding-0.6B"}'
```

### PBS Job Not Starting

```bash
# Check job status
qstat -u $USER

# View job output
cat rhea-server.o<jobid>
cat rhea-server.e<jobid>

# Check queue limits
qstat -Q
```

## File Structure

After installation, you'll have:

```
rhea/
├── .env                    # HPC service configuration
├── .env_pbs               # PBS cluster settings
├── activate_rhea.sh       # Environment activation script
├── init_database.sh       # Database initialization script
├── start_server.sh        # Server start script
├── submit_rhea.pbs        # PBS batch job script
├── rhea/                  # Rhea source code
│   ├── agents/           # Custom agents (peptide design)
│   ├── server/           # MCP server
│   ├── utils/            # Utilities (embedding, schema)
│   └── preprocess/       # Database setup scripts
└── .venv/                # Python virtual environment
```

## Configuration Reference

### Environment Variables (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://user:pass@host:5432/rhea` |
| `REDIS_HOST` | Redis hostname | `hpc-redis` |
| `REDIS_PORT` | Redis port | `6379` |
| `EMBEDDING_URL` | Embedding service endpoint | `http://hpc-embedding:8000/v1` |
| `MINIO_ENDPOINT` | MinIO/S3 endpoint | `hpc-minio:9000` |
| `PARSL_PROVIDER` | Execution provider | `pbs`, `local`, or `k8` |
| `PARSL_CONTAINER_BACKEND` | Container runtime | `podman` or `docker` |

### PBS Settings (.env_pbs)

| Variable | Description | Example |
|----------|-------------|---------|
| `ACCOUNT` | PBS account/project | `your_project` |
| `QUEUE` | PBS queue name | `regular` |
| `WALLTIME` | Job walltime | `01:00:00` |
| `SCHEDULER_OPTIONS` | PBS resource requests | `#PBS -l select=1:ncpus=4:mem=16GB` |
| `WORKER_INIT` | Module loads | `module load python/3.10` |

## Next Steps

1. **Connect BindCraft agents**: Replace placeholder implementations in `rhea/agents/peptide_design.py` with actual BindCraft code
2. **Add more tools**: Use `docs/custom_tools.md` to add additional custom tools
3. **Configure for production**: Adjust PBS settings for long-running workflows
4. **Monitor performance**: Check logs and resource usage

## Support

- Documentation: `docs/`
- Custom tools guide: `docs/custom_tools.md`
- Peptide tools setup: `PEPTIDE_TOOLS_SETUP.md`
- Full HPC setup: `SUPERCOMPUTER_SETUP.md`

