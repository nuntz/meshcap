from __future__ import annotations


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
                "position": {
                    "latitude": 12.345678,
                    "longitude": 98.765432,
                    "altitude": 150,
                },
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

    def test_nodeinfo_format_full(self) -> None:
        pf = PayloadFormatter()
        packet = {
            "decoded": {
                "portnum": "NODEINFO_APP",
                "user": {
                    "longName": "Alice Wonderland",
                    "shortName": "Alice",
                    "hwModel": "T-Echo",
                },
            }
        }
        assert pf.format(packet) == "user:Alice Wonderland/Alice T-Echo"

    def test_nodeinfo_format_partial(self) -> None:
        pf = PayloadFormatter()
        # Only longName present
        packet_long_only = {
            "decoded": {
                "portnum": "NODEINFO_APP",
                "user": {"longName": "Solo Long"},
            }
        }
        assert pf.format(packet_long_only) == "user:Solo Long"

        # Only hwModel present
        packet_hw_only = {
            "decoded": {
                "portnum": "NODEINFO_APP",
                "user": {"hwModel": "LILYGO"},
            }
        }
        assert pf.format(packet_hw_only) == "user: LILYGO"

        # Only shortName present
        packet_short_only = {
            "decoded": {
                "portnum": "NODEINFO_APP",
                "user": {"shortName": "Al"},
            }
        }
        assert pf.format(packet_short_only) == "user:Al"

    def test_telemetry_format_full(self) -> None:
        pf = PayloadFormatter()
        packet = {
            "decoded": {
                "portnum": "TELEMETRY_APP",
                "telemetry": {
                    "device_metrics": {"battery_level": 78, "voltage": 3.703},
                    "environment_metrics": {"temperature": 24.12},
                },
            }
        }
        assert pf.format(packet) == "tele:bat=78%/3.70V temp=24.1°C"

    def test_telemetry_format_partial(self) -> None:
        pf = PayloadFormatter()
        # Only voltage
        packet_volt_only = {
            "decoded": {
                "portnum": "TELEMETRY_APP",
                "telemetry": {"device_metrics": {"voltage": 3.8}},
            }
        }
        assert pf.format(packet_volt_only) == "tele:bat=3.80V"

        # Only battery
        packet_bat_only = {
            "decoded": {
                "portnum": "TELEMETRY_APP",
                "telemetry": {"device_metrics": {"battery_level": 53}},
            }
        }
        assert pf.format(packet_bat_only) == "tele:bat=53%"

        # Only temperature
        packet_temp_only = {
            "decoded": {
                "portnum": "TELEMETRY_APP",
                "telemetry": {"environment_metrics": {"temperature": 21.0}},
            }
        }
        assert pf.format(packet_temp_only) == "tele:temp=21.0°C"

        # Missing everything in telemetry
        packet_empty = {"decoded": {"portnum": "TELEMETRY_APP", "telemetry": {}}}
        assert pf.format(packet_empty) == "tele:"
