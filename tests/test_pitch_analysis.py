"""Tests for the analysis and service layer."""

import unittest

import numpy as np

from app.analysis.pitch import find_local_peaks, get_strongest_peak_index, median_filter
from app.config import AppConfig
from app.services.audio_loader import AudioLoaderService
from app.services.pitch_service import PitchService
from app.services.results import ServiceFailure, ServiceSuccess


class AnalysisTests(unittest.TestCase):
    """Verify the pure analysis helpers behave as expected."""

    def test_find_local_peaks_detects_plateau_peak(self):
        """Plateau peaks should still return a valid peak location."""

        values = [0, 1, 3, 3, 3, 1, 0]
        peaks = find_local_peaks(values, 1, len(values) - 1)
        self.assertEqual(peaks, [4])

    def test_get_strongest_peak_index_returns_strongest_candidate(self):
        """The strongest peak should be selected from a candidate list."""

        values = [0, 1, 5, 2, 9, 4]
        peaks = [2, 4]
        self.assertEqual(get_strongest_peak_index(values, peaks), 1)

    def test_median_filter_smooths_outlier(self):
        """A median filter should suppress a single obvious outlier."""

        filtered = median_filter([100, 102, 300, 103, 104], 3)
        self.assertEqual(filtered.tolist(), [100, 102, 103, 104, 103])


class ServiceTests(unittest.TestCase):
    """Verify typed services return structured results."""

    def test_audio_loader_returns_failure_for_missing_file(self):
        """Loading a missing file should return a structured failure result."""

        result = AudioLoaderService().load_wave_file("missing.wav")
        self.assertIsInstance(result, ServiceFailure)

    def test_pitch_service_returns_typed_success(self):
        """Pitch service should return a typed success for valid synthetic input."""

        config = AppConfig()
        service = PitchService(config)
        sample_rate = 8000
        duration = 0.2
        time = np.arange(int(sample_rate * duration)) / sample_rate
        samples = np.sin(2 * np.pi * 200 * time)
        result = service.build_pitch_computation(samples, duration, 40, 5, 0.3)
        self.assertIsInstance(result, ServiceSuccess)
        self.assertGreater(result.value.window_samples, 0)


if __name__ == "__main__":
    unittest.main()
