import strawberry
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from app.api.context import CustomContext, get_context
from app.schemas.telemetry import VelocityBucket

@strawberry.type
class Query:
    @strawberry.field(description="Calculate the average pins knocked down for simulations that fall within a specific velocity range. Only completed simulations are included in the calculation.")
    def avg_pins_by_velocity(
        self,
        info: Info[CustomContext, None],
        min_velocity: float,
        max_velocity: float
    ) -> VelocityBucket:
        return info.context.telemetry_service.get_avg_pins_by_velocity(min_velocity, max_velocity)


schema = strawberry.Schema(Query)
router = GraphQLRouter(schema, context_getter=get_context)
