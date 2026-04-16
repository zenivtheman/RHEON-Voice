"""
Zentrale Konfiguration – hier alles anpassen!
"""
from dataclasses import dataclass, field
from typing import List


@dataclass
class Settings:
    # ── Vosk ──────────────────────────────────
    VOSK_MODEL_PATH: str = "/media/pascal/Data/FH/robotik_club/spracherkennung/vosk_model_de_small"

    # ── Audio ──────────────────────────────────
    AUDIO_DEVICE: int  = 13       # sounddevice Geräte-ID  (None = Standard) 14/13 bei pascal
    SAMPLE_RATE:  int  = 16000
    CHANNELS:     int = 1
    BLOCK_SIZE:   int  = 8000 # 8000 Samples = 0.5 Sekunde Audio

    # ── Wake-Word ─────────────────────────────
    WAKE_WORDS: List[str] = field(default_factory=lambda: [
        "roboter",
        "hey",
        "hallo",
    ])
    WAKE_RESPONSE: str = "Ja"

    # ── Ollama / LLM ──────────────────────────
    OLLAMA_HOST:  str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3:mini"
    LLM_TIMEOUT:  int = 30       # Sekunden

    # ── ROS2 ──────────────────────────────────
    ROS2_COMMAND_TOPIC:  str = "/robot/voice_command"
    ROS2_ENABLED:        bool = False   # False = nur simulieren (kein ROS2 nötig)

    # ── TTS ───────────────────────────────────
    TTS_RATE:   int = 160        # Wörter pro Minute
    TTS_VOLUME: float = 0.9
