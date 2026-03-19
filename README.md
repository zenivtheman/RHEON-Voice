# Robot Voice Pipeline – FHWN Robotik Club

Lokale Voice-AI-Pipeline:
**Mikrofon → Wake-Word → STT → phi3 (Ollama) → Intent → ROS2 / TTS**

---

## Voraussetzungen

### 1. Python-Pakete
```bash
pip install -r requirements.txt
```

### 2. Ollama installieren + phi3 laden
```bash
# Ollama installieren: https://ollama.com
ollama pull phi3
ollama serve          # in eigenem Terminal lassen
```

### 3. Vosk Deutsches Modell
Modell herunterladen: https://alphacephei.com/vosk/models  
Empfehlung: `vosk-model-de-0.21` (1,9 GB) oder `vosk-model-small-de-0.15` (45 MB, schneller)  
Pfad in `config/settings.py` → `VOSK_MODEL_PATH` anpassen.

### 4. ROS2 (optional)
```bash
source /opt/ros/humble/setup.bash   # oder iron / jazzy
```
Ohne ROS2: `ROS2_ENABLED = False` in `config/settings.py` → läuft im Simulations-Modus.

---

## Starten
```bash
python main.py
```

---

## Dateistruktur
```
robot_voice/
├── main.py              ← Hauptprogramm / Pipeline-Orchestrator
├── llm_client.py        ← Ollama-Client (phi3)
├── intent_parser.py     ← JSON-Parser für LLM-Antworten
├── tts_engine.py        ← Text-to-Speech (pyttsx3, lokal)
├── requirements.txt
├── config/
│   └── settings.py      ← ALLE Einstellungen hier anpassen
└── ros2_bridge/
    └── publisher.py     ← ROS2-Publisher (/cmd_vel + /robot/voice_command)
```

---

## Erkannte Befehle (Beispiele)

| Sprache                   | ROS2-Action       | Topic          |
|---------------------------|-------------------|----------------|
| „Fahr nach vorne"         | `fahre vorwärts`  | /cmd_vel       |
| „Dreh links"              | `drehe links`     | /cmd_vel       |
| „Stopp"                   | `stoppe`          | /robot/voice_command |
| „Greif den Ball"          | `greife ball`     | /robot/voice_command |
| „Wie heißt du?"           | Konversation      | — (nur TTS)    |

---

## Wake-Words anpassen
In `config/settings.py`:
```python
WAKE_WORDS = ["hey robo", "hallo roboter", "hey robot"]
```

---

## ROS2-Topic abhören (zum Testen)
```bash
ros2 topic echo /robot/voice_command
ros2 topic echo /cmd_vel
```

## Testen welches Mikro da ist und passt
```bash
python3 -c "
import sounddevice as sd
devices = sd.query_devices()
for i, d in enumerate(devices):
    if d['max_input_channels'] > 0:
        for rate in [16000, 44100, 48000]:
            try:
                sd.check_input_settings(device=i, channels=1, dtype='int16', samplerate=rate)
                print(f'Gerät {i}: {d[\"name\"]} – {rate} Hz, 1 Kanal: OK')
                break
            except:
                pass
"
```

## Nicht vergessen Venv zu starten
```bash
source .venv/bin/activate
```