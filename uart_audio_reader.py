"""
UART Audio Reader
Liest I2S-Audioframes vom ESP32 und legt int16-Samples in eine Queue.

Frame-Format:
  [0xAA][0x55] [KANAL 1B] [LEN_H 1B] [LEN_L 1B] [DATA N*2B] [CRC8 1B]
  KANAL: 0x4C = 'L', 0x52 = 'R'
  DATA:  int16 Samples, little-endian, bereits auf 16-Bit konvertiert (ESP32-seitig)
"""

import queue
import serial
from config.settings import Settings


class UartAudioReader:
    """Liest Frames vom ESP32 und legt int16-Samples in eine Queue."""

    MAGIC = b'\xAA\x55'

    def __init__(self, cfg: Settings, audio_queue: queue.Queue, tts_speaking_ref):
        """
        Args:
            cfg:              Settings-Instanz
            audio_queue:      Queue in die Samples geschrieben werden
            tts_speaking_ref: lambda/callable das True zurückgibt wenn TTS aktiv
        """
        self.cfg          = cfg
        self.queue        = audio_queue
        self.tts_speaking = tts_speaking_ref
        self.ser          = serial.Serial(
            port=cfg.UART_PORT,
            baudrate=cfg.UART_BAUDRATE,
            timeout=1.0
        )

    def _crc8(self, data: bytes) -> int:
        crc = 0
        for b in data:
            crc ^= b
            for _ in range(8):
                crc = (crc << 1) ^ 0x07 if crc & 0x80 else crc << 1
                crc &= 0xFF
        return crc

    def _sync(self):
        """Sucht Magic-Bytes im Stream – stellt Synchronisation nach Fehlern wieder her."""
        buf = b''
        while True:
            byte = self.ser.read(1)
            if not byte:
                continue
            buf += byte
            if buf[-2:] == self.MAGIC:
                return

    def _read_frame(self):
        """
        Liest einen vollständigen Frame.
        Gibt (kanal, payload) zurück oder None bei Fehler.
        """
        self._sync()

        header = self.ser.read(3)  # KANAL, LEN_H, LEN_L
        if len(header) < 3:
            return None

        kanal, len_h, len_l = header
        length = (len_h << 8) | len_l

        payload = self.ser.read(length)
        crc_byte = self.ser.read(1)

        if len(payload) < length or not crc_byte:
            return None

        if self._crc8(payload) != crc_byte[0]:
            print("[UART] CRC-Fehler – Frame verworfen")
            return None

        return kanal, payload

    def run(self):
        """
        Blockierender Loop – in einem eigenen Thread starten.
        Legt nur Frames des aktiven Kanals in die Queue.
        Verwirft Frames wenn TTS gerade spricht.
        """
        print(f"[UART] Lese von {self.cfg.UART_PORT} @ {self.cfg.UART_BAUDRATE} Baud")

        while True:
            result = self._read_frame()
            if result is None:
                continue

            kanal, payload = result

            # Vorerst: nur aktiver Kanal → Queue
            # TODO: später beide Kanäle in separate Queues (L/R-Feature)
            if kanal != self.cfg.UART_ACTIVE_CHAN:
                continue

            if not self.tts_speaking():
                self.queue.put(payload)
