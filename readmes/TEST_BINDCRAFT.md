# Testing BindCraft Agents

This guide shows how to test your BindCraft peptide design agents.

## Prerequisites

1. **Clone BindCraft** (agent_acad branch):
   ```bash
   cd ~/Desktop/Code
   git clone -b agent_acad https://github.com/msinclair-py/bindcraft.git
   cd bindcraft
   ```

2. **Install dependencies**:
   ```bash
   # If using uv
   uv sync
   
   # Or with pip
   pip install -e .
   ```

3. **Install required tools**:
   - **Chai-1** for structure prediction
   - **ProteinMPNN** for sequence generation

## Testing Individual Agents

### 1. Test Forward Folding Agent

```python
import asyncio
from academy import Agent
from bindcraft.agents import ForwardFoldingAgent  # Adjust import path

async def test_forward_folding():
    # Create agent
    agent = ForwardFoldingAgent()
    
    # Test sequences
    target_seq = "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL"
    binder_seq = "GSGSGS"
    
    # Call action
    result = await agent.fold_initial(
        target_sequence=target_seq,
        binder_sequence=binder_seq,
        trial=1
    )
    
    print(f"✓ Forward folding complete!")
    print(f"  Structure path: {result['structure_path']}")
    print(f"  Confidence: {result.get('confidence', 'N/A')}")
    
    return result

# Run test
asyncio.run(test_forward_folding())
```

### 2. Test Inverse Folding Agent

```python
import asyncio
from bindcraft.agents import InverseFoldingAgent

async def test_inverse_folding():
    agent = InverseFoldingAgent()
    
    # Use structure from forward folding
    structure_path = "path/to/structure.pdb"
    
    result = await agent.generate_sequences(
        structure_path=structure_path,
        num_sequences=10,
        temperature=0.1
    )
    
    print(f"✓ Generated {len(result['sequences'])} sequences")
    for i, seq in enumerate(result['sequences'][:3]):
        print(f"  {i+1}. {seq}")
    
    return result

asyncio.run(test_inverse_folding())
```

### 3. Test Quality Control Agent

```python
import asyncio
from bindcraft.agents import QualityControlAgent

async def test_quality_control():
    agent = QualityControlAgent()
    
    # Test sequences
    sequences = [
        "GSGSGS",
        "MKTAYIAK",
        "AAAAAAAAAAAAAAAAAAAAAA",  # Too long
        "AA",  # Too short
        "GSXGSGS",  # Invalid character
    ]
    
    result = await agent.filter_sequences(
        sequences=sequences,
        min_length=6,
        max_length=20,
        allowed_amino_acids="ACDEFGHIKLMNPQRSTVWY"
    )
    
    print(f"✓ Filtered sequences:")
    print(f"  Input: {len(sequences)} sequences")
    print(f"  Passed: {len(result['passed_sequences'])} sequences")
    print(f"  Failed: {len(result['failed_sequences'])} sequences")
    
    for seq in result['passed_sequences']:
        print(f"    ✓ {seq}")
    
    return result

asyncio.run(test_quality_control())
```

### 4. Test Analysis Agent

```python
import asyncio
from bindcraft.agents import AnalysisAgent

async def test_analysis():
    agent = AnalysisAgent()
    
    # Analyze structure
    structure_path = "path/to/structure.pdb"
    
    result = await agent.analyze_structure(
        structure_path=structure_path,
        metrics=["energy", "contacts", "rmsd"]
    )
    
    print(f"✓ Structure analysis complete:")
    print(f"  Energy: {result.get('energy', 'N/A')}")
    print(f"  Contacts: {result.get('contacts', 'N/A')}")
    print(f"  RMSD: {result.get('rmsd', 'N/A')}")
    
    return result

asyncio.run(test_analysis())
```

## Testing Full Workflow

### Test Coordinator

```python
import asyncio
from bindcraft.agents import PeptideDesignCoordinator

async def test_full_workflow():
    # Create coordinator
    coordinator = PeptideDesignCoordinator()
    
    # Configure workflow
    config = {
        "target_sequence": "MKTAYIAKQRQISFVKSHFSRQLEERLGLIEVQAPILSRVGDGTQDNLSGAEKAVQVKVKALPDAQFEVVHSLAKWKRQTLGQHDFSAGEGLYTHMKALRPDEDRLSPLHSVYVDQWDWERVMGDGERQFSTLKSTVEAIWAGIKATEAAVSEEFGLAPFLPDQIHFVHSQELLSRYPDLDAKGRERAIAKDLGAVFLVGIGGKLSDGHRHDVRAPDYDDWSTPSELGHAGLNGDILVWNPVLEDAFELSSMGIRVDADTLKHQLALTGDEDRLELEWHQALLRGEMPQTIGGGIGQSRLTMLLLQLPHIGQVQAGVWPAAVRESVPSLL",
        "binder_sequence": "GSGSGS",
        "num_rounds": 2,
        "sequences_per_round": 10,
        "min_length": 6,
        "max_length": 20,
        "temperature": 0.1
    }
    
    # Run workflow
    print("Starting peptide design workflow...")
    result = await coordinator.run_full_workflow(**config)
    
    print(f"\n✓ Workflow complete!")
    print(f"  Rounds completed: {result['rounds_completed']}")
    print(f"  Total sequences generated: {result['total_sequences_generated']}")
    print(f"  Total sequences filtered: {result['total_sequences_filtered']}")
    print(f"  Best structures: {len(result.get('best_structures', []))}")
    
    return result

# Run test
asyncio.run(test_full_workflow())
```

