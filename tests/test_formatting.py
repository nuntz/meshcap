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


def with_suffix_if_portnum(packet: dict, s: str) -> str:
    """Append the payload placeholder when a portnum is present.

    For packets that include a decoded.portnum, the formatter now appends
    " [unformatted]" at the end of the line. This helper mirrors that
    behavior for expected strings across tests.
    """
    decoded = packet.get("decoded")
    if isinstance(decoded, dict) and "portnum" in decoded:
        return s + " [unformatted]"
    return s


class MockInterface:
    """Mock interface for testing node resolution."""

    def __init__(self, nodes=None):
        self.nodes = nodes or {}


class TestFormatPacket:
    """Test cases for the format_packet function."""

    def test_text_message_packet(self):
        """Test formatting a text message packet."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Hello World!"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_position_packet(self):
        """Test formatting a position packet."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -92,
            "rxSnr": 8.0,
            "fromId": "!12345678",
            "toId": "!87654321",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 37.7749, "longitude": -122.4194},
            },
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -92dBm/8.0dB Hop:0 from:!12345678 to:!87654321 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_encrypted_packet(self):
        """Test formatting an encrypted packet."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -78,
            "rxSnr": 15.2,
            "fromId": "!aaaabbbb",
            "toId": "!ccccdddd",
            "encrypted": b"some encrypted data here",
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -78dBm/15.2dB Hop:0 from:!aaaabbbb to:!ccccdddd Encrypted: length=24"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_encrypted_packet_no_decoded(self):
        """Test formatting a packet with no decoded field."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -95,
            "rxSnr": 5.5,
            "fromId": "!11111111",
            "toId": "!22222222",
            "encrypted": b"encrypted",
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:3 -95dBm/5.5dB Hop:0 from:!11111111 to:!22222222 Encrypted: length=9"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_other_portnum_packet(self):
        """Test formatting a packet with an unknown portnum."""
        packet = {
            "rxTime": 1697731200,
            "channel": 4,
            "rxRssi": -88,
            "rxSnr": 10.0,
            "fromId": "!abcd1234",
            "toId": "!5678efab",
            "decoded": {"portnum": "UNKNOWN_APP", "data": {"some": "data"}},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:4 -88dBm/10.0dB Hop:0 from:!abcd1234 to:!5678efab UNKNOWN_APP: [UNKNOWN_APP]"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_other_portnum_packet_verbose(self):
        """Test formatting a packet with an unknown portnum in verbose mode."""
        packet = {
            "rxTime": 1697731200,
            "channel": 4,
            "rxRssi": -88,
            "rxSnr": 10.0,
            "fromId": "!abcd1234",
            "toId": "!5678efab",
            "decoded": {"portnum": "UNKNOWN_APP", "data": {"some": "data"}},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:4 -88dBm/10.0dB Hop:0 from:!abcd1234 to:!5678efab UNKNOWN_APP: {{'portnum': 'UNKNOWN_APP', 'data': {{'some': 'data'}}}}"
        assert (
            capture._format_packet(packet, MockInterface(), False, verbose=True)
            == with_suffix_if_portnum(packet, expected)
        )

    def test_missing_fields_defaults(self):
        """Test formatting a packet with missing fields using defaults."""
        packet = {}

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(0)
        expected = f"[{ts}] Ch:0 - Hop:0 from:unknown to:unknown Encrypted: length=0"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_empty_text_message(self):
        """Test formatting a text message packet with empty text."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -80,
            "rxSnr": 12.0,
            "fromId": "!ae511234",
            "toId": "!de515678",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": ""},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -80dBm/12.0dB Hop:0 from:!ae511234 to:!de515678 Text: "
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_position_packet_missing_coordinates(self):
        """Test formatting a position packet with missing coordinates."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 7.5,
            "fromId": "!a0512345",
            "toId": "!1a4ee678",
            "decoded": {"portnum": "POSITION_APP", "position": {}},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -90dBm/7.5dB Hop:0 from:!a0512345 to:!1a4ee678 Position: lat=0, lon=0"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_decoded_with_empty_portnum(self):
        """Test formatting a packet with decoded field but empty portnum."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -85,
            "rxSnr": 9.0,
            "fromId": "!e0a71234",
            "toId": "!e0a75678",
            "decoded": {},
            "encrypted": b"test",
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:3 -85dBm/9.0dB Hop:0 from:!e0a71234 to:!e0a75678 Encrypted: length=4"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)


class TestNodeResolution:
    """Test cases for node name resolution functionality."""

    def test_node_resolution_known_ids(self):
        """Test that known fromId is correctly resolved to its longName."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_node_resolution_unknown_to_id_fallback(self):
        """Test that an unknown toId correctly falls back to its raw ID."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!0eabc123",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!a1b2c3d4) to:!0eabc123 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_node_resolution_disabled(self):
        """Test that when no_resolve is True, no name resolution occurs."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = (
            f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Hello!"
        )
        assert capture._format_packet(packet, mock_interface, True) == with_suffix_if_portnum(packet, expected)

    def test_node_resolution_no_interface(self):
        """Test that no resolution occurs when interface is None."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = (
            f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Hello!"
        )
        assert capture._format_packet(packet, None, False) == with_suffix_if_portnum(packet, expected)

    def test_node_resolution_missing_user_data(self):
        """Test that nodes without proper user data fall back to raw IDs."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {
                    "user": {}  # Missing longName
                },
                "!e5f6a7b8": {},  # Missing user entirely
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = (
            f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Hello!"
        )
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)


