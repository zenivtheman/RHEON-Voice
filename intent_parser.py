"""
Intent-Parser – interpretiert die JSON-Antwort des LLM.
Gibt ein normalisiertes Dict zurück, das main.py weiterverarbeitet.
"""

import json


class IntentParser:
    def parse(self, llm_output: str) -> dict:
        """
        Erwartet JSON-String vom LLM.
        Gibt immer ein dict mit mindestens {"type": ..., "speech": ...} zurück.
        """
        try:
            # Manchmal packt das Modell JSON in ```json ... ``` – bereinigen
            cleaned = llm_output.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(
                    l for l in lines if not l.startswith("```")
                )

            data = json.loads(cleaned)

            intent_type = data.get("type", "conversation")

            if intent_type == "command":
                cmd = data.get("command", {})
                if not isinstance(cmd, dict) or "action" not in cmd:
                    # Kaputtes Kommando → als Konversation behandeln
                    return {
                        "type": "conversation",
                        "speech": data.get("speech", "Ich habe das nicht verstanden."),
                    }
                return {
                    "type": "command",
                    "command": cmd,
                    "speech": data.get("speech", ""),
                }

            # Alles andere → Konversation
            return {
                "type": "conversation",
                "speech": data.get("speech", "Ich habe keine Antwort."),
            }

        except json.JSONDecodeError:
            # Modell hat kein valides JSON geliefert – Rohtext ausgeben
            print(f"[INTENT] Kein valides JSON: {llm_output[:80]}")
            return {
                "type": "conversation",
                "speech": llm_output[:200],   # Roh-Antwort sprechen
            }
