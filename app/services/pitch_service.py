"""Pitch-computation service."""

from numpy import hamming

from app.analysis.pitch import (
    PitchComputation,
    autocorrelation_fft,
    compute_pitch_contour,
    find_local_peaks,
    get_strongest_peak_index,
)
from app.services.results import PitchPreviewData, ServiceFailure, ServiceSuccess, PitchResult


class PitchService:
    """Compute pitch contours and preview-window details."""

    def __init__(self, config):
        """Store configuration once for the service methods."""

        self.config = config

    def build_pitch_computation(self, samples, duration, window_length_ms, kernel_size, threshold_ratio) -> PitchResult:
        """Compute the full raw pitch contour for the loaded waveform."""

        try:
            window_samples = max(1, int(window_length_ms * len(samples) / (duration * 1000)))
            hamming_window = hamming(window_samples)
            min_delay_ms = 1000 / self.config.analysis.max_frequency_hz
            max_delay_ms = 1000 / self.config.analysis.min_frequency_hz
            min_frame = int(min_delay_ms * window_samples / window_length_ms)
            max_frame = int(max_delay_ms * window_samples / window_length_ms)
            frequencies, indexes = compute_pitch_contour(
                samples,
                window_length_ms,
                window_samples,
                hamming_window,
                threshold_ratio,
                min_frame,
                max_frame,
                self.config.analysis.contour_threshold_delta,
            )
            time_indexes = [index * duration / len(samples) for index in indexes]
            return ServiceSuccess(
                PitchComputation(
                    window_length_ms=window_length_ms,
                    kernel_size=kernel_size,
                    threshold_ratio=threshold_ratio,
                    window_samples=window_samples,
                    hamming_window=hamming_window,
                    min_frame=min_frame,
                    max_frame=max_frame,
                    frequencies=frequencies,
                    time_indexes=time_indexes,
                )
            )
        except Exception as error:
            return ServiceFailure(f"Unable to compute pitch contour: {error}")

    def build_preview_data(self, samples, duration, analysis_state, frame) -> PitchPreviewData:
        """Compute all data needed to render the hover preview panel."""

        windowed_samples = samples[frame:frame + analysis_state.window_samples] * analysis_state.hamming_window
        autocorrelation = autocorrelation_fft(windowed_samples)
        threshold = autocorrelation[0] * analysis_state.threshold_ratio
        hover_time = frame * duration / len(samples)
        is_periodic = True
        title = self.config.text.preview_non_periodic_title
        peak_index = None
        peak_value = None

        max_indexes = find_local_peaks(autocorrelation, analysis_state.min_frame, analysis_state.max_frame)
        min_indexes = find_local_peaks(-1 * autocorrelation, analysis_state.min_frame, analysis_state.max_frame)
        if len(max_indexes) == 0 or len(min_indexes) == 0:
            is_periodic = False

        if is_periodic:
            strongest_peak = get_strongest_peak_index(autocorrelation, max_indexes)
            max_local = autocorrelation[max_indexes[strongest_peak]]
            min_local = autocorrelation[min_indexes[strongest_peak]]
            if max_local < threshold or max_local - min_local < self.config.analysis.preview_threshold_delta:
                is_periodic = False
            else:
                peak_index = max_indexes[strongest_peak]
                peak_value = max_local

        if is_periodic:
            period_ms = peak_index * analysis_state.window_length_ms / analysis_state.window_samples
            frequency = 1000 / period_ms
            if frequency > self.config.analysis.max_frequency_hz or frequency < self.config.analysis.min_frequency_hz:
                title = self.config.text.preview_out_of_range_title.format(f0=frequency)
                is_periodic = False
            else:
                title = self.config.text.preview_periodic_title.format(f0=frequency)

        return PitchPreviewData(
            frame=frame,
            hover_time=hover_time,
            windowed_samples=windowed_samples,
            autocorrelation=autocorrelation,
            threshold=threshold,
            min_frame=analysis_state.min_frame,
            max_frame=analysis_state.max_frame,
            is_periodic=is_periodic,
            title=title,
            peak_index=peak_index,
            peak_value=peak_value,
        )
