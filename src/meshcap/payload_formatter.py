"""Payload formatting utilities.

This module provides a simple `PayloadFormatter` class that can be extended to
apply special formatting rules to packet payloads based on their `portnum`.
"""

from __future__ import annotations

from typing import Any, Callable

from . import constants


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

        Uses a dispatch table mapping `portnum` to private helpers.
        """
        decoded = packet.get("decoded")
        if not isinstance(decoded, dict):
            return ""

        portnum = decoded.get("portnum")
        if not portnum:
            return ""

        # Build dispatch map. Keys cover current string-based portnums.
        dispatch: dict[str, Callable[[dict[str, Any]], str]] = {
            constants.TEXT_MESSAGE_APP: self._format_text,
            constants.POSITION_APP: self._format_position,
            constants.NODEINFO_APP: self._format_nodeinfo,
            constants.TELEMETRY_APP: self._format_telemetry,
        }

        handler = dispatch.get(portnum)
        if handler is None:
            return "[unformatted]"
        return handler(decoded)

    def _format_text(self, decoded: dict[str, Any]) -> str:
        text = decoded.get("text", "")
        return f"text:{text}"

    def _format_position(self, decoded: dict[str, Any]) -> str:
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
        return f"pos:{lat_f:.{constants.POSITION_PRECISION}f},{lon_f:.{constants.POSITION_PRECISION}f} {alt_i}m"

    def _format_nodeinfo(self, decoded: dict[str, Any]) -> str:
        user = decoded.get("user") or {}
        long_name = user.get("longName") or user.get("long_name") or ""
        short_name = user.get("shortName") or user.get("short_name") or ""
        hw_model = user.get("hwModel") or user.get("hw_model") or ""

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

    def _format_telemetry(self, decoded: dict[str, Any]) -> str:
        telemetry = decoded.get("telemetry") or {}
        dev = telemetry.get("device_metrics") or telemetry.get("deviceMetrics") or {}
        env = (
            telemetry.get("environment_metrics")
            or telemetry.get("environmentMetrics")
            or {}
        )

        bat_raw = dev.get("battery_level") or dev.get("batteryLevel")
        volt_raw = dev.get("voltage")
        temp_raw = env.get("temperature")

        bat_str = ""
        if bat_raw is not None:
            try:
                bat_val = int(float(bat_raw))
                bat_str = f"{bat_val}%"
            except (TypeError, ValueError):
                bat_str = ""

        volt_str = ""
        if volt_raw is not None:
            try:
                volt_val = float(volt_raw)
                volt_str = f"{volt_val:.{constants.VOLTAGE_PRECISION}f}V"
            except (TypeError, ValueError):
                volt_str = ""

        parts: list[str] = []
        if bat_str or volt_str:
            if bat_str and volt_str:
                parts.append(f"bat={bat_str}/{volt_str}")
            elif bat_str:
                parts.append(f"bat={bat_str}")
            else:
                parts.append(f"bat={volt_str}")

        if temp_raw is not None:
            try:
                temp_val = float(temp_raw)
                parts.append(f"temp={temp_val:.{constants.TEMPERATURE_PRECISION}f}°C")
            except (TypeError, ValueError):
                pass

        suffix = " ".join(parts)
        return f"tele:{suffix}" if suffix else "tele:"
