from __future__ import annotations

from pathlib import Path


class TTSService:
    """Text-to-speech using gTTS (free, no API key required)."""

    def __init__(self, lang: str = "en", slow: bool = False):
        self.lang = lang
        self.slow = slow

    def synthesize(self, text: str, output_file: str) -> str:
        """Convert text to speech and save to output_file (.mp3 or .wav path)."""
        from gtts import gTTS

        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        tts = gTTS(text=text, lang=self.lang, slow=self.slow)
        # gTTS always writes MP3; save with .mp3 regardless of requested extension.
        mp3_path = str(Path(output_file).with_suffix(".mp3"))
        tts.save(mp3_path)
        return mp3_path

