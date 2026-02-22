from typing import List
import uuid
from datetime import datetime

from sqlalchemy import Enum, ForeignKey, Index, PrimaryKeyConstraint, SmallInteger, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.schemas.simulation_state import SimulationState

class Base(DeclarativeBase):
    pass

class Simulation(Base):
    """Represents a bowling simulation execution, including input parameters, status, results, and telemetry."""
    __tablename__ = "simulations"

    # overall simulation details
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid7)
    queued_at: Mapped[datetime] = mapped_column(default=datetime.now)
    
    # queue management
    status: Mapped[SimulationState] = mapped_column(Enum(SimulationState), default=SimulationState.PENDING)
    retry_count: Mapped[int] = mapped_column(SmallInteger, default=0)
    error_msg: Mapped[str | None] = mapped_column(String(255))
    started_at: Mapped[datetime | None] = mapped_column()
    completed_at: Mapped[datetime | None] = mapped_column()
    
    # simulation input parameters
    velocity: Mapped[float] = mapped_column(comment="Initial velocity of the bowling ball in m/s")
    rpm: Mapped[int] = mapped_column(SmallInteger, comment="Rotations per meter traveled")
    friction: Mapped[float] = mapped_column(comment="Friction coefficient of the lane")
    launch_angle: Mapped[float] = mapped_column(comment="Launch angle of the bowling ball in degrees")
    lateral_offset: Mapped[float] = mapped_column(comment="Lateral offset of the bowling ball from the center of the lane in meters")
    
    # simulation results
    results: Mapped["SimulationResult | None"] = relationship("SimulationResult", back_populates="simulation", uselist=False)
    
    # telemetry
    telemetry: Mapped[List["Telemetry"] | None] = relationship("Telemetry", back_populates="simulation")
    
    __table_args__ = (
        Index("idx_status", "status"),
    )

class SimulationResult(Base):
    """Represents the results of a completed bowling simulation, including pins knocked, impact velocity, hook potential, and detailed pin states."""
    __tablename__ = "simulation_results"

    simulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulations.id"), primary_key=True)
    execution_duration: Mapped[float] = mapped_column(comment="Total execution time of the simulation in milliseconds")
    pins_knocked: Mapped[int] = mapped_column(SmallInteger, comment="Number of pins knocked down in the simulation")
    impact_velocity: Mapped[float] = mapped_column(comment="Velocity of the ball at the moment of impact with the pins in m/s")
    hook_potential: Mapped[float] = mapped_column(comment="Potential for the ball to hook based on its spin and lane conditions")
    entry_angle: Mapped[float] = mapped_column(comment="Angle at which the ball enters the pin formation in degrees")
    ball_deflection: Mapped[float] = mapped_column(comment="Deflection of the ball after hitting the pins in degrees")
    trajectory_length: Mapped[float] = mapped_column(comment="Total length of the ball's trajectory in meters")
    
    pin_states: Mapped[List["PinState"]] = relationship("PinState", back_populates="simulation_results")

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="results", uselist=False)

class PinState(Base):
    """Represents the state of an individual pin in a completed bowling simulation."""
    __tablename__ = "pin_states"

    simulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulation_results.simulation_id"))
    pin_number: Mapped[int] = mapped_column(SmallInteger, comment="Pin number (1-10)")
    knocked: Mapped[bool] = mapped_column(comment="Indicates whether the pin was knocked down")
    impact_velocity: Mapped[float | None] = mapped_column(comment="Velocity of the ball at the moment of impact with the pin in m/s")

    simulation_results: Mapped["SimulationResult"] = relationship("SimulationResult", back_populates="pin_states", uselist=False)
    
    __table_args__ = (
        PrimaryKeyConstraint("simulation_id", "pin_number", name="pk_simulation_pin"),
    )

class Telemetry(Base):
    """Represents the telemetry data of a bowling simulation, including position, velocity, speed, and rotation over time."""
    __tablename__ = "telemetry"

    simulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulations.id"))
    time: Mapped[float] = mapped_column(comment="Time since the start of the simulation in seconds")
    position_x: Mapped[float] = mapped_column(comment="X-coordinate of the ball's position in meters")
    position_y: Mapped[float] = mapped_column(comment="Y-coordinate of the ball's position in meters")
    velocity_x: Mapped[float] = mapped_column(comment="X-component of the ball's velocity in m/s")
    velocity_y: Mapped[float] = mapped_column(comment="Y-component of the ball's velocity in m/s")
    speed: Mapped[float] = mapped_column(comment="Magnitude of the ball's velocity in m/s")
    rotation: Mapped[float] = mapped_column(comment="Rotation of the ball in degrees")

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="telemetry", uselist=False)
    
    __table_args__ = (
        PrimaryKeyConstraint("simulation_id", "time", name="pk_simulation_time"),
    )