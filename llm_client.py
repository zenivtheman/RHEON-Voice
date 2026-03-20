"""
Ollama-Client – sendet Text an phi3 und bekommt strukturierte JSON-Antwort zurück.

Das System-Prompt weist das Modell an, IMMER JSON zurückzugeben:
  {"type": "command", "command": {...}, "speech": "..."}
  {"type": "conversation", "speech": "..."}
"""

import json
import requests
from config.settings import Settings


SYSTEM_PROMPT = """
Du bist der Sprachassistent eines humanoiden Roboters.
Antworte IMMER ausschließlich mit gültigem JSON – niemals mit normalem Text.

JSON-Schema:

Wenn der Nutzer einen Bewegungs- oder Aktionsbefehl gibt:
{
  "type": "command",
  "command": {
    "action": "<fahre|drehe|greife|stoppe|hebe|senke|nicke|schüttele_kopf>",
    "direction": "<vorwärts|rückwärts|links|rechts>",   // optional
    "speed": <0.1 bis 1.0>,                              // optional, Standard 0.5
    "distance": <Meter als float>,                       // optional
    "angle": <Grad als int>,                             // optional
    "object": "<Objektname>",                            // optional, für greife
    "arm": "<links|rechts|beide>"                        // optional, für Arm-Befehle
  },
  "speech": "Ich führe den Befehl aus."
}

Wenn der Nutzer eine Frage stellt oder spricht:
{
  "type": "conversation",
  "speech": "<Deine Antwort auf Deutsch, max 2 Sätze>"
}

Beispiele:
- "Fahr nach vorne" → {"type":"command","command":{"action":"fahre","direction":"vorwärts","speed":0.5},"speech":"Ich fahre vorwärts."}
- "Greif den Ball" → {"type":"command","command":{"action":"greife","object":"ball","arm":"rechts"},"speech":"Ich greife den Ball."}
- "Stopp!" → {"type":"command","command":{"action":"stoppe"},"speech":"Angehalten."}
- "Wie heißt du?" → {"type":"conversation","speech":"Ich bin der Roboterassistent der FHWN."}
"""


class LLMClient:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self._url = f"{cfg.OLLAMA_HOST}/api/chat"
        self._history = []   # Gesprächsverlauf für Kontext
        # Modell vorladen damit es im RAM bleibt
        self._warmup()

    def query(self, user_text: str) -> str | None:
        """Sendet user_text an Ollama und gibt den Antwort-String zurück."""
        self._history.append({"role": "user", "content": user_text})

        payload = {
            "model": self.cfg.OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                *self._history,
            ],
            "stream": False,
            "format": "json",   # Ollama JSON-Mode erzwingen
        }

        try:
            resp = requests.post(
                self._url,
                json=payload,
                timeout=self.cfg.LLM_TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            answer = data["message"]["content"]

            # Verlauf pflegen (maximal 10 Turns, um Kontext klein zu halten)
            self._history.append({"role": "assistant", "content": answer})
            if len(self._history) > 20:
                self._history = self._history[-20:]

            return answer

        except requests.exceptions.ConnectionError:
            print("[LLM] FEHLER: Ollama nicht erreichbar. Läuft 'ollama serve'?")
            return None
        except requests.exceptions.Timeout:
            print("[LLM] FEHLER: Timeout – phi3 zu langsam?")
            return None
        except Exception as e:
            print(f"[LLM] FEHLER: {e}")
            return None

    def reset_history(self):
        """Gesprächsverlauf leeren."""
        self._history.clear()
    
    def _warmup(self):
        #Modell einmal aufwärmen damit Ollama es im RAM behält.
        print("[LLM]   Lade phi3:mini in RAM...")
        self.query("Hallo")
        print("[LLM]   Bereit.")
        self._history.clear()  # Warmup nicht im Verlauf behalten
