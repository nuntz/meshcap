from __future__ import annotations

import pytest

from meshcap.payload_formatter import PayloadFormatter


class TestPayloadFormatter:
    def test_format_returns_placeholder_when_portnum_present(self) -> None:
        pf = PayloadFormatter()
        packet_with_port = {"decoded": {"portnum": 123}}
        assert pf.format(packet_with_port) == "[unformatted]"

    def test_format_returns_empty_when_no_portnum(self) -> None:
        pf = PayloadFormatter()
        packet_no_decoded = {}
        packet_decoded_no_port = {"decoded": {}}

        assert pf.format(packet_no_decoded) == ""
        assert pf.format(packet_decoded_no_port) == ""

