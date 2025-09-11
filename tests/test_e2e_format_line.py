from unittest.mock import Mock
from datetime import datetime, timezone
from meshcap.main import MeshCap


def local_ts_str(epoch: int) -> str:
    """Convert epoch timestamp to local time string format used in packet output."""
    return (
        datetime.fromtimestamp(epoch, timezone.utc)
        .astimezone()
        .strftime("%Y-%m-%d %H:%M:%S")
    )


class MockInterface:
    """Mock interface for testing node resolution."""

    def __init__(self, nodes=None):
        self.nodes = nodes or {}


class TestE2EFormatLine:
    """End-to-end test for full packet formatting line output."""

    def test_full_format_line_with_addressing_and_signals(self):
        """Test that _format_packet produces complete formatted line with all fields."""
        # Build minimal packet with key fields for comprehensive formatting test
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "hop_start": 7,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {
                    "latitude": 12.345678,
                    "longitude": 98.765432,
                    "altitude": 150,
                },
            },
        }

        # Mock interface with node resolution data
        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        # Create MeshCap instance with mock args
        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Format the packet
        result = capture._format_packet(packet, mock_interface, False)

        # Assert the full line contains all expected components
        ts = local_ts_str(1697731200)
        expected = (
            f"[{ts}] Ch:5 -85dBm/12.5dB Hops:4/7 "
            f"from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) "
            f"pos:12.3457,98.7654 150m"
        )
        assert result == expected

        # Additional assertions to verify specific field formatting
        assert f"[{local_ts_str(1697731200)}]" in result  # Timestamp
        assert "Ch:5" in result  # Channel
        assert "-85dBm/12.5dB" in result  # Signal strength
        assert "Hops:4/7" in result  # Hop usage
        assert "from:Alice Node (!a1b2c3d4)" in result  # Resolved from address
        assert "to:Bob Node (!e5f6a7b8)" in result  # Resolved to address
        assert "pos:12.3457,98.7654 150m" in result  # Payload
