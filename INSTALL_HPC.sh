#!/bin/bash
# Rhea Installation Script for Supercomputer (No Docker)
# Run this on your HPC login node

set -e  # Exit on error

echo "=========================================="
echo "Rhea HPC Installation Script"
echo "=========================================="
echo ""

# Step 1: Install uv package manager
echo "[1/5] Installing uv package manager..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
    echo "✓ uv installed"
else
    echo "✓ uv already installed"
fi

# Step 2: Install Python dependencies
echo ""
echo "[2/5] Installing Python dependencies..."
uv sync
echo "✓ Dependencies installed"

# Step 3: Create .env file template
echo ""
echo "[3/5] Creating .env configuration file..."
cat > .env << 'EOF'
# ============================================
# Rhea Configuration for HPC
# ============================================

# Database Configuration
# Replace with your HPC PostgreSQL connection string
DATABASE_URL=postgresql+asyncpg://username:password@postgres-host:5432/rhea

# Redis Configuration
# Replace with your HPC Redis host/port
REDIS_HOST=redis-host
REDIS_PORT=6379

# Embedding Service
# Replace with your embedding service endpoint
EMBEDDING_URL=http://embedding-host:8000/v1
EMBEDDING_KEY=
MODEL=Qwen/Qwen3-Embedding-0.6B

# Agent Configuration (for Parsl)
AGENT_REDIS_HOST=redis-host
AGENT_REDIS_PORT=6379

# MinIO/S3 Configuration
# Replace with your HPC object storage endpoint
MINIO_ENDPOINT=minio-host:9000
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key

# Parsl Configuration for HPC
# Options: 'local', 'pbs', 'k8'
PARSL_PROVIDER=pbs
PARSL_CONTAINER_BACKEND=podman
PARSL_MAX_BLOCKS=10
PARSL_INIT_BLOCKS=0
PARSL_MIN_BLOCKS=0
PARSL_NODES_PER_BLOCK=1

# Server Configuration
HOST=0.0.0.0
PORT=3001
EOF

echo "✓ .env file created (EDIT THIS FILE WITH YOUR HPC SETTINGS)"

# Step 4: Create PBS configuration template
echo ""
echo "[4/5] Creating PBS configuration file..."
cat > .env_pbs << 'EOF'
# PBS Configuration
# Edit these values for your HPC cluster

ACCOUNT=your_account_name
QUEUE=your_queue_name
WALLTIME=01:00:00
SCHEDULER_OPTIONS=#PBS -l select=1:ncpus=4:mem=16GB
SELECT_OPTIONS=
WORKER_INIT=module load python/3.10
CPUS_PER_NODE=4
EOF

echo "✓ .env_pbs file created (EDIT THIS FILE WITH YOUR PBS SETTINGS)"

# Step 5: Create activation script
echo ""
echo "[5/5] Creating activation script..."
cat > activate_rhea.sh << 'EOF'
#!/bin/bash
# Activate Rhea environment

# Add uv to PATH
export PATH="$HOME/.local/bin:$PATH"

# Activate virtual environment
source .venv/bin/activate

echo "Rhea environment activated!"
echo ""
echo "Available commands:"
echo "  - Initialize database:     python -m rhea.preprocess.create_custom_tools_table"
echo "  - Register peptide tools:  python -m rhea.preprocess.register_peptide_tools"
echo "  - Start Rhea server:       python -m rhea.server.mcp_server"
echo ""
EOF

chmod +x activate_rhea.sh
echo "✓ Activation script created"

# Create database initialization script
cat > init_database.sh << 'EOF'
#!/bin/bash
# Initialize Rhea database

source activate_rhea.sh

echo "Creating custom tools table..."
python -m rhea.preprocess.create_custom_tools_table

echo ""
echo "Registering peptide design tools..."
python -m rhea.preprocess.register_peptide_tools

echo ""
echo "✓ Database initialized successfully!"
EOF

chmod +x init_database.sh

# Create server start script
cat > start_server.sh << 'EOF'
#!/bin/bash
# Start Rhea MCP server

source activate_rhea.sh

echo "Starting Rhea MCP server..."
python -m rhea.server.mcp_server
EOF

chmod +x start_server.sh

# Create PBS batch script template
cat > submit_rhea.pbs << 'EOF'
#!/bin/bash
#PBS -N rhea-server
#PBS -l select=1:ncpus=8:mem=32GB
#PBS -l walltime=24:00:00
#PBS -q your_queue
#PBS -A your_account

# Load required modules (adjust for your HPC)
module load python/3.10

# Change to working directory
cd $PBS_O_WORKDIR

# Activate Rhea environment
source activate_rhea.sh

# Start Rhea server
python -m rhea.server.mcp_server --host 0.0.0.0 --port 3001
EOF

chmod +x submit_rhea.pbs

echo ""
echo "=========================================="
echo "Installation Complete!"
echo "=========================================="
echo ""
echo "Next Steps:"
echo ""
echo "1. EDIT CONFIGURATION FILES:"
echo "   - Edit .env with your HPC service endpoints"
echo "   - Edit .env_pbs with your PBS settings"
echo "   - Edit submit_rhea.pbs with your job requirements"
echo ""
echo "2. TRANSFER TO SUPERCOMPUTER:"
echo "   scp -r rhea/ your-hpc:~/rhea/"
echo ""
echo "3. ON SUPERCOMPUTER, RUN:"
echo "   cd ~/rhea"
echo "   ./activate_rhea.sh"
echo "   ./init_database.sh"
echo "   ./start_server.sh"
echo ""
echo "   OR submit as batch job:"
echo "   qsub submit_rhea.pbs"
echo ""
echo "=========================================="

