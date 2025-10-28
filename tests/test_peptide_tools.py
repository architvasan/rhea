#!/usr/bin/env python3
"""
Test script for BindCraft peptide design tools in Rhea.

This tests the custom tools framework integration with peptide design agents.
"""

import asyncio
import sys
from typing import List

# Test 1: Import custom tool modules
async def test_imports():
    """Test that all custom tool modules can be imported."""
    print("=" * 60)
    print("Test 1: Importing custom tool modules")
    print("=" * 60)
    
    try:
        from rhea.utils.custom_tool_schema import (
            CustomTool,
            CustomToolParameter,
            CustomToolOutput,
            CustomToolRequirements
        )
        print("✓ Custom tool schema imported")
        
        from rhea.utils.models import CustomToolModel
        print("✓ CustomToolModel imported")
        
        from rhea.server.custom_tool_utils import create_custom_tool
        print("✓ create_custom_tool imported")
        
        from rhea.agents.peptide_design import (
            ForwardFoldingAgent,
            InverseFoldingAgent,
            QualityControlAgent,
            AnalysisAgent,
            PeptideDesignCoordinator
        )
        print("✓ Peptide design agents imported")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False


# Test 2: Test agent instantiation
async def test_agent_creation():
    """Test that peptide design agents can be created."""
    print("\n" + "=" * 60)
    print("Test 2: Creating peptide design agents")
    print("=" * 60)
    
    try:
        from rhea.agents.peptide_design import (
            ForwardFoldingAgent,
            InverseFoldingAgent,
            QualityControlAgent,
            AnalysisAgent
        )
        
        agents = {
            "ForwardFolding": ForwardFoldingAgent(),
            "InverseFolding": InverseFoldingAgent(),
            "QualityControl": QualityControlAgent(),
            "Analysis": AnalysisAgent()
        }
        
        for name, agent in agents.items():
            print(f"✓ {name}Agent created")
        
        return True
    except Exception as e:
        print(f"✗ Agent creation failed: {e}")
        return False


# Test 3: Test database connection
async def test_database_connection():
    """Test connection to PostgreSQL database."""
    print("\n" + "=" * 60)
    print("Test 3: Testing database connection")
    print("=" * 60)
    
    try:
        from rhea.utils.models import get_session
        from sqlalchemy import text
        
        async with get_session() as session:
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("✓ Database connection successful")
                return True
            else:
                print("✗ Database query returned unexpected result")
                return False
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        print("  Make sure DATABASE_URL is set in .env")
        return False


# Test 4: Test custom tools table exists
async def test_custom_tools_table():
    """Test that customtools table exists in database."""
    print("\n" + "=" * 60)
    print("Test 4: Checking customtools table")
    print("=" * 60)
    
    try:
        from rhea.utils.models import get_session
        from sqlalchemy import text
        
        async with get_session() as session:
            # Check if table exists
            result = await session.execute(text(
                "SELECT EXISTS (SELECT FROM information_schema.tables "
                "WHERE table_name = 'customtools')"
            ))
            exists = result.fetchone()[0]
            
            if exists:
                print("✓ customtools table exists")
                
                # Check if pgvector extension is enabled
                result = await session.execute(text(
                    "SELECT EXISTS (SELECT FROM pg_extension WHERE extname = 'vector')"
                ))
                vector_exists = result.fetchone()[0]
                
                if vector_exists:
                    print("✓ pgvector extension enabled")
                else:
                    print("⚠ pgvector extension not found")
                
                return True
            else:
                print("✗ customtools table does not exist")
                print("  Run: python -m rhea.preprocess.create_custom_tools_table")
                return False
    except Exception as e:
        print(f"✗ Table check failed: {e}")
        return False


# Test 5: Test peptide tools registration
async def test_peptide_tools_registered():
    """Test that peptide design tools are registered in database."""
    print("\n" + "=" * 60)
    print("Test 5: Checking peptide tools registration")
    print("=" * 60)
    
    try:
        from rhea.utils.models import get_session, CustomToolModel
        from sqlalchemy import select
        
        expected_tools = [
            "peptide_forward_fold_initial",
            "peptide_inverse_fold",
            "peptide_quality_control",
            "peptide_analyze_structure"
        ]
        
        async with get_session() as session:
            result = await session.execute(
                select(CustomToolModel.id).where(
                    CustomToolModel.id.in_(expected_tools)
                )
            )
            registered_ids = [row[0] for row in result.fetchall()]
            
            print(f"Found {len(registered_ids)}/{len(expected_tools)} peptide tools:")
            for tool_id in expected_tools:
                if tool_id in registered_ids:
                    print(f"  ✓ {tool_id}")
                else:
                    print(f"  ✗ {tool_id} (not registered)")
            
            if len(registered_ids) == len(expected_tools):
                print("✓ All peptide tools registered")
                return True
            else:
                print("⚠ Some tools missing")
                print("  Run: python -m rhea.preprocess.register_peptide_tools")
                return False
    except Exception as e:
        print(f"✗ Registration check failed: {e}")
        return False


