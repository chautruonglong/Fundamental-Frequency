"""Centralized application configuration and UI copy."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class UiText:
    """Store every user-facing string in one place."""

    app_title: str = "Fundamental Frequency"
    open_file_button: str = "Open file"
    pitch_button: str = "Pitch contour"
    loading_file: str = "Loading file..."
    processing_pitch: str = "Processing..."
    no_wave_file: str = "No wave file"
    sidebar_window_length: str = "Window length:"
    sidebar_kernel_size: str = "Kernel size:"
    sidebar_threshold: str = "Threshold:"
    graph_frequency_label: str = "Frequency (Hz)"
    graph_time_label: str = "Time"
    graph_amplitude_label: str = "Amplitude"
    preview_title: str = "Window Details"
    preview_sample_label: str = "Sample"
    preview_delay_label: str = "Delay"
    preview_autocorr_label: str = "Auto correlation"
    preview_window_title_template: str = "Window at {time:.3f} s"
    preview_non_periodic_title: str = "Not periodicity, F0 = NaN"
    preview_periodic_title: str = "Periodicity, F0 = {f0:.3f}"
    preview_out_of_range_title: str = "Periodicity, out F0 = {f0:.3f}"
    before_filter_title: str = "Before median filter, F0 = {f0}"
    after_filter_title: str = "After median filter, F0 = {f0}"
    nan_title: str = "{label}, F0 = NaN"
    waveform_title_template: str = "{name}, {duration:.2f}(s)"


@dataclass(frozen=True)
class ThemeConfig:
    """Collect all visual constants used by the Tk UI."""

    sidebar_width: int = 150
    window_width: int = 1200
    window_height: int = 800
    min_window_width: int = 1200
    min_window_height: int = 800
    preview_width: int = 500
    preview_height: int = 500
    preview_shadow_pad: int = 10
    sidebar_bg: str = "#efefef"
    button_bg: str = "#0052cc"
    button_active_bg: str = "#0d66e5"
    button_fg: str = "#ffffff"
    label_fg: str = "#222222"
    input_bg: str = "#ffffff"
    input_fg: str = "#222222"
    canvas_bg: str = "#ffffff"
    preview_bg: str = "#ffffff"
    preview_header_bg: str = "#1f2937"
    preview_header_fg: str = "#ffffff"
    preview_border: str = "#cbd5e1"
    preview_shadow: str = "#d7dde7"
    combo_border: str = "#b8b8b8"
    selected_bg: str = "#cfe3ff"


@dataclass(frozen=True)
class AnalysisConfig:
    """Store all analysis-related numeric configuration."""

    default_window_index: int = 3
    default_kernel_index: int = 1
    default_threshold_index: int = 0
    window_length_options: tuple[str, ...] = ("10 ms", "20 ms", "30 ms", "40 ms", "50 ms", "60 ms")
    kernel_size_options: tuple[int, ...] = (3, 5, 7, 9, 11, 13)
    threshold_options: tuple[str, ...] = ("30%", "50%", "70%")
    min_frequency_hz: int = 75
    max_frequency_hz: int = 350
    frequency_plot_limit: int = 400
    preview_threshold_delta: float = 0.01
    contour_threshold_delta: float = 0.02
    loader_poll_ms: int = 30
    root_refresh_ms: int = 60
    hover_hide_delay_ms: int = 120


@dataclass(frozen=True)
class LayoutConfig:
    """Describe fixed positions used by the handcrafted Tk layout."""

    file_button_x: int = 10
    file_button_y: int = 250
    button_width: int = 100
    button_height: int = 28
    label_width: int = 100
    control_width: int = 100
    window_label_y: int = 300
    window_box_y: int = 320
    kernel_label_y: int = 370
    kernel_box_y: int = 390
    threshold_label_y: int = 440
    threshold_box_y: int = 460
    pitch_button_y: int = 510
    loader_x: int = 10
    loader_y: int = 548
    loader_width: int = 130
    loader_height: int = 34
    loader_bar_y: int = 24
    loader_bar_width: int = 80
    preview_top_gap: int = 0


@dataclass(frozen=True)
class AppConfig:
    """Bundle every config object so the app can pass one dependency around."""

    text: UiText = field(default_factory=UiText)
    theme: ThemeConfig = field(default_factory=ThemeConfig)
    analysis: AnalysisConfig = field(default_factory=AnalysisConfig)
    layout: LayoutConfig = field(default_factory=LayoutConfig)