## Testing with Redis (Distributed Mode)

If you want to test agents in distributed mode with Redis:

```python
import asyncio
from academy import Agent
from bindcraft.agents import ForwardFoldingAgent

async def test_with_redis():
    # Start agent with Redis backend
    agent = ForwardFoldingAgent(
        redis_host="localhost",
        redis_port=6379
    )
    
    # Launch agent
    await agent.start()
    
    # Get handle
    handle = await agent.get_handle()
    
    # Call action via handle
    result = await handle.fold_initial(
        target_sequence="MKTAYIAK...",
        binder_sequence="GSGSGS",
        trial=1
    )
    
    print(f"✓ Result: {result}")
    
    # Cleanup
    await agent.stop()

asyncio.run(test_with_redis())
```

## Quick Test Script

Create `test_bindcraft.py`:

```python
#!/usr/bin/env python3
"""Quick test script for BindCraft agents."""

import asyncio
import sys

async def test_imports():
    """Test that all agents can be imported."""
    print("Testing imports...")
    try:
        from bindcraft.agents import (
            ForwardFoldingAgent,
            InverseFoldingAgent,
            QualityControlAgent,
            AnalysisAgent,
            PeptideDesignCoordinator
        )
        print("✓ All agents imported successfully")
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

async def test_agent_creation():
    """Test that agents can be instantiated."""
    print("\nTesting agent creation...")
    try:
        from bindcraft.agents import ForwardFoldingAgent
        agent = ForwardFoldingAgent()
        print("✓ Agent created successfully")
        return True
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        return False

async def test_simple_action():
    """Test a simple agent action."""
    print("\nTesting simple action...")
    try:
        from bindcraft.agents import QualityControlAgent
        agent = QualityControlAgent()
        
        result = await agent.filter_sequences(
            sequences=["GSGSGS", "MKTAYIAK"],
            min_length=6,
            max_length=20
        )
        
        print(f"✓ Action executed successfully")
        print(f"  Passed: {len(result['passed_sequences'])} sequences")
        return True
    except Exception as e:
        print(f"✗ Action failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("=" * 50)
    print("BindCraft Agent Tests")
    print("=" * 50)
    
    tests = [
        test_imports(),
        test_agent_creation(),
        test_simple_action()
    ]
    
    results = await asyncio.gather(*tests, return_exceptions=True)
    
    print("\n" + "=" * 50)
    passed = sum(1 for r in results if r is True)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    print("=" * 50)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

Run it:
```bash
cd ~/Desktop/Code/bindcraft
python test_bindcraft.py
```

## Common Issues

### Import Errors

```bash
# Make sure BindCraft is installed
pip install -e .

# Or with uv
uv pip install -e .
```

### Chai-1 Not Found

```bash
# Install Chai-1
pip install chai-lab

# Or follow Chai-1 installation instructions
```

### ProteinMPNN Not Found

```bash
# Clone ProteinMPNN
git clone https://github.com/dauparas/ProteinMPNN.git
cd ProteinMPNN

# Add to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)
```

### Redis Connection Failed

```bash
# Start Redis locally
redis-server &

# Or use Docker
docker run -d -p 6379:6379 redis:latest
```

## Next Steps

Once BindCraft tests pass:

1. **Integrate with Rhea**: Copy working agents to `rhea/agents/peptide_design.py`
2. **Update imports**: Replace placeholder implementations
3. **Test in Rhea**: Use `python -m rhea.preprocess.register_peptide_tools`
4. **Deploy to HPC**: Follow `HPC_QUICKSTART.md`

## Example Test Output

```
==================================================
BindCraft Agent Tests
==================================================
Testing imports...
✓ All agents imported successfully

Testing agent creation...
✓ Agent created successfully

Testing simple action...
✓ Action executed successfully
  Passed: 2 sequences

==================================================
Tests passed: 3/3
==================================================
```

---

**Ready to test!** Start with the quick test script, then move to individual agent tests.

