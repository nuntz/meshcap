"""Payload formatting utilities.

This module provides a simple `PayloadFormatter` class that can be extended to
apply special formatting rules to packet payloads based on their `portnum`.
"""

from __future__ import annotations

from typing import Any


class PayloadFormatter:
    """Formats packet payloads based on `portnum`.

    The initial implementation is intentionally minimal: it only checks whether
    the provided packet dictionary includes a `decoded` mapping with a
    `portnum`. If not present, it returns an empty string; otherwise, it
    returns a placeholder string indicating the payload has not been
    specially formatted yet.
    """

    def __init__(self) -> None:
        """Initialize a new payload formatter.

        Future options for configuration can be added here.
        """

    def format(self, packet: dict[str, Any]) -> str:
        """Return a formatted payload string for the given packet.

        - If `packet` lacks a `decoded` key or `decoded.portnum`, return "".
        - For `TEXT_MESSAGE_APP`, return `text:<text>` using `decoded["text"]`.
        - For `POSITION_APP`, return `pos:<lat>,<lon> <alt>m` using values from
          `decoded["position"]` with latitude/longitude to 4 decimal places and
          altitude defaulting to 0 when missing.
        - Otherwise, return a placeholder string.
        """
        decoded = packet.get("decoded")
        if not isinstance(decoded, dict):
            return ""

        portnum = decoded.get("portnum")
        if not portnum:
            return ""

        if portnum == "TEXT_MESSAGE_APP":
            text = decoded.get("text", "")
            return f"text:{text}"

        if portnum == "POSITION_APP":
            position = decoded.get("position") or {}
            lat = position.get("latitude", 0.0) or 0.0
            lon = position.get("longitude", 0.0) or 0.0
            alt = position.get("altitude")
            if alt is None:
                alt = 0
            try:
                lat_f = float(lat)
            except (TypeError, ValueError):
                lat_f = 0.0
            try:
                lon_f = float(lon)
            except (TypeError, ValueError):
                lon_f = 0.0
            try:
                alt_i = int(alt)
            except (TypeError, ValueError):
                alt_i = 0
            return f"pos:{lat_f:.4f},{lon_f:.4f} {alt_i}m"

        if portnum == "NODEINFO_APP":
            user = decoded.get("user") or {}
            # Support both camelCase and snake_case keys for robustness
            long_name = user.get("longName") or user.get("long_name") or ""
            short_name = user.get("shortName") or user.get("short_name") or ""
            hw_model = user.get("hwModel") or user.get("hw_model") or ""

            # Build name part intelligently to avoid dangling separators
            if long_name and short_name:
                name_part = f"{long_name}/{short_name}"
            elif long_name:
                name_part = str(long_name)
            elif short_name:
                name_part = str(short_name)
            else:
                name_part = ""

            hw_part = f" {hw_model}" if hw_model else ""
            return f"user:{name_part}{hw_part}"

        if portnum == "TELEMETRY_APP":
            telemetry = decoded.get("telemetry") or {}
            dev = (
                telemetry.get("device_metrics")
                or telemetry.get("deviceMetrics")
                or {}
            )
            env = (
                telemetry.get("environment_metrics")
                or telemetry.get("environmentMetrics")
                or {}
            )

            # Extract battery level and voltage
            bat_raw = dev.get("battery_level") or dev.get("batteryLevel")
            volt_raw = dev.get("voltage")
            temp_raw = env.get("temperature")

            bat_str = ""
            if bat_raw is not None:
                try:
                    # Accept int/float/str; clamp to int representation for display
                    bat_val = int(float(bat_raw))
                    bat_str = f"{bat_val}%"
                except (TypeError, ValueError):
                    bat_str = ""

            volt_str = ""
            if volt_raw is not None:
                try:
                    volt_val = float(volt_raw)
                    volt_str = f"{volt_val:.2f}V"
                except (TypeError, ValueError):
                    volt_str = ""

            parts: list[str] = []

            # Combine battery and voltage under single 'bat=' segment, with '/' when both exist
            if bat_str or volt_str:
                if bat_str and volt_str:
                    parts.append(f"bat={bat_str}/{volt_str}")
                elif bat_str:
                    parts.append(f"bat={bat_str}")
                else:
                    parts.append(f"bat={volt_str}")

            # Temperature with one decimal if available
            if temp_raw is not None:
                try:
                    temp_val = float(temp_raw)
                    parts.append(f"temp={temp_val:.1f}°C")
                except (TypeError, ValueError):
                    pass

            suffix = " ".join(parts)
            return f"tele:{suffix}" if suffix else "tele:"

        return "[unformatted]"