class TestNewFormattingFeatures:
    """Test cases for the new formatting features with resolved names and raw IDs."""

    def test_new_format_with_resolved_names(self):
        """Test that the new format correctly displays both resolved names and raw IDs."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Hello World!"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_new_format_with_unresolved_names(self):
        """Test that unresolved node IDs fall back to raw IDs in the new format."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!ca0e1234",
            "toId": "!0eabc567",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Testing unresolved"},
        }

        # Mock interface only has one of the two nodes
        mock_interface = MockInterface(
            {
                "!ca0e1234": {"user": {"longName": "Known User"}}
                # '!0eabc567' is not in the nodes list
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -90dBm/8.5dB Hop:0 from:Known User (!ca0e1234) to:!0eabc567 Text: Testing unresolved"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_new_format_with_no_resolve_flag(self):
        """Test that --no-resolve flag shows only raw IDs in the new format."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -88,
            "rxSnr": 10.2,
            "fromId": "!abcd2345",
            "toId": "!1234a890",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 40.7128, "longitude": -74.0060},
            },
        }

        # Mock interface has both nodes available for resolution
        mock_interface = MockInterface(
            {
                "!abcd2345": {"user": {"longName": "First User"}},
                "!1234a890": {"user": {"longName": "Second User"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        # With no_resolve=True, should only show raw IDs despite having resolvable names
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:3 -88dBm/10.2dB Hop:0 from:!abcd2345 to:!1234a890 Position: lat=40.7128, lon=-74.006"
        assert capture._format_packet(packet, mock_interface, True) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_with_from_and_to(self):
        """Test formatting a packet that includes from and to integer fields."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "from": 123456789,
            "to": 987654321,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello with from/to!"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Hello with from/to!"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_with_source_and_dest(self):
        """Test formatting a packet that includes source and dest in decoded payload."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "from": 111111111,
            "to": 222222222,
            "decoded": {
                "portnum": "TEXT_MESSAGE_APP",
                "text": "Message with routing info",
                "source": 333333333,
                "dest": 444444444,
            },
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -90dBm/8.5dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Message with routing info"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_without_source_and_dest(self):
        """Test formatting a packet without source and dest fields (should default to unknown)."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -85,
            "rxSnr": 10.0,
            "fromId": "!ae511234",
            "toId": "!de515678",
            "from": 555555555,
            "to": 666666666,
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 37.7749, "longitude": -122.4194},
                # Note: no source or dest fields in decoded
            },
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:3 -85dBm/10.0dB Hop:0 from:!ae511234 to:!de515678 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_all_address_fields_resolvable(self):
        """Test formatting a packet with all four address fields, all resolvable."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!aaaaaaaa",
            "toId": "!bbbbbbbb",
            "from": 2863311530,  # !aaaaaaaa as int
            "to": 3149642683,  # !bbbbbbbb as int
            "decoded": {
                "portnum": "TEXT_MESSAGE_APP",
                "text": "Full routing example",
                "source": 3435973836,  # !cccccccc as int
                "dest": 3722304989,  # !dddddddd as int
            },
        }

        mock_interface = MockInterface(
            {
                "!aaaaaaaa": {"user": {"longName": "Alice Node"}},
                "!bbbbbbbb": {"user": {"longName": "Bob Node"}},
                "!cccccccc": {"user": {"longName": "Charlie Node"}},
                "!dddddddd": {"user": {"longName": "Delta Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!aaaaaaaa) to:Bob Node (!bbbbbbbb) Text: Full routing example"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_mixed_resolvable_unresolvable(self):
        """Test formatting a packet with only some address fields resolvable."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!ca0e0123",
            "toId": "!0eabc099",
            "from": 1111111111,
            "to": 2222222222,
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 37.7749, "longitude": -122.4194},
                "source": 3333333333,
                "dest": 4444444444,
            },
        }

        # Only resolve some of the nodes
        mock_interface = MockInterface(
            {
                "!ca0e0123": {"user": {"longName": "Known User"}}
                # Note: other nodes should not resolve
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -90dBm/8.5dB Hop:0 from:Known User (!ca0e0123) to:!0eabc099 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_only_fromid_toid(self):
        """Test formatting a packet with only fromId and toId (backward compatibility)."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -80,
            "rxSnr": 15.0,
            "fromId": "!a1dca0e1",
            "toId": "!a1dca0e2",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Simple message"},
        }

        mock_interface = MockInterface(
            {
                "!a1dca0e1": {"user": {"longName": "Old Sender"}},
                "!a1dca0e2": {"user": {"longName": "Old Receiver"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -80dBm/15.0dB Hop:0 from:Old Sender (!a1dca0e1) to:Old Receiver (!a1dca0e2) Text: Simple message"
        assert capture._format_packet(packet, mock_interface, False) == with_suffix_if_portnum(packet, expected)

    def test_format_encrypted_packet_comprehensive(self):
        """Test formatting an encrypted packet without decoded section."""
        packet = {
            "rxTime": 1697731200,
            "channel": 4,
            "rxRssi": -95,
            "rxSnr": 3.2,
            "fromId": "!eecabc01",
            "toId": "!eecabc02",
            "encrypted": b"this is some encrypted binary data here",
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:4 -95dBm/3.2dB Hop:0 from:!eecabc01 to:!eecabc02 Encrypted: length=39"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_format_packet_with_hop_limit(self):
        """Test formatting a packet with hop_limit field."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -80,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "hopLimit": 3,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -80dBm/12.0dB Hop:3 from:!a1b2c3d4 to:!e5f6a7b8 Text: Hello World!"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_node_number_display_instead_of_node_id(self):
        """Test that _format_packet displays node numbers (123456789) instead of node IDs (!075bcd15)."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "from": 123456789,  # This should be displayed as 123456789
            "to": 987654321,  # This should be displayed as 987654321
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        # Create mock interface with node that has both node ID and node number
        mock_interface = MockInterface(
            {
                "123456789": {"user": {"longName": "Test Node"}},  # Node number as key
                "987654321": {
                    "user": {"longName": "Target Node"}
                },  # Node number as key
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Expected: canonical addressing format using from/to pairs
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.0dB Hop:0 from:!075bcd15 to:!3ade68b1 Text: Hello World!"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_missing_node_number_fallback_to_node_id(self):
        """Test that _format_packet falls back to node ID when node number is not available (e.g., old capture files)."""
        # Simulate old capture file scenario where we have node data but no node numbers
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!deadbeef",  # String node ID from old capture
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "From old capture"},
        }

        # Mock interface has node data but no 'num' field (simulating old node data)
        mock_interface = MockInterface(
            {
                "!deadbeef": {
                    "user": {"longName": "Old Node"}
                    # Note: no 'num' field in this node data
                }
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Expected: should fall back to node ID since no node number is available
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -90dBm/8.5dB Hop:0 from:Old Node (!deadbeef) to:unknown Text: From old capture"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_missing_node_number_with_string_identifier_fallback(self):
        """Test fallback behavior with string identifier when no node number is available."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -85,
            "rxSnr": 10.0,
            "fromId": "!abc12345",
            "toId": "!def67890",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 40.0, "longitude": -74.0},
            },
        }

        # Interface has partial node data - one with user info but no num, one completely missing
        mock_interface = MockInterface(
            {
                "!abc12345": {
                    "user": {"longName": "Known Old Node"}
                    # No 'num' field
                }
                # "!def67890" is completely missing from interface
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Expected: resolved name with node ID fallback for first, raw node ID for second
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:3 -85dBm/10.0dB Hop:0 from:Known Old Node (!abc12345) to:!def67890 Position: lat=40.0, lon=-74.0"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)


class TestFormatNodeLabel:
    """Test cases for the format_node_label method."""

    def test_format_node_label_no_resolve(self):
        """Test format_node_label with no_resolve=True returns user_id."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(mock_interface, "!a1b2c3d4", no_resolve=True)
        assert result == "!a1b2c3d4"

        result = capture.format_node_label(mock_interface, 123456789, no_resolve=True)
        assert result == "!075bcd15"

    def test_format_node_label_hex_only_mode(self):
        """Test format_node_label with hex-only mode returns user_id."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="hex-only"
        )
        assert result == "!a1b2c3d4"

    def test_format_node_label_named_only_mode_with_long_name(self):
        """Test format_node_label with named-only mode returns best name."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-only"
        )
        assert result == "Alice Node"

    def test_format_node_label_named_only_mode_no_name_fallback(self):
        """Test format_node_label with named-only mode falls back to user_id when no name available."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {}}  # No user data
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-only"
        )
        assert result == "!a1b2c3d4"

    def test_format_node_label_named_with_hex_mode_with_long_name(self):
        """Test format_node_label with named-with-hex mode returns name and hex."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-with-hex"
        )
        assert result == "Alice Node (!a1b2c3d4)"

    def test_format_node_label_named_with_hex_mode_no_name_fallback(self):
        """Test format_node_label with named-with-hex mode falls back to user_id when no name available."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {}}  # No user data
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-with-hex"
        )
        assert result == "!a1b2c3d4"

    def test_format_node_label_with_short_name_priority(self):
        """Test format_node_label prefers shortName over longName."""
        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {
                    "user": {"longName": "Alice Long Node Name", "shortName": "Alice"}
                }
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-only"
        )
        assert result == "Alice"

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-with-hex"
        )
        assert result == "Alice (!a1b2c3d4)"

    def test_format_node_label_with_empty_short_name(self):
        """Test format_node_label handles empty/whitespace shortName correctly."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node", "shortName": "   "}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, "!a1b2c3d4", label_mode="named-only"
        )
        assert (
            result == "Alice Node"
        )  # Falls back to longName since shortName is whitespace

    def test_format_node_label_integer_node_input(self):
        """Test format_node_label handles integer node input correctly."""
        mock_interface = MockInterface(
            {"!075bcd15": {"user": {"longName": "Node 123456789"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            mock_interface, 123456789, label_mode="named-with-hex"
        )
        assert result == "Node 123456789 (!075bcd15)"

    def test_format_node_label_no_interface(self):
        """Test format_node_label handles None interface correctly."""
        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(
            None, "!a1b2c3d4", label_mode="named-with-hex"
        )
        assert result == "!a1b2c3d4"  # Falls back to user_id

    def test_format_node_label_invalid_mode(self):
        """Test format_node_label raises ValueError for invalid label_mode."""
        mock_interface = MockInterface({})

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        try:
            capture.format_node_label(
                mock_interface, "!a1b2c3d4", label_mode="invalid-mode"
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown label_mode: invalid-mode" in str(e)

    def test_format_node_label_default_mode(self):
        """Test format_node_label uses named-with-hex as default mode."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        result = capture.format_node_label(mock_interface, "!a1b2c3d4")
        assert result == "Alice Node (!a1b2c3d4)"


