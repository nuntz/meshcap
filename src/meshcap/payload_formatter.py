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
        - Otherwise, return a placeholder string for now.
        """
        decoded = packet.get("decoded")
        if not isinstance(decoded, dict):
            return ""

        if "portnum" not in decoded:
            return ""

        return "[unformatted]"

