from unittest.mock import Mock

from meshcap.main import MeshCap


class TestHopFormatting:
    def setup_method(self):
        # Create MeshCap instance with mock arguments
        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        self.capture = MeshCap(mock_args)

    def test_format_hop_info_with_valid_hops(self):
        # Sample packet with hop_start and hop_limit
        packet = {"hop_start": 7, "hop_limit": 5}

        # Call the helper and assert the formatted output
        result = self.capture._format_hop_info(packet)
        assert result == "Hops:2/7"

    def test_format_hop_info_hop_start_is_zero(self):
        # hop_start and hop_limit are zero
        packet = {"hop_start": 0, "hop_limit": 0}

        result = self.capture._format_hop_info(packet)
        assert result == "Hop:0"

    def test_format_hop_info_hop_limit_greater_than_hop_start(self):
        # hop_limit is greater than hop_start
        packet = {"hop_start": 5, "hop_limit": 7}

        result = self.capture._format_hop_info(packet)
        assert result == "Hop:7"

    def test_format_hop_info_missing_hop_start(self):
        # hop_start missing; only hop_limit provided
        packet = {"hop_limit": 3}

        result = self.capture._format_hop_info(packet)
        assert result == "Hop:3"

    def test_format_hop_info_missing_hop_limit(self):
        # hop_limit missing; only hop_start provided
        packet = {"hop_start": 7}

        result = self.capture._format_hop_info(packet)
        assert result == "Hop:0"

    def test_format_hop_info_missing_both_fields(self):
        # Both hop_start and hop_limit are missing
        packet = {}

        result = self.capture._format_hop_info(packet)
        assert result == "Hop:0"

    def test_format_hop_info_full_ttl(self):
        # hop_limit equals hop_start (no hops used)
        packet = {"hop_start": 7, "hop_limit": 7}

        result = self.capture._format_hop_info(packet)
        assert result == "Hops:0/7"
