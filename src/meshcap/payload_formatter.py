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

        return "[unformatted]"