class TestRSSIHandling:
    """Test cases for robust RSSI handling."""

    def test_packet_with_both_rssi_and_snr(self):
        """Test formatting a packet with both rxRssi and rxSnr present."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Both values"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.5dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Both values"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_packet_with_only_rssi(self):
        """Test formatting a packet with only rxRssi present."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "rxRssi": -85,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Only RSSI"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = (
            f"[{ts}] Ch:1 -85dBm Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Only RSSI"
        )
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_packet_with_only_snr(self):
        """Test formatting a packet with only rxSnr present."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "rxSnr": 12.5,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Only SNR"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = (
            f"[{ts}] Ch:1 12.5dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Only SNR"
        )
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_packet_with_rssi_fallback(self):
        """Test formatting a packet that uses rssi fallback when rxRssi is missing."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "rssi": -90,  # Fallback field
            "rxSnr": 8.0,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "RSSI fallback"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -90dBm/8.0dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: RSSI fallback"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_packet_with_no_signal_values(self):
        """Test formatting a packet with no signal strength values."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "No signals"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 - Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: No signals"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)

    def test_packet_rxrssi_preferred_over_rssi_fallback(self):
        """Test that rxRssi is preferred over rssi fallback when both are present."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "rxRssi": -85,  # This should be used
            "rssi": -90,  # This should be ignored
            "rxSnr": 12.5,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Preference test"},
        }

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.5dB Hop:0 from:!a1b2c3d4 to:!e5f6a7b8 Text: Preference test"
        assert capture._format_packet(packet, MockInterface(), False) == with_suffix_if_portnum(packet, expected)


