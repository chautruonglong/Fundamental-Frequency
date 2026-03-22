"""Audio loading service."""

from numpy import linspace
from scipy.io.wavfile import read

from app.services.results import LoadedAudio, ServiceFailure, ServiceSuccess, WaveResult


class AudioLoaderService:
    """Load and normalize wave files for the UI."""

    def load_wave_file(self, path: str) -> WaveResult:
        """Load a `.wav` file and normalize its amplitude for plotting and analysis."""

        try:
            sample_rate, loaded_data = read(path)
            if len(loaded_data.shape) > 1:
                loaded_data = loaded_data.mean(axis=1)

            max_value = abs(loaded_data).max()
            if max_value != 0:
                loaded_data = loaded_data / max_value

            duration = len(loaded_data) / sample_rate
            time = linspace(0, duration, len(loaded_data))
            return ServiceSuccess(LoadedAudio(path=path, data=loaded_data, duration=duration, time=time))
        except Exception as error:
            return ServiceFailure(f"Unable to load wave file: {error}")
