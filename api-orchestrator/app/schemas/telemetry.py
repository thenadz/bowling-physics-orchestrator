import strawberry

@strawberry.type
class VelocityBucket:
    """Represents a bucket of simulations that fall within a specific velocity range, along with aggregated telemetry data."""
    
    min_velocity: float = strawberry.field(description="Minimum (inclusive) velocity of the bucket in m/s")
    max_velocity: float = strawberry.field(description="Maximum (inclusive) velocity of the bucket in m/s")
    average_pins: float | None = strawberry.field(description="Average number of pins knocked down for simulations in this velocity bucket. Null if no simulations in this bucket.")
    simulation_count: int = strawberry.field(description="Number of simulations in this velocity bucket")
