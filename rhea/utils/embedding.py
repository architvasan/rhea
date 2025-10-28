from openai import OpenAI
from typing import List

from rhea.utils.schema import Tool
from rhea.utils.custom_tool_schema import CustomTool
from rhea.utils.models import GalaxyTool, CustomToolModel

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

template = """# {name}

**Description**  
{description}

---

## Long Description

{long_description}

## README

{readme}
"""


def get_embedding(input_text: str, client: OpenAI, model: str) -> List[float]:
    response = client.embeddings.create(
        model=model, input=input_text, encoding_format="float"
    )
    embedding: List[float] = response.data[0].embedding
    return embedding


def generate_tool_documentation_embedding(
    t: Tool, client: OpenAI, model: str
) -> List[float]:
    return get_embedding(
        input_text=template.format(
            name=t.name or t.user_provided_name,
            description=t.description,
            long_description=t.long_description,
            readme=t.documentation,
        ),
        client=client,
        model=model,
    )


def generate_custom_tool_documentation_embedding(
    t: CustomTool, client: OpenAI, model: str
) -> List[float]:
    """Generate embedding for a custom tool."""
    return get_embedding(
        input_text=template.format(
            name=t.name,
            description=t.description,
            long_description=t.long_description or "",
            readme=t.documentation or "",
        ),
        client=client,
        model=model,
    )


async def get_l2_distance(
    query_vec: List[float], session: AsyncSession, limit: int = 10
) -> List[Tool]:
    """Search for Galaxy tools using L2 distance."""
    dist_col = GalaxyTool.embedding.l2_distance(query_vec).label("distance")

    result = await session.execute(
        (select(GalaxyTool, dist_col).order_by(dist_col).limit(limit))
    )

    rows = result.all()
    return [orm_obj.definition for orm_obj, _dist in rows]


async def get_l2_distance_custom(
    query_vec: List[float], session: AsyncSession, limit: int = 10
) -> List[CustomTool]:
    """Search for custom tools using L2 distance."""
    dist_col = CustomToolModel.embedding.l2_distance(query_vec).label("distance")

    result = await session.execute(
        (select(CustomToolModel, dist_col).order_by(dist_col).limit(limit))
    )

    rows = result.all()
    return [orm_obj.definition for orm_obj, _dist in rows]


async def get_l2_distance_combined(
    query_vec: List[float], session: AsyncSession, limit: int = 10
) -> tuple[List[Tool], List[CustomTool]]:
    """
    Search for both Galaxy and custom tools using L2 distance.

    Returns top results from both tables, combined up to the limit.
    """
    # Get results from both tables
    galaxy_dist_col = GalaxyTool.embedding.l2_distance(query_vec).label("distance")
    custom_dist_col = CustomToolModel.embedding.l2_distance(query_vec).label("distance")

    galaxy_result = await session.execute(
        (select(GalaxyTool, galaxy_dist_col).order_by(galaxy_dist_col).limit(limit))
    )

    custom_result = await session.execute(
        (select(CustomToolModel, custom_dist_col).order_by(custom_dist_col).limit(limit))
    )

    galaxy_rows = galaxy_result.all()
    custom_rows = custom_result.all()

    galaxy_tools = [orm_obj.definition for orm_obj, _dist in galaxy_rows]
    custom_tools = [orm_obj.definition for orm_obj, _dist in custom_rows]

    return galaxy_tools, custom_tools
