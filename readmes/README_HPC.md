# Rhea for HPC - Installation Summary

## Quick Install (3 Steps)

### 1. Run Installation Script
```bash
./INSTALL_HPC.sh
```

This will:
- Install `uv` package manager
- Install all Python dependencies
- Create configuration templates (`.env`, `.env_pbs`, `submit_rhea.pbs`)
- Create helper scripts (`activate_rhea.sh`, `init_database.sh`, `start_server.sh`)

### 2. Edit Configuration Files

**`.env`** - Update with your HPC endpoints:
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@your-postgres:5432/rhea
REDIS_HOST=your-redis-host
MINIO_ENDPOINT=your-minio:9000
EMBEDDING_URL=http://your-embedding-service:8000/v1
```

**`.env_pbs`** - Update with your cluster settings:
```bash
ACCOUNT=your_account
QUEUE=your_queue
WALLTIME=01:00:00
```

### 3. Transfer to Supercomputer
```bash
scp -r rhea/ username@your-hpc.edu:~/
```

## On Supercomputer

```bash
# SSH to HPC
ssh username@your-hpc.edu
cd ~/rhea

# Initialize (first time only)
./activate_rhea.sh
./init_database.sh

# Start server
./start_server.sh

# OR submit as batch job
qsub submit_rhea.pbs
```

## What You Get

✅ **Custom Tools Framework** - Add Academy agents as MCP tools  
✅ **Peptide Design Agents** - ForwardFolding, InverseFolding, QC, Analysis  
✅ **RAG-based Tool Discovery** - Find tools with natural language queries  
✅ **HPC Integration** - PBS/Slurm support via Parsl  
✅ **No Docker Required** - Runs natively on supercomputers  

## Files Created

| File | Purpose |
|------|---------|
| `INSTALL_HPC.sh` | Installation script |
| `.env` | Service configuration (EDIT THIS) |
| `.env_pbs` | PBS settings (EDIT THIS) |
| `activate_rhea.sh` | Activate environment |
| `init_database.sh` | Initialize database |
| `start_server.sh` | Start server |
| `submit_rhea.pbs` | PBS batch script (EDIT THIS) |

## Documentation

- **Quick Start**: `HPC_QUICKSTART.md` - Step-by-step guide
- **Full Setup**: `SUPERCOMPUTER_SETUP.md` - Detailed HPC setup
- **Custom Tools**: `docs/custom_tools.md` - Add your own tools
- **Peptide Tools**: `PEPTIDE_TOOLS_SETUP.md` - Peptide design workflow

## Need Help?

1. Check `HPC_QUICKSTART.md` for common issues
2. Verify service endpoints in `.env`
3. Check PBS logs: `cat rhea-server.e*`

---

**Ready to go!** Just run `./INSTALL_HPC.sh` and edit the config files.

