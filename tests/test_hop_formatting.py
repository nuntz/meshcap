from unittest.mock import Mock

from meshcap.main import MeshCap


class TestHopFormatting:
    def test_format_hop_info_with_valid_hops(self):
        # Create MeshCap instance with mock arguments
        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Sample packet with hop_start and hop_limit
        packet = {"hop_start": 7, "hop_limit": 5}

        # Call the helper and assert the formatted output
        result = capture._format_hop_info(packet)
        assert result == "Hops:2/7"

