from __future__ import annotations

import pytest

from meshcap.payload_formatter import PayloadFormatter


class TestPayloadFormatter:
    def test_text_message_format(self) -> None:
        pf = PayloadFormatter()
        packet = {"decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello world"}}
        assert pf.format(packet) == "text:Hello world"

    def test_position_format_with_altitude(self) -> None:
        pf = PayloadFormatter()
        packet = {
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 12.345678, "longitude": 98.765432, "altitude": 150},
            }
        }
        assert pf.format(packet) == "pos:12.3457,98.7654 150m"

    def test_position_format_without_altitude(self) -> None:
        pf = PayloadFormatter()
        packet = {
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": -33.865, "longitude": 151.209444},
            }
        }
        assert pf.format(packet) == "pos:-33.8650,151.2094 0m"

    def test_format_returns_empty_when_no_portnum(self) -> None:
        pf = PayloadFormatter()
        packet_no_decoded = {}
        packet_decoded_no_port = {"decoded": {}}

        assert pf.format(packet_no_decoded) == ""
        assert pf.format(packet_decoded_no_port) == ""
