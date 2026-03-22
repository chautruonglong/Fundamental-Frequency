"""Pitch-analysis routines extracted from the legacy single-file script."""

from dataclasses import dataclass
from pathlib import Path

from numpy import array, real, round
from numpy.fft import fft, ifft


@dataclass(frozen=True)
class PitchComputation:
    """Describe the values needed to draw the main pitch-contour plots."""

    window_length_ms: int
    kernel_size: int
    threshold_ratio: float
    window_samples: int
    hamming_window: any
    min_frame: int
    max_frame: int
    frequencies: list[float]
    time_indexes: list[float]


def autocorrelation_fft(samples):
    """Compute autocorrelation with an FFT-based implementation."""

    signal_length = 2 * len(samples) - 1
    forward = fft(samples, signal_length)
    reversed_signal = fft(samples[::-1], signal_length)
    correlated = ifft(forward * reversed_signal)
    return real(correlated[signal_length // 2:])


def find_local_peaks(values, start_frame, end_frame):
    """Return peak locations, including plateau-like maxima."""

    peak_indexes = []
    plateau_start = 0
    is_tracking_plateau = False

    for index in range(start_frame, end_frame):
        if values[index] > values[index - 1] and values[index] > values[index + 1]:
            peak_indexes.append(index)
        elif values[index] > values[index - 1] and values[index] == values[index + 1]:
            plateau_start = index
            is_tracking_plateau = True
        elif values[index] == values[index - 1] and values[index] > values[index + 1] and is_tracking_plateau:
            peak_indexes.append(index)
            is_tracking_plateau = False

    return peak_indexes


def get_strongest_peak_index(values, peak_indexes):
    """Return the index of the strongest peak from a candidate list."""

    strongest_index = 0
    for index in range(1, len(peak_indexes)):
        if values[peak_indexes[index]] > values[peak_indexes[strongest_index]]:
            strongest_index = index
    return strongest_index


def median_filter(values, kernel_size):
    """Smooth the pitch contour with a simple zero-padded median filter."""

    if type(values) is not list:
        values = values.tolist()

    value_count = len(values)
    half_kernel = (kernel_size - 1) // 2
    filtered_values = []

    for index in range(value_count):
        left = index - half_kernel
        right = index + half_kernel
        if left < 0:
            neighborhood = [0] * (0 - left) + values[0:right + 1]
        elif right >= value_count:
            neighborhood = values[left:value_count] + [0] * (right - value_count + 1)
        else:
            neighborhood = values[left:right + 1]
        neighborhood.sort()
        filtered_values.append(neighborhood[half_kernel])

    return array(filtered_values)


def extract_filename(path):
    """Return only the file name from an audio path."""

    return Path(path).name


def compute_pitch_contour(samples, window_length_ms, window_samples, hamming_window, threshold_ratio,
                          min_frame, max_frame, threshold_delta):
    """Compute the raw pitch contour using autocorrelation windows."""

    frequencies = []
    indexes = []
    cursor = 0

    while cursor + window_samples <= len(samples):
        windowed_samples = samples[cursor:cursor + window_samples] * hamming_window
        cursor += window_samples // 2
        autocorrelation = autocorrelation_fft(windowed_samples)
        threshold = autocorrelation[0] * threshold_ratio

        max_indexes = find_local_peaks(autocorrelation, min_frame, max_frame)
        min_indexes = find_local_peaks(-1 * autocorrelation, 0, len(autocorrelation) - 1)
        if len(max_indexes) == 0 or len(min_indexes) == 0:
            continue

        strongest_peak_position = get_strongest_peak_index(autocorrelation, max_indexes)
        max_local = autocorrelation[max_indexes[strongest_peak_position]]
        min_local = autocorrelation[min_indexes[strongest_peak_position]]
        if max_local < threshold or max_local - min_local < threshold_delta:
            continue

        period_ms = max_indexes[strongest_peak_position] * window_length_ms / window_samples
        frequency = 1000 / period_ms
        frequencies.append(frequency)
        indexes.append(cursor - window_samples)

    return frequencies, indexes
