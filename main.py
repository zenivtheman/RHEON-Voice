"""
Humanoider Roboter - Voice AI Pipeline
FHWN Robotik Club

Pipeline:
  Mikrofon → Wake-Word → STT (Vosk) → Ollama (phi3) → Intent → ROS2 / TTS
"""

import queue
import json
import threading
import time
import sounddevice as sd
from vosk import Model, KaldiRecognizer

from config.settings import Settings
from intent_parser import IntentParser
from llm_client import LLMClient
from tts_engine import TTSEngine
from ros2_bridge.publisher import ROS2Bridge


class RHEONVoicePipeline:
    def __init__(self):
        cfg = Settings()

        print("[INIT] Lade Vosk-Modell...")
        self.model      = Model(cfg.VOSK_MODEL_PATH)
        self.recognizer = KaldiRecognizer(self.model, cfg.SAMPLE_RATE)

        self.llm    = LLMClient(cfg)
        self.tts    = TTSEngine(cfg)
        self.intent = IntentParser()
        self.ros2   = ROS2Bridge(cfg)

        self.audio_queue   = queue.Queue()
        self.cfg           = cfg
        self._state        = "listening_for_wake"
        self._lock         = threading.Lock()
        self._tts_speaking = False  # Mikrofon stumm während TTS

    def _audio_callback(self, indata, frames, time, status):
        if status:
            print(f"[AUDIO] {status}")
        if not self._tts_speaking:  # Echo-Schutz
            self.audio_queue.put(bytes(indata))

    @property
    def state(self):
        with self._lock:
            return self._state

    @state.setter
    def state(self, value):
        with self._lock:
            self._state = value
        print(f"[STATE] → {value}")

    def _contains_wake_word(self, text: str) -> bool:
        text_lower = text.lower()
        return any(w in text_lower for w in self.cfg.WAKE_WORDS)

    def _speak(self, text: str):
        """TTS mit Echo-Schutz."""
        self._tts_speaking = True
        self.tts.speak(
            text,
            on_done=lambda: setattr(self, '_tts_speaking', False)
        )

    def run(self):
        print(f"[START] Wake-Words: {self.cfg.WAKE_WORDS}")
        print("[START] Mikrofon läuft – warte auf Wake-Word...")

        with sd.RawInputStream(
            device=self.cfg.AUDIO_DEVICE,
            samplerate=self.cfg.SAMPLE_RATE,
            blocksize=self.cfg.BLOCK_SIZE,
            dtype="int16",
            channels=1,
            callback=self._audio_callback,
        ):
            while True:
                data = self.audio_queue.get()

                if not self.recognizer.AcceptWaveform(data):
                    if self.state == "listening_for_wake":
                        partial = json.loads(self.recognizer.PartialResult())
                        text    = partial.get("partial", "").strip()
                    else:
                        continue
                else:
                    result = json.loads(self.recognizer.Result())
                    text   = result.get("text", "").strip()

                if not text:
                    continue

                if self.state == "listening_for_wake":
                    if self._contains_wake_word(text):
                        print(f"[WAKE]  '{text}'  →  Wake-Word erkannt!")
                        self._speak(self.cfg.WAKE_RESPONSE)
                        self.recognizer.Reset()
                        time.sleep(2.0)
                        while not self.audio_queue.empty():
                            self.audio_queue.get_nowait()
                        self.state = "listening_for_command"

                elif self.state == "listening_for_command":
                    print(f"[STT]   '{text}'")
                    self.recognizer.Reset()
                    self.state = "listening_for_wake"
                    threading.Thread(
                        target=self._process_command,
                        args=(text,),
                        daemon=True,
                    ).start()

    def _process_command(self, user_text: str):
        print(f"[LLM]   Sende an phi3:mini: '{user_text}'")
        llm_response = self.llm.query(user_text)

        if llm_response is None:
            self._speak("Entschuldigung, der Sprachassistent antwortet nicht.")
            return

        print(f"[LLM]   Antwort: {llm_response}")
        parsed = self.intent.parse(llm_response)

        if parsed["type"] == "command":
            cmd = parsed["command"]
            print(f"[ROS2]  Befehl → {cmd}")
            self.ros2.send_command(cmd)
            if parsed.get("speech"):
                self._speak(parsed["speech"])
        else:
            self._speak(parsed.get("speech", llm_response))


if __name__ == "__main__":
    pipeline = RHEONVoicePipeline()
    pipeline.run()