import math
import os
import struct
import tempfile
import wave


def generate_welcome_chime(path=None):
    """Generate a pleasant welcome chime WAV file using pure Python.

    Returns the path to the generated WAV file.
    """
    if path is None:
        path = os.path.join(tempfile.gettempdir(), "azan_welcome.wav")

    sample_rate = 22050
    # A pleasant ascending chime: C5, E5, G5, C6
    notes = [523.25, 659.25, 783.99, 1046.50]
    note_duration = 0.3
    pause = 0.1
    samples = []

    for freq in notes:
        n_samples = int(sample_rate * note_duration)
        for i in range(n_samples):
            t = i / sample_rate
            # Sine wave with exponential decay for a bell-like tone
            envelope = math.exp(-3 * t / note_duration)
            value = math.sin(2 * math.pi * freq * t) * envelope
            # Add a subtle harmonic for richness
            value += 0.3 * math.sin(2 * math.pi * freq * 2 * t) * envelope
            samples.append(int(value * 16000))

        # Pause between notes
        for _ in range(int(sample_rate * pause)):
            samples.append(0)

    with wave.open(path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(struct.pack(f"<{len(samples)}h", *samples))

    return path


def play_welcome(catt_path, device_name):
    """Generate and play a welcome chime on the speaker. Cleans up after."""
    from azan import player

    chime_path = generate_welcome_chime()
    try:
        success = player.play_azan(catt_path, device_name, chime_path, "100")
        if success:
            # Wait for chime to finish (~1.6 seconds)
            import time
            time.sleep(2)
        return success
    finally:
        if os.path.exists(chime_path):
            os.remove(chime_path)