# Test 6: Test embedding service
async def test_embedding_service():
    """Test connection to embedding service."""
    print("\n" + "=" * 60)
    print("Test 6: Testing embedding service")
    print("=" * 60)
    
    try:
        from rhea.utils.embedding import get_embedding_client
        
        client = get_embedding_client()
        result = await client.embed(["test query for peptide design"])
        
        if result and len(result) > 0 and len(result[0]) > 0:
            print(f"✓ Embedding service working")
            print(f"  Embedding dimension: {len(result[0])}")
            return True
        else:
            print("✗ Embedding service returned empty result")
            return False
    except Exception as e:
        print(f"✗ Embedding service failed: {e}")
        print("  Make sure EMBEDDING_URL is set in .env")
        return False


# Test 7: Test tool discovery (RAG search)
async def test_tool_discovery():
    """Test RAG-based tool discovery for peptide design."""
    print("\n" + "=" * 60)
    print("Test 7: Testing tool discovery (RAG search)")
    print("=" * 60)
    
    try:
        from rhea.utils.embedding import get_l2_distance_combined, get_embedding_client
        from rhea.utils.models import get_session
        
        # Generate query embedding
        client = get_embedding_client()
        query_vec = (await client.embed(["peptide design binder"]))[0]
        
        # Search for tools
        async with get_session() as session:
            galaxy_tools, custom_tools = await get_l2_distance_combined(
                query_vec, session, limit=10
            )
            
            print(f"✓ Search completed")
            print(f"  Galaxy tools found: {len(galaxy_tools)}")
            print(f"  Custom tools found: {len(custom_tools)}")
            
            if len(custom_tools) > 0:
                print(f"\n  Custom tools discovered:")
                for tool in custom_tools[:5]:
                    print(f"    - {tool.name} ({tool.id})")
                return True
            else:
                print("⚠ No custom tools found in search")
                print("  Make sure peptide tools are registered")
                return False
    except Exception as e:
        print(f"✗ Tool discovery failed: {e}")
        return False


# Test 8: Test custom tool schema validation
async def test_tool_schema():
    """Test that peptide tools have valid schema."""
    print("\n" + "=" * 60)
    print("Test 8: Validating tool schemas")
    print("=" * 60)
    
    try:
        from rhea.utils.models import get_session, CustomToolModel
        from rhea.utils.custom_tool_schema import CustomTool
        from sqlalchemy import select
        
        async with get_session() as session:
            result = await session.execute(
                select(CustomToolModel).where(
                    CustomToolModel.id == "peptide_forward_fold_initial"
                )
            )
            tool_model = result.scalar_one_or_none()
            
            if tool_model:
                # Validate schema
                tool = tool_model.definition
                
                print(f"✓ Tool schema loaded: {tool.name}")
                print(f"  ID: {tool.id}")
                print(f"  Version: {tool.version}")
                print(f"  Type: {tool.tool_type}")
                print(f"  Parameters: {len(tool.parameters)}")
                print(f"  Outputs: {len(tool.outputs)}")
                
                # Check required fields
                assert tool.id, "Tool ID missing"
                assert tool.name, "Tool name missing"
                assert tool.agent_class, "Agent class missing"
                assert tool.action_name, "Action name missing"
                assert len(tool.parameters) > 0, "No parameters defined"
                
                print("✓ Schema validation passed")
                return True
            else:
                print("✗ Tool not found in database")
                return False
    except Exception as e:
        print(f"✗ Schema validation failed: {e}")
        return False


# Test 9: Test MCP tool creation
async def test_mcp_tool_creation():
    """Test that custom tools can be converted to MCP tools."""
    print("\n" + "=" * 60)
    print("Test 9: Testing MCP tool creation")
    print("=" * 60)
    
    try:
        from rhea.utils.models import get_session, CustomToolModel
        from rhea.server.custom_tool_utils import create_custom_tool
        from sqlalchemy import select
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.files = {}
        
        ctx = MockContext()
        
        async with get_session() as session:
            result = await session.execute(
                select(CustomToolModel).where(
                    CustomToolModel.id == "peptide_quality_control"
                )
            )
            tool_model = result.scalar_one_or_none()
            
            if tool_model:
                tool = tool_model.definition
                mcp_tool = create_custom_tool(tool, ctx)
                
                print(f"✓ MCP tool created: {mcp_tool.name}")
                print(f"  Description: {mcp_tool.description[:60]}...")
                print(f"  Input schema defined: {bool(mcp_tool.inputSchema)}")
                
                return True
            else:
                print("✗ Tool not found")
                return False
    except Exception as e:
        print(f"✗ MCP tool creation failed: {e}")
        return False


# Main test runner
async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("RHEA PEPTIDE DESIGN TOOLS TEST SUITE")
    print("=" * 60)
    print()
    
    tests = [
        ("Imports", test_imports()),
        ("Agent Creation", test_agent_creation()),
        ("Database Connection", test_database_connection()),
        ("Custom Tools Table", test_custom_tools_table()),
        ("Peptide Tools Registration", test_peptide_tools_registered()),
        ("Embedding Service", test_embedding_service()),
        ("Tool Discovery", test_tool_discovery()),
        ("Tool Schema", test_tool_schema()),
        ("MCP Tool Creation", test_mcp_tool_creation()),
    ]
    
    results = []
    for name, test_coro in tests:
        try:
            result = await test_coro
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 All tests passed! Peptide design tools are ready to use.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. See output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))

