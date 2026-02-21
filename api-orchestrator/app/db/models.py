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
    velocity: Mapped[float] = mapped_column()
    rpm: Mapped[int] = mapped_column(SmallInteger)
    friction: Mapped[float] = mapped_column()
    launch_angle: Mapped[float] = mapped_column()
    lateral_offset: Mapped[float] = mapped_column()
    
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
    execution_duration: Mapped[float] = mapped_column()
    pins_knocked: Mapped[int] = mapped_column(SmallInteger)
    impact_velocity: Mapped[float] = mapped_column()
    hook_potential: Mapped[float] = mapped_column()
    entry_angle: Mapped[float] = mapped_column()
    ball_deflection: Mapped[float] = mapped_column()
    trajectory_length: Mapped[float] = mapped_column()
    
    pin_states: Mapped[List["PinState"]] = relationship("PinState", back_populates="simulation_results")

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="results", uselist=False)

class PinState(Base):
    """Represents the state of an individual pin in a completed bowling simulation."""
    __tablename__ = "pin_states"

    simulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulation_results.simulation_id"))
    pin_number: Mapped[int] = mapped_column(SmallInteger)
    knocked: Mapped[bool] = mapped_column()
    impact_velocity: Mapped[float | None] = mapped_column()

    simulation_results: Mapped["SimulationResult"] = relationship("SimulationResult", back_populates="pin_states", uselist=False)
    
    __table_args__ = (
        PrimaryKeyConstraint("simulation_id", "pin_number", name="pk_simulation_pin"),
    )

class Telemetry(Base):
    """Represents the telemetry data of a bowling simulation, including position, velocity, speed, and rotation over time."""
    __tablename__ = "telemetry"

    simulation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("simulations.id"))
    time: Mapped[float] = mapped_column()
    position_x: Mapped[float] = mapped_column()
    position_y: Mapped[float] = mapped_column()
    velocity_x: Mapped[float] = mapped_column()
    velocity_y: Mapped[float] = mapped_column()
    speed: Mapped[float] = mapped_column()
    rotation: Mapped[float] = mapped_column()

    simulation: Mapped["Simulation"] = relationship("Simulation", back_populates="telemetry", uselist=False)
    
    __table_args__ = (
        PrimaryKeyConstraint("simulation_id", "time", name="pk_simulation_time"),
    )