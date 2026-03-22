"""Typed result models used by background services."""

from dataclasses import dataclass
from typing import Generic, TypeVar

from app.analysis.pitch import PitchComputation

T = TypeVar("T")


@dataclass(frozen=True)
class ServiceSuccess(Generic[T]):
    """Wrap a successful service result."""

    value: T


@dataclass(frozen=True)
class ServiceFailure:
    """Wrap a failed service result with a user-safe message."""

    message: str


@dataclass(frozen=True)
class LoadedAudio:
    """Describe a fully loaded and normalized audio file."""

    path: str
    data: any
    duration: float
    time: any


@dataclass(frozen=True)
class PitchPreviewData:
    """Describe the content needed by the hover preview panel."""

    frame: int
    hover_time: float
    windowed_samples: any
    autocorrelation: any
    threshold: float
    min_frame: int
    max_frame: int
    is_periodic: bool
    title: str
    peak_index: int | None = None
    peak_value: float | None = None


ServiceResult = ServiceSuccess | ServiceFailure
PitchResult = ServiceSuccess[PitchComputation] | ServiceFailure
WaveResult = ServiceSuccess[LoadedAudio] | ServiceFailure
