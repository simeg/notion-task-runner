"""
Domain models for statistics and inventory tracking.

This module contains all the data classes and enums used across
the statistics system to represent domain entities like watches,
cables, adapters, and other inventory items.
"""

from dataclasses import dataclass
from enum import Enum


class CableType(Enum):
    """Types of cables in the inventory."""

    HDMI = "HDMI"
    USB_A = "USB-A"
    USB_C = "USB-C"
    AUDIO = "Audio"
    ETHERNET = "Ethernet"
    DISPLAY_PORT = "DisplayPort"
    OTHER = "Other"


@dataclass(frozen=True)
class Watch:
    """Represents a watch in the collection."""

    name: str
    cost: int
    purchased_date: str

    def __post_init__(self) -> None:
        """Validate watch data after initialization."""
        if self.cost < 0:
            raise ValueError("Watch cost cannot be negative")
        if not self.name.strip():
            raise ValueError("Watch name cannot be empty")


@dataclass(frozen=True)
class Cable:
    """Represents a cable in the inventory."""

    type: CableType
    length_cm: int

    def __post_init__(self) -> None:
        """Validate cable data after initialization."""
        if self.length_cm <= 0:
            raise ValueError("Cable length must be positive")

    @property
    def length_meters(self) -> float:
        """Return cable length in meters."""
        return self.length_cm / 100.0


@dataclass(frozen=True)
class Adapter:
    """Represents an adapter in the inventory."""

    type: str
    length_cm: int

    def __post_init__(self) -> None:
        """Validate adapter data after initialization."""
        if self.length_cm < 0:
            raise ValueError("Adapter length cannot be negative")
        if not self.type.strip():
            raise ValueError("Adapter type cannot be empty")


@dataclass(frozen=True)
class Pryl:
    """Represents a miscellaneous item (pryl) in the inventory."""

    title: str
    number: int

    def __post_init__(self) -> None:
        """Validate pryl data after initialization."""
        if self.number < 0:
            raise ValueError("Pryl number cannot be negative")
        if not self.title.strip():
            raise ValueError("Pryl title cannot be empty")


@dataclass(frozen=True)
class Vinyl:
    """Represents a vinyl record in the collection."""

    title: str
    artist: str
    year: int | None = None
    cost: int | None = None

    def __post_init__(self) -> None:
        """Validate vinyl data after initialization."""
        if not self.title.strip():
            raise ValueError("Vinyl title cannot be empty")
        if not self.artist.strip():
            raise ValueError("Vinyl artist cannot be empty")
        if self.year is not None and (self.year < 1900 or self.year > 2030):
            raise ValueError("Vinyl year must be between 1900 and 2030")
        if self.cost is not None and self.cost < 0:
            raise ValueError("Vinyl cost cannot be negative")


@dataclass(frozen=True)
class WorkspaceStats:
    """Aggregated statistics for the entire workspace."""

    total_watches: int
    total_watch_cost: int
    total_cables: int
    total_adapters: int
    total_prylar: int
    total_vinyl_records: int
    total_vinyl_cost: int

    def __post_init__(self) -> None:
        """Validate workspace stats after initialization."""
        fields = [
            self.total_watches,
            self.total_watch_cost,
            self.total_cables,
            self.total_adapters,
            self.total_prylar,
            self.total_vinyl_records,
            self.total_vinyl_cost,
        ]
        for field in fields:
            if field < 0:
                raise ValueError("All stats values must be non-negative")

    @property
    def total_items(self) -> int:
        """Return total count of all items."""
        return (
            self.total_watches
            + self.total_cables
            + self.total_adapters
            + self.total_prylar
            + self.total_vinyl_records
        )

    @property
    def total_cost(self) -> int:
        """Return total cost of all items."""
        return self.total_watch_cost + self.total_vinyl_cost
