"""Shared application state models."""

from dataclasses import dataclass, field
from typing import Any

from app.services.worker_runner import WorkerJob


@dataclass
class AudioSelection:
    """Hold the currently loaded audio file and all derived values."""

    path: str = ""
    data: Any = field(default_factory=list)
    duration: float = 0.0
    time: Any = field(default_factory=list)


@dataclass
class AnalysisSelection:
    """Store the active pitch-analysis parameters and caches."""

    window_length_ms: int = 0
    kernel_size: int = 0
    threshold_ratio: float = 0.0
    window_samples: int = 0
    hamming_window: Any = field(default_factory=list)
    min_frame: int = 0
    max_frame: int = 0


@dataclass
class WorkerState:
    """Track the one background worker used by the Tk application."""

    job: WorkerJob = field(default_factory=WorkerJob)


@dataclass
class HoverState:
    """Track delayed preview rendering for the floating hover panel."""

    pending_frame: int | None = None
    render_job: Any = None
    is_visible: bool = False
    has_custom_position: bool = False
    drag_offset_x: int = 0
    drag_offset_y: int = 0


@dataclass
class AppState:
    """Aggregate every mutable value used by the app."""

    audio: AudioSelection = field(default_factory=AudioSelection)
    analysis: AnalysisSelection = field(default_factory=AnalysisSelection)
    worker: WorkerState = field(default_factory=WorkerState)
    hover: HoverState = field(default_factory=HoverState)
    is_loader_visible: bool = False
    is_redraw_needed: bool = False
