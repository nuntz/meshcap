from unittest.mock import Mock
from meshcap.main import MeshCap


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
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Test message"},
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
        expected = "[2023-10-19 16:00:00] Ch:5 -85dBm/12.5dB Hop:3 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Test message"
        assert result == expected

        # Additional assertions to verify specific field formatting
        assert "[2023-10-19 16:00:00]" in result  # Timestamp
        assert "Ch:5" in result  # Channel
        assert "-85dBm/12.5dB" in result  # Signal strength
        assert "Hop:3" in result  # Hop limit
        assert "from:Alice Node (!a1b2c3d4)" in result  # Resolved from address
        assert "to:Bob Node (!e5f6a7b8)" in result  # Resolved to address
        assert "Text: Test message" in result  # Payload