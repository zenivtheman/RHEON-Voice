"""
Text-to-Speech Engine – pyttsx3 (100% lokal, kein Internet nötig).
Spricht in einem eigenen Thread, damit die Spracherkennung nicht blockiert.
"""
import threading
import pyttsx3
from config.settings import Settings


class TTSEngine:
    def __init__(self, cfg: Settings):
        self._engine = pyttsx3.init()
        self._engine.setProperty("rate",   cfg.TTS_RATE)
        self._engine.setProperty("volume", cfg.TTS_VOLUME)
        self._set_german_voice()
        self._lock = threading.Lock()

    def _set_german_voice(self):
        voices = self._engine.getProperty("voices")
        for v in voices:
            if "de" in v.languages or "german" in v.name.lower():
                self._engine.setProperty("voice", v.id)
                print(f"[TTS]   Deutsche Stimme: {v.name}")
                return
        print("[TTS]   Keine deutsche Stimme gefunden – Standardstimme wird verwendet.")

    def speak(self, text: str, on_done=None):
        """Gibt Text asynchron aus. on_done() wird nach dem Sprechen aufgerufen."""
        if not text or not text.strip():
            if on_done:
                on_done()
            return

        def _do_speak():
            with self._lock:
                print(f"[TTS]   '{text}'")
                self._engine.say(text)
                self._engine.runAndWait()
            if on_done:
                on_done()

        threading.Thread(target=_do_speak, daemon=True).start()