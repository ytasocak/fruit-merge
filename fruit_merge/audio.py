"""Sound effects generator and non-blocking playback engine using native Windows audio."""

import io
import math
import struct
import threading
import queue
import wave
from typing import Optional, Dict

try:
    import winsound
    HAS_WINSOUND = True
except ImportError:
    HAS_WINSOUND = False


class AudioManager:
    """Manages procedural sound effects with non-blocking background playback."""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled and HAS_WINSOUND
        self._sound_queue: "queue.Queue[Optional[bytes]]" = queue.Queue(maxsize=8)
        self._worker_thread: Optional[threading.Thread] = None
        self._running = False
        self._wav_cache: Dict[str, bytes] = {}

        if self.enabled:
            self._pregenerate_sounds()
            self._start_worker()

    def _start_worker(self) -> None:
        self._running = True
        self._worker_thread = threading.Thread(target=self._playback_loop, daemon=True, name="AudioWorker")
        self._worker_thread.start()

    def _playback_loop(self) -> None:
        while self._running:
            try:
                wav_data = self._sound_queue.get(timeout=0.5)
                if wav_data is None:
                    break
                if self.enabled and HAS_WINSOUND:
                    winsound.PlaySound(wav_data, winsound.SND_MEMORY)
                self._sound_queue.task_done()
            except queue.Empty:
                continue
            except Exception:
                pass

    def stop(self) -> None:
        self._running = False
        try:
            self._sound_queue.put_nowait(None)
        except Exception:
            pass

    def toggle_sound(self) -> bool:
        self.enabled = not self.enabled
        return self.enabled

    @property
    def is_enabled(self) -> bool:
        return self.enabled

    def _generate_wav(self, samples: list[int], sample_rate: int = 22050) -> bytes:
        """Encodes 16-bit mono PCM samples into WAV container bytes."""
        buf = io.BytesIO()
        with wave.open(buf, "wb") as w:
            w.setnchannels(1)
            w.setsampwidth(2)
            w.setframerate(sample_rate)
            raw = struct.pack("<" + "h" * len(samples), *samples)
            w.writeframes(raw)
        return buf.getvalue()

    def _synthesize_sine_sweep(
        self, start_f: float, end_f: float, duration_s: float, volume: float = 0.5, sample_rate: int = 22050
    ) -> bytes:
        num_samples = int(duration_s * sample_rate)
        samples = []
        phase = 0.0
        for i in range(num_samples):
            t = i / num_samples
            freq = start_f + (end_f - start_f) * t
            phase += 2.0 * math.pi * freq / sample_rate
            # Smooth envelope: fast attack, exponential decay
            env = (1.0 - math.exp(-t * 20.0)) * math.exp(-t * 4.0)
            sample = int(32767.0 * volume * env * math.sin(phase))
            samples.append(max(-32767, min(32767, sample)))
        return self._generate_wav(samples, sample_rate)

    def _synthesize_chime(
        self, freqs: list[float], duration_s: float = 0.18, volume: float = 0.45, sample_rate: int = 22050
    ) -> bytes:
        num_samples = int(duration_s * sample_rate)
        samples = []
        for i in range(num_samples):
            t = i / num_samples
            env = (1.0 - math.exp(-t * 30.0)) * math.exp(-t * 5.0)
            val = 0.0
            for idx, f in enumerate(freqs):
                val += math.sin(2.0 * math.pi * f * (i / sample_rate)) * (1.0 / (idx + 1))
            sample = int(32767.0 * volume * env * val)
            samples.append(max(-32767, min(32767, sample)))
        return self._generate_wav(samples, sample_rate)

    def _pregenerate_sounds(self) -> None:
        """Pre-computes waveforms for low-latency playback."""
        # Drop sound: soft pop/thud
        self._wav_cache["drop"] = self._synthesize_sine_sweep(350, 160, 0.09, volume=0.4)

        # Merge sounds: pitch climbs with fruit tier (C5, D5, E5, F5, G5, A5, B5, C6...)
        base_freqs = [
            523.25, 587.33, 659.25, 698.46, 783.99,
            880.00, 987.77, 1046.50, 1174.66, 1318.51, 1567.98,
        ]
        for tier in range(1, 12):
            f1 = base_freqs[(tier - 1) % len(base_freqs)]
            f2 = f1 * 1.5  # perfect fifth
            self._wav_cache[f"merge_{tier}"] = self._synthesize_chime([f1, f2], duration_s=0.16, volume=0.45)

        # Danger warning: short alert blip
        self._wav_cache["danger"] = self._synthesize_sine_sweep(440, 400, 0.12, volume=0.3)

        # Game over: falling melody
        self._wav_cache["game_over"] = self._synthesize_sine_sweep(400, 120, 0.45, volume=0.5)

        # Start game: bright ascending cafe welcome chime (C5-E5-G5-C6)
        self._wav_cache["start"] = self._synthesize_chime([523.25, 659.25, 783.99, 1046.50], duration_s=0.24, volume=0.45)

        # Button click: crisp UI feedback tap
        self._wav_cache["click"] = self._synthesize_sine_sweep(650, 420, 0.05, volume=0.3)

    def _enqueue(self, wav_data: bytes) -> None:
        if not self.enabled or not wav_data:
            return
        try:
            self._sound_queue.put_nowait(wav_data)
        except queue.Full:
            pass

    def play_drop(self) -> None:
        if "drop" in self._wav_cache:
            self._enqueue(self._wav_cache["drop"])

    def play_merge(self, tier: int) -> None:
        key = f"merge_{tier}"
        if key in self._wav_cache:
            self._enqueue(self._wav_cache[key])
        elif "drop" in self._wav_cache:
            self._enqueue(self._wav_cache["drop"])

    def play_danger(self) -> None:
        if "danger" in self._wav_cache:
            self._enqueue(self._wav_cache["danger"])

    def play_game_over(self) -> None:
        if "game_over" in self._wav_cache:
            self._enqueue(self._wav_cache["game_over"])

    def play_start(self) -> None:
        if "start" in self._wav_cache:
            self._enqueue(self._wav_cache["start"])

    def play_click(self) -> None:
        if "click" in self._wav_cache:
            self._enqueue(self._wav_cache["click"])
