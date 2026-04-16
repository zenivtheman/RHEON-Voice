from dataclasses import dataclass, field
from typing import List

@dataclass
class Settings:
    # ── Vosk ──────────────────────────────────
    VOSK_MODEL_PATH: str = "/media/pascal/Data/FH/robotik_club/spracherkennung/vosk_model_de_small"

    # ── Audio ──────────────────────────────────
    AUDIO_DEVICE: int  = 13
    SAMPLE_RATE:  int  = 16000
    CHANNELS:     int  = 1
    BLOCK_SIZE:   int  = 8000

    # ── UART ──────────────────────────────────
    UART_PORT:      str   = "/dev/ttyUSB0"
    UART_BAUDRATE:  int   = 921600
    UART_MAGIC:     bytes = b'\xAA\x55'
    UART_CHAN_L:    int   = 0x4C   # 'L'
    UART_CHAN_R:    int   = 0x52   # 'R'
    # vorerst: welcher Kanal geht an VOSK (später beide)
    UART_ACTIVE_CHAN: int = 0x4C   # 'L' oder 'R'

    # ── Wake-Word ─────────────────────────────
    WAKE_WORDS: List[str] = field(default_factory=lambda: [
        "roboter", "hey", "hallo",
    ])
    WAKE_RESPONSE: str = "Ja"

    # ── Ollama / LLM ──────────────────────────
    OLLAMA_HOST:  str = "http://localhost:11434"
    OLLAMA_MODEL: str = "phi3:mini"
    LLM_TIMEOUT:  int = 30

    # ── ROS2 ──────────────────────────────────
    ROS2_COMMAND_TOPIC:  str  = "/robot/voice_command"
    ROS2_ENABLED:        bool = False

    # ── TTS ───────────────────────────────────
    TTS_RATE:   int   = 160
    TTS_VOLUME: float = 0.9