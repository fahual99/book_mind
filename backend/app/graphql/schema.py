"""
GraphQL schema assembly.
"""

import strawberry
from strawberry.fastapi import GraphQLRouter

from .queries import make_query
from .mutations import make_mutation


def create_graphql_router(app_state: dict) -> GraphQLRouter:
    """Create the Strawberry GraphQL router with app state."""
    Query = make_query(app_state)
    Mutation = make_mutation(app_state)

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    return GraphQLRouter(schema)
