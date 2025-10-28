from sqlalchemy import Column, String, Index, Text, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from pgvector.sqlalchemy import Vector
from typing import List
from .schema import Tool
from .custom_tool_schema import CustomTool

Base = declarative_base()


class GalaxyTool(Base):
    __tablename__ = "galaxytools"
    __table_args__ = (
        Index(
            "ix_galaxytools_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    user_provided_name = Column(String)
    description = Column(Text)
    long_description = Column(Text)
    documentation = Column(Text)
    _definition = Column("definition", JSONB, nullable=False)
    embedding = Column(Vector(1024), nullable=False)

    @property
    def definition(self) -> Tool:
        return Tool.model_validate(self._definition)

    @definition.setter
    def definition(self, t: Tool | dict):
        if isinstance(t, Tool):
            self._definition = t.model_dump()
        else:
            self._definition = Tool.model_validate(t).model_dump()


async def get_galaxytool_by_id(session: AsyncSession, tool_id: str) -> Tool | None:
    statement = select(GalaxyTool).where(GalaxyTool.id == tool_id)
    result = await session.execute(statement)
    row = result.scalar_one_or_none()
    if row is None:
        return row
    return row.definition


async def get_galaxytool_by_name(session: AsyncSession, tool_name: str) -> Tool | None:
    statement = select(GalaxyTool).where(GalaxyTool.name == tool_name)
    result = await session.execute(statement)
    row = result.scalars().first()
    if row is None:
        return None
    return row.definition


async def get_all_tool_ids(session: AsyncSession) -> List[str] | None:
    statement = select(GalaxyTool.id)
    result = await session.execute(statement)
    tool_ids = [row[0] for row in result.fetchall()]
    return tool_ids if tool_ids else None


class CustomToolModel(Base):
    """Database model for custom (non-Galaxy) tools like Academy agents."""

    __tablename__ = "customtools"
    __table_args__ = (
        Index(
            "ix_customtools_embedding",
            "embedding",
            postgresql_using="ivfflat",
            postgresql_ops={"embedding": "vector_l2_ops"},
        ),
    )

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    long_description = Column(Text)
    documentation = Column(Text)
    tool_type = Column(String, nullable=False)  # 'academy_agent', 'python_function', etc.
    _definition = Column("definition", JSONB, nullable=False)
    embedding = Column(Vector(1024), nullable=False)

    @property
    def definition(self) -> CustomTool:
        return CustomTool.model_validate(self._definition)

    @definition.setter
    def definition(self, t: CustomTool | dict):
        if isinstance(t, CustomTool):
            self._definition = t.model_dump()
        else:
            self._definition = CustomTool.model_validate(t).model_dump()


async def get_customtool_by_id(session: AsyncSession, tool_id: str) -> CustomTool | None:
    """Get a custom tool by its ID."""
    statement = select(CustomToolModel).where(CustomToolModel.id == tool_id)
    result = await session.execute(statement)
    row = result.scalar_one_or_none()
    if row is None:
        return None
    return row.definition


async def get_customtool_by_name(session: AsyncSession, tool_name: str) -> CustomTool | None:
    """Get a custom tool by its name."""
    statement = select(CustomToolModel).where(CustomToolModel.name == tool_name)
    result = await session.execute(statement)
    row = result.scalars().first()
    if row is None:
        return None
    return row.definition


async def get_all_customtool_ids(session: AsyncSession) -> List[str] | None:
    """Get all custom tool IDs."""
    statement = select(CustomToolModel.id)
    result = await session.execute(statement)
    tool_ids = [row[0] for row in result.fetchall()]
    return tool_ids if tool_ids else None
