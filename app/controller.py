"""Application controller that coordinates services, the view, and UI state."""

from app.analysis.pitch import extract_filename, median_filter
from app.config import AppConfig
from app.preview_controller import PreviewController
from app.services.audio_loader import AudioLoaderService
from app.services.pitch_service import PitchService
from app.services.results import ServiceSuccess
from app.services.worker_runner import WorkerRunner
from app.state import AppState
from app.ui.main_window import MainWindow


class ApplicationController:
    """Coordinate all UI events, background work, and plot rendering."""

    def __init__(self, config: AppConfig | None = None):
        """Create the shared state and wire the Tk view to controller callbacks."""

        self.config = config or AppConfig()
        self.state = AppState()
        self.window = MainWindow(self.config)
        self.audio_loader = AudioLoaderService()
        self.pitch_service = PitchService(self.config)
        self.worker_runner = WorkerRunner()
        self.preview_controller = PreviewController(self.config, self.state, self.window, self.pitch_service)
        self.window.bind_resize(self._on_root_resize)
        self.window.bind_file_open(self._on_open_file_clicked)
        self.window.bind_pitch_compute(self._on_pitch_clicked)
        self.window.bind_canvas_motion(self.preview_controller.on_canvas_motion, self.preview_controller.hide)

    def run(self):
        """Start the Tk main loop."""

        self.window.root.after(0, self._refresh_ui, 0)
        self.window.root.mainloop()

    def _on_root_resize(self, _event):
        """Keep the layout responsive while preserving the preview position rules."""

        self.window.resize()
        self.preview_controller.keep_position_synced()

    def _on_open_file_clicked(self, _event):
        """Ask the user for a WAV file and start a background load operation."""

        if self.state.is_loader_visible:
            return

        selected_path = self.window.request_wave_file()
        if selected_path == "":
            return

        self._show_loader(self.config.text.loading_file)
        self._start_worker("wave", self.audio_loader.load_wave_file, selected_path)

    def _on_pitch_clicked(self, _event):
        """Start the pitch contour computation with the current sidebar settings."""

        if self.state.is_loader_visible or self.state.audio.duration == 0:
            return

        window_length_ms, kernel_size, threshold_ratio = self.window.read_controls()
        self._show_loader(self.config.text.processing_pitch)
        self._start_worker(
            "pitch",
            self.pitch_service.build_pitch_computation,
            self.state.audio.data,
            self.state.audio.duration,
            window_length_ms,
            kernel_size,
            threshold_ratio,
        )

    def _show_loader(self, message):
        """Show the sidebar loader and update the shared state."""

        self.state.is_loader_visible = True
        self.window.show_loader(message)

    def _hide_loader(self):
        """Hide the sidebar loader and update the shared state."""

        self.state.is_loader_visible = False
        self.window.hide_loader()

    def _start_worker(self, kind, target, *args):
        """Start the single background worker used by the app."""

        self.worker_runner.start(kind, self._run_service_call, target, *args)
        self.state.worker.job = self.worker_runner.job
        self.window.root.after(self.config.analysis.loader_poll_ms, self._finish_worker_if_ready)

    def _finish_worker_if_ready(self):
        """Apply completed worker results on the Tk main thread."""

        if self.state.worker.job.thread is None:
            self._hide_loader()
            return

        if self.worker_runner.is_running():
            self.window.root.after(self.config.analysis.loader_poll_ms, self._finish_worker_if_ready)
            return

        completed_kind, result = self.worker_runner.finish()
        self.state.worker.job = self.worker_runner.job

        try:
            if isinstance(result, ServiceSuccess):
                if completed_kind == "wave":
                    self._apply_wave_data(result.value)
                elif completed_kind == "pitch":
                    self._apply_pitch_contour(result.value)
        finally:
            self._hide_loader()

    def _run_service_call(self, target, *args):
        """Execute a service method inside the worker and store its typed result."""

        self.worker_runner.job.result = target(*args)

    def _apply_wave_data(self, loaded_audio):
        """Store loaded audio data and redraw the waveform plot."""

        self.state.audio.path = loaded_audio.path
        self.state.audio.data = loaded_audio.data
        self.state.audio.duration = loaded_audio.duration
        self.state.audio.time = loaded_audio.time
        self.preview_controller.hide()
        self.window.render_wave(
            extract_filename(loaded_audio.path),
            loaded_audio.data,
            loaded_audio.time,
            loaded_audio.duration,
        )
        self.state.is_redraw_needed = True

    def _apply_pitch_contour(self, computation):
        """Update contour state and redraw the before/after pitch plots."""

        self.state.analysis.window_length_ms = computation.window_length_ms
        self.state.analysis.kernel_size = computation.kernel_size
        self.state.analysis.threshold_ratio = computation.threshold_ratio
        self.state.analysis.window_samples = computation.window_samples
        self.state.analysis.hamming_window = computation.hamming_window
        self.state.analysis.min_frame = computation.min_frame
        self.state.analysis.max_frame = computation.max_frame

        filtered_frequencies = median_filter(computation.frequencies, computation.kernel_size)
        self.window.render_pitch_contours(
            computation.time_indexes,
            computation.frequencies,
            filtered_frequencies,
        )
        self.state.is_redraw_needed = True

    def _refresh_ui(self, index):
        """Drive redraw work and safety checks from one light Tk timer."""

        if index == 8:
            index = 0

        self.preview_controller.refresh_from_pointer()

        if self.state.is_redraw_needed:
            self.window.redraw_main_figure()
            self.state.is_redraw_needed = False

        self.window.root.after(self.config.analysis.root_refresh_ms, self._refresh_ui, index + 1)