class TestGoldenExamples:
    """Golden examples for stabilizing text and position packet output formats."""

    def test_text_packet_with_resolved_names_golden(self):
        """Golden example: Text packet with resolved names -> 'Name(!hex)' format."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello from Alice!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:1 -85dBm/12.5dB Hop:0 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Hello from Alice!"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_text_packet_without_resolved_names_golden(self):
        """Golden example: Text packet without resolved names -> '!hex' format."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 2,
            "rxRssi": -92,
            "rxSnr": 8.0,
            "fromId": "!12345678",
            "toId": "!87654321",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Message from unknown"},
        }

        # Empty interface - no name resolution available
        mock_interface = MockInterface({})

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:2 -92dBm/8.0dB Hop:0 from:!12345678 to:!87654321 Text: Message from unknown"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_text_packet_mixed_resolution_golden(self):
        """Golden example: Text packet with mixed name resolution."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 3,
            "rxRssi": -78,
            "rxSnr": 15.2,
            "fromId": "!aaaa1234",
            "toId": "!bbbb5678",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Mixed resolution test"},
        }

        mock_interface = MockInterface(
            {
                "!aaaa1234": {"user": {"longName": "Known User"}}
                # !bbbb5678 not in nodes - should fallback to hex
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:3 -78dBm/15.2dB Hop:0 from:Known User (!aaaa1234) to:!bbbb5678 Text: Mixed resolution test"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_position_packet_with_lat_lon_preview_golden(self):
        """Golden example: Position packet with lat/lon/alt preview."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 4,
            "rxRssi": -88,
            "rxSnr": 10.0,
            "fromId": "!cccc1234",
            "toId": "!dddd5678",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "altitude": 43,
                },
            },
        }

        mock_interface = MockInterface(
            {
                "!cccc1234": {"user": {"longName": "GPS Tracker"}},
                "!dddd5678": {"user": {"longName": "Base Station"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Note: Current implementation shows lat/lon, not altitude in preview
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:4 -88dBm/10.0dB Hop:0 from:GPS Tracker (!cccc1234) to:Base Station (!dddd5678) Position: lat=37.7749, lon=-122.4194"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_position_packet_without_names_golden(self):
        """Golden example: Position packet without resolved names."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -95,
            "rxSnr": 5.5,
            "fromId": "!eeee1234",
            "toId": "!ffff5678",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 40.7128, "longitude": -74.0060},
            },
        }

        # Empty interface - no name resolution
        mock_interface = MockInterface({})

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -95dBm/5.5dB Hop:0 from:!eeee1234 to:!ffff5678 Position: lat=40.7128, lon=-74.006"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_position_packet_missing_coords_golden(self):
        """Golden example: Position packet with missing coordinates defaults to 0."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 6,
            "rxRssi": -90,
            "rxSnr": 7.5,
            "fromId": "!aaaa9999",
            "toId": "!bbbb8888",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {},  # Empty position data
            },
        }

        mock_interface = MockInterface(
            {"!aaaa9999": {"user": {"longName": "Bad GPS Unit"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:6 -90dBm/7.5dB Hop:0 from:Bad GPS Unit (!aaaa9999) to:!bbbb8888 Position: lat=0, lon=0"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_encrypted_payload_preview_unchanged_golden(self):
        """Golden example: Encrypted payload preview shows length, unchanged by resolution."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 7,
            "rxRssi": -82,
            "rxSnr": 13.8,
            "fromId": "!aaaa0001",
            "toId": "!bbbb0002",
            "encrypted": b"this is some encrypted binary payload data here for testing",
        }

        mock_interface = MockInterface(
            {
                "!aaaa0001": {"user": {"longName": "Secure Node Alpha"}},
                "!bbbb0002": {"user": {"longName": "Secure Node Beta"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:7 -82dBm/13.8dB Hop:0 from:Secure Node Alpha (!aaaa0001) to:Secure Node Beta (!bbbb0002) Encrypted: length=59"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_encrypted_payload_no_names_golden(self):
        """Golden example: Encrypted payload without name resolution."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 8,
            "rxRssi": -99,
            "rxSnr": 2.1,
            "fromId": "!cccc0001",
            "toId": "!dddd0002",
            "encrypted": b"encrypted",
        }

        # No name resolution available
        mock_interface = MockInterface({})

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:8 -99dBm/2.1dB Hop:0 from:!cccc0001 to:!dddd0002 Encrypted: length=9"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_consistent_utc_timestamp_formatting_golden(self):
        """Golden example: UTC timestamp formatting consistency across different scenarios."""
        # Test various timestamps to ensure consistent formatting
        test_cases = [
            {
                "rxTime": 0,  # Unix epoch
                "expected_time": f"[{local_ts_str(0)}]",
            },
            {
                "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
                "expected_time": f"[{local_ts_str(1697731200)}]",
            },
            {
                "rxTime": 1735689600,  # 2025-01-01 00:00:00 UTC (future date)
                "expected_time": f"[{local_ts_str(1735689600)}]",
            },
        ]

        mock_interface = MockInterface({})
        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        for case in test_cases:
            packet = {
                "rxTime": case["rxTime"],
                "channel": 1,
                "rxRssi": -85,
                "rxSnr": 12.0,
                "fromId": "!aaaa0000",
                "toId": "!bbbb0000",
                "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Timestamp test"},
            }

            result = capture._format_packet(packet, mock_interface, False)
            assert result.startswith(case["expected_time"]), (
                f"Expected {case['expected_time']}, got: {result[:21]}"
            )

    def test_hop_limit_display_golden(self):
        """Golden example: Hop limit display in packet formatting."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 9,
            "rxRssi": -87,
            "rxSnr": 9.5,
            "fromId": "!aaaa1111",
            "toId": "!bbbb2222",
            "hopLimit": 5,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Multi-hop message"},
        }

        mock_interface = MockInterface(
            {"!aaaa1111": {"user": {"longName": "Router Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:9 -87dBm/9.5dB Hop:5 from:Router Node (!aaaa1111) to:!bbbb2222 Text: Multi-hop message"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_empty_text_message_golden(self):
        """Golden example: Empty text message handling."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 10,
            "rxRssi": -80,
            "rxSnr": 12.0,
            "fromId": "!cccc3333",
            "toId": "!dddd4444",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": ""},
        }

        mock_interface = MockInterface(
            {"!cccc3333": {"user": {"longName": "Silent Node"}}}
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:10 -80dBm/12.0dB Hop:0 from:Silent Node (!cccc3333) to:!dddd4444 Text: "
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_next_hop_present_named_with_hex(self):
        """Test that when nextHop is present, it shows NH:<label> after Hop:<N>."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "nextHop": 0x15,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Directed hop"},
        }

        # Mock interface with node resolution data
        mock_interface = MockInterface(
            {
                "!a1b2c315": {
                    "user": {"longName": "NH Node"}
                },  # ends with 15 to match nextHop 0x15
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Expected format includes NH: field between Hop:3 and from:
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 NH:NH Node (!a1b2c315) from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Directed hop"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_next_hop_no_resolve_hex_only(self):
        """Test that when no_resolve=True, nextHop shows only hex ID without name resolution."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "nextHop": 0x15,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Directed hop"},
        }

        # Mock interface with node resolution data (but will be ignored due to no_resolve)
        mock_interface = MockInterface(
            {
                "!a1b2c315": {
                    "user": {"longName": "NH Node"}
                },  # ends with 15 to match nextHop 0x15
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # With no_resolve=True, should show only hex byte without name resolution
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 NH:0x15 from:!a1b2c3d4 to:!e5f6a7b8 Text: Directed hop"
        result = capture._format_packet(packet, mock_interface, True)  # no_resolve=True
        assert result == with_suffix_if_portnum(packet, expected)

    def test_next_hop_absent_or_zero_hidden(self):
        """Test that when nextHop is absent or zero, NH: field is not displayed."""
        # Case A: No nextHop key at all
        packet_no_key = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            # Note: no nextHop key
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "No next hop"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Should NOT contain " NH:" substring
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: No next hop"
        result = capture._format_packet(packet_no_key, mock_interface, False)
        assert result == with_suffix_if_portnum(packet_no_key, expected)
        assert " NH:" not in result

        # Case B: nextHop is 0
        packet_zero = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "nextHop": 0,  # Zero value
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Zero next hop"},
        }

        # Should NOT contain " NH:" substring
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Zero next hop"
        result = capture._format_packet(packet_zero, mock_interface, False)
        assert result == with_suffix_if_portnum(packet_zero, expected)
        assert " NH:" not in result

    def test_next_hop_snake_case_key(self):
        """Test that when next_hop (snake_case) is present, it shows NH:<label> after Hop:<N>."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "next_hop": 0x15,  # Snake case instead of camelCase
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Directed hop"},
        }

        # Mock interface with node resolution data
        mock_interface = MockInterface(
            {
                "!a1b2c315": {
                    "user": {"longName": "NH Node"}
                },  # ends with 15 to match nextHop 0x15
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Expected format includes NH: field between Hop:3 and from:
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 NH:NH Node (!a1b2c315) from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Directed hop"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_next_hop_no_matching_node(self):
        """Test that when no node matches the nextHop last byte, show raw hex."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "nextHop": 0x42,  # No node ends with 42
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "No matching node"},
        }

        # Mock interface with nodes that don't match nextHop 0x42
        mock_interface = MockInterface(
            {
                "!a1b2c315": {"user": {"longName": "Node 15"}},  # ends with 15, not 42
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Should show raw hex since no node matches
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 NH:0x42 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: No matching node"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)

    def test_next_hop_multiple_matching_nodes(self):
        """Test that when multiple nodes match the nextHop last byte, show raw hex."""
        packet = {
            "rxTime": 1697731200,  # 2023-10-19 16:00:00 UTC
            "channel": 5,
            "rxRssi": -85,
            "rxSnr": 12.5,
            "hopLimit": 3,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6a7b8",
            "nextHop": 0x15,  # Multiple nodes end with 15
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Multiple matches"},
        }

        # Mock interface with multiple nodes ending with 15
        mock_interface = MockInterface(
            {
                "!a1b2c315": {"user": {"longName": "Node A"}},  # ends with 15
                "!b1b2c315": {"user": {"longName": "Node B"}},  # also ends with 15
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6a7b8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        capture = MeshCap(mock_args)

        # Should show raw hex since multiple nodes match
        ts = local_ts_str(1697731200)
        expected = f"[{ts}] Ch:5 -85dBm/12.5dB Hop:3 NH:0x15 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6a7b8) Text: Multiple matches"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == with_suffix_if_portnum(packet, expected)
