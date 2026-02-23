# pyright: reportMissingImports=false
"""
SQLAlchemy models for Escape Room Multiplayer.
Matches backend/db/schema.sql (PostgreSQL).
"""
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base for all models."""


# ---------------------------------------------------------------------------
# Enums (match schema)
# ---------------------------------------------------------------------------
class TaskType(str, PyEnum):
    PUZZLE = "puzzle"
    SEARCH = "search"
    LOGIC = "logic"
    CODE = "code"


class TaskStatus(str, PyEnum):
    PENDING = "pending"
    DONE = "done"


# ---------------------------------------------------------------------------
# Rooms
# ---------------------------------------------------------------------------
class Room(Base):
    __tablename__ = "Rooms"

    room_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    room_order: Mapped[int] = mapped_column(Integer, nullable=False)
    room_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )

    # Relationships
    players: Mapped[list["Player"]] = relationship(
        "Player", back_populates="current_room", foreign_keys="Player.current_room_id"
    )
    tasks: Mapped[list["Task"]] = relationship("Task", back_populates="room", cascade="all, delete-orphan")


# ---------------------------------------------------------------------------
# Players
# ---------------------------------------------------------------------------
class Player(Base):
    __tablename__ = "Players"

    player_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    group_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    current_room_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("Rooms.room_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True
    )
    total_speed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    __table_args__ = (Index("uq_player_group", "username", "group_name", unique=True),)

    # Relationships
    current_room: Mapped[Optional["Room"]] = relationship(
        "Room", back_populates="players", foreign_keys=[current_room_id]
    )
    assigned_tasks: Mapped[list["Task"]] = relationship(
        "Task", back_populates="assigned_player", foreign_keys="Task.assigned_to"
    )
    task_answers: Mapped[list["TaskAnswer"]] = relationship(
        "TaskAnswer", back_populates="player", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------
class Task(Base):
    __tablename__ = "Tasks"

    task_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Rooms.room_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    task_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    task_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    task_type: Mapped[TaskType] = mapped_column(
        Enum(TaskType, name="task_type", create_constraint=True), nullable=False
    )
    task_status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus, name="task_status", create_constraint=True),
        default=TaskStatus.PENDING,
        nullable=False,
    )
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("Players.player_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=True
    )

    # Relationships
    room: Mapped["Room"] = relationship("Room", back_populates="tasks")
    assigned_player: Mapped[Optional["Player"]] = relationship(
        "Player", back_populates="assigned_tasks", foreign_keys=[assigned_to]
    )
    answers: Mapped[list["TaskAnswer"]] = relationship(
        "TaskAnswer", back_populates="task", cascade="all, delete-orphan"
    )


# ---------------------------------------------------------------------------
# Task_Answers
# ---------------------------------------------------------------------------
class TaskAnswer(Base):
    __tablename__ = "Task_Answers"

    answer_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Tasks.task_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    player_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("Players.player_id", ondelete="CASCADE", onupdate="CASCADE"), nullable=False
    )
    answer_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    time_taken: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    task: Mapped["Task"] = relationship("Task", back_populates="answers")
    player: Mapped["Player"] = relationship("Player", back_populates="task_answers")
