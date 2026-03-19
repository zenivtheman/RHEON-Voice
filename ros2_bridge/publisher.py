"""
ROS2 Bridge – veröffentlicht Roboter-Befehle auf ROS2-Topics.

Funktioniert in zwei Modi:
  1. ROS2_ENABLED=True  → echter rclpy-Publisher (ROS2 muss installiert sein)
  2. ROS2_ENABLED=False → Simulation (nur print, kein ROS2 nötig zum Testen)

Topics:
  /robot/voice_command  – std_msgs/String mit JSON-Payload
  /cmd_vel              – geometry_msgs/Twist für Fahrbefehle

Befehle, die direkt auf /cmd_vel gemappt werden:
  fahre vorwärts/rückwärts, drehe links/rechts

Alle anderen gehen als JSON auf /robot/voice_command.
"""

import json
from config.settings import Settings


class ROS2Bridge:
    def __init__(self, cfg: Settings):
        self.cfg = cfg
        self._node = None
        self._pub_cmd  = None   # /robot/voice_command
        self._pub_vel  = None   # /cmd_vel

        if cfg.ROS2_ENABLED:
            self._init_ros2()

    # ── ROS2 initialisieren ───────────────────
    def _init_ros2(self):
        try:
            import rclpy
            from rclpy.node import Node
            from std_msgs.msg import String
            from geometry_msgs.msg import Twist

            if not rclpy.ok():
                rclpy.init()

            self._node = rclpy.create_node("voice_command_publisher")

            self._pub_cmd = self._node.create_publisher(
                String, self.cfg.ROS2_COMMAND_TOPIC, 10
            )
            self._pub_vel = self._node.create_publisher(
                Twist, "/cmd_vel", 10
            )

            print(f"[ROS2]  Node gestartet, publiziere auf '{self.cfg.ROS2_COMMAND_TOPIC}' und '/cmd_vel'")
            self._ros2_available = True

        except ImportError:
            print("[ROS2]  rclpy nicht gefunden – wechsle in Simulations-Modus")
            self._ros2_available = False
        except Exception as e:
            print(f"[ROS2]  Init-Fehler: {e}")
            self._ros2_available = False

    # ── Hauptmethode: Befehl senden ───────────
    def send_command(self, command: dict):
        action = command.get("action", "").lower()

        # Fahrbefehle → /cmd_vel (Twist)
        if action in ("fahre", "drehe") and self._pub_vel:
            self._send_twist(command)

        # Alle anderen → /robot/voice_command (JSON-String)
        self._send_json(command)

        # Simulations-Ausgabe immer
        print(f"[ROS2]  Befehl: {json.dumps(command, ensure_ascii=False)}")

    # ── Twist-Nachricht aufbauen ──────────────
    def _send_twist(self, cmd: dict):
        if not self.cfg.ROS2_ENABLED or not getattr(self, "_ros2_available", False):
            return

        try:
            from geometry_msgs.msg import Twist
            msg = Twist()
            action    = cmd.get("action", "")
            direction = cmd.get("direction", "")
            speed     = float(cmd.get("speed", 0.5))

            if action == "fahre":
                if direction == "vorwärts":
                    msg.linear.x = speed
                elif direction == "rückwärts":
                    msg.linear.x = -speed

            elif action == "drehe":
                if direction in ("links", "left"):
                    msg.angular.z = speed
                elif direction in ("rechts", "right"):
                    msg.angular.z = -speed

            self._pub_vel.publish(msg)
            print(f"[ROS2]  /cmd_vel linear={msg.linear.x:.2f} angular={msg.angular.z:.2f}")

        except Exception as e:
            print(f"[ROS2]  Twist-Fehler: {e}")

    # ── JSON-String-Nachricht ─────────────────
    def _send_json(self, cmd: dict):
        if not self.cfg.ROS2_ENABLED or not getattr(self, "_ros2_available", False):
            return

        try:
            from std_msgs.msg import String
            msg = String()
            msg.data = json.dumps(cmd, ensure_ascii=False)
            self._pub_cmd.publish(msg)
            print(f"[ROS2]  {self.cfg.ROS2_COMMAND_TOPIC} ← {msg.data}")
        except Exception as e:
            print(f"[ROS2]  Publish-Fehler: {e}")

    # ── Aufräumen ─────────────────────────────
    def destroy(self):
        if self._node:
            import rclpy
            self._node.destroy_node()
            if rclpy.ok():
                rclpy.shutdown()
