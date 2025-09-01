from unittest.mock import Mock
from meshcap.main import MeshCap


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
            "toId": "!e5f6g7h8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:5 -85dBm/12.5dB Hop:0 from:!a1b2c3d4 to:!e5f6g7h8 Text: Hello World!"
        assert capture._format_packet(packet, MockInterface(), False) == expected

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
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -92dBm/8.0dB Hop:0 from:!12345678 to:!87654321 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, MockInterface(), False) == expected

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
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -78dBm/15.2dB Hop:0 from:!aaaabbbb to:!ccccdddd Encrypted: length=24"
        assert capture._format_packet(packet, MockInterface(), False) == expected

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
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:3 -95dBm/5.5dB Hop:0 from:!11111111 to:!22222222 Encrypted: length=9"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_other_portnum_packet(self):
        """Test formatting a packet with an unknown portnum."""
        packet = {
            "rxTime": 1697731200,
            "channel": 4,
            "rxRssi": -88,
            "rxSnr": 10.0,
            "fromId": "!abcd1234",
            "toId": "!5678efgh",
            "decoded": {"portnum": "UNKNOWN_APP", "data": {"some": "data"}},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:4 -88dBm/10.0dB Hop:0 from:!abcd1234 to:!5678efgh UNKNOWN_APP: [UNKNOWN_APP]"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_other_portnum_packet_verbose(self):
        """Test formatting a packet with an unknown portnum in verbose mode."""
        packet = {
            "rxTime": 1697731200,
            "channel": 4,
            "rxRssi": -88,
            "rxSnr": 10.0,
            "fromId": "!abcd1234",
            "toId": "!5678efgh",
            "decoded": {"portnum": "UNKNOWN_APP", "data": {"some": "data"}},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:4 -88dBm/10.0dB Hop:0 from:!abcd1234 to:!5678efgh UNKNOWN_APP: {'portnum': 'UNKNOWN_APP', 'data': {'some': 'data'}}"
        assert (
            capture._format_packet(packet, MockInterface(), False, verbose=True)
            == expected
        )

    def test_missing_fields_defaults(self):
        """Test formatting a packet with missing fields using defaults."""
        packet = {}

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[1970-01-01 00:00:00] Ch:0 0dBm/0dB Hop:0 from:unknown to:unknown Encrypted: length=0"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_empty_text_message(self):
        """Test formatting a text message packet with empty text."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -80,
            "rxSnr": 12.0,
            "fromId": "!test1234",
            "toId": "!dest5678",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": ""},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -80dBm/12.0dB Hop:0 from:!test1234 to:!dest5678 Text: "
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_position_packet_missing_coordinates(self):
        """Test formatting a position packet with missing coordinates."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 7.5,
            "fromId": "!pos12345",
            "toId": "!target678",
            "decoded": {"portnum": "POSITION_APP", "position": {}},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -90dBm/7.5dB Hop:0 from:!pos12345 to:!target678 Position: lat=0, lon=0"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_decoded_with_empty_portnum(self):
        """Test formatting a packet with decoded field but empty portnum."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -85,
            "rxSnr": 9.0,
            "fromId": "!empty1234",
            "toId": "!empty5678",
            "decoded": {},
            "encrypted": b"test",
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:3 -85dBm/9.0dB Hop:0 from:!empty1234 to:!empty5678 Encrypted: length=4"
        assert capture._format_packet(packet, MockInterface(), False) == expected


class TestResolveNodeInfo:
    """Test cases for the _resolve_node_info method."""

    def test_resolve_node_info_with_string_id(self):
        """Test _resolve_node_info with string node ID that can be resolved."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, "!a1b2c3d4", "from")
        expected = {"label": "from", "value": "Alice Node (!a1b2c3d4)"}
        assert result == expected

    def test_resolve_node_info_with_integer_id(self):
        """Test _resolve_node_info with integer node ID that can be resolved."""
        mock_interface = MockInterface(
            {
                "!075bcd15": {  # hex representation of 123456789
                    "user": {"longName": "Bob Node"}
                }
            }
        )

        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, 123456789, "to")
        expected = {
            "label": "to",
            "value": "Bob Node (123456789)",
            "node_number": 123456789,
        }
        assert result == expected

    def test_resolve_node_info_unresolvable_string(self):
        """Test _resolve_node_info with string node ID that cannot be resolved."""
        mock_interface = MockInterface({})  # Empty nodes dict

        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, "!unknown123", "source")
        expected = {"label": "source", "value": "!unknown123"}
        assert result == expected

    def test_resolve_node_info_unresolvable_integer(self):
        """Test _resolve_node_info with integer node ID that cannot be resolved."""
        mock_interface = MockInterface({})  # Empty nodes dict

        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, 987654321, "dest")
        expected = {
            "label": "dest",
            "value": "987654321",
        }  # node number representation
        assert result == expected

    def test_resolve_node_info_no_resolve_flag(self):
        """Test _resolve_node_info with no_resolve flag set to True."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        mock_args.no_resolve = True
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, "!a1b2c3d4", "from")
        expected = {"label": "from", "value": "!a1b2c3d4"}
        assert result == expected

    def test_resolve_node_info_no_interface(self):
        """Test _resolve_node_info with None interface."""
        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(None, "!a1b2c3d4", "from")
        expected = {"label": "from", "value": "!a1b2c3d4"}
        assert result == expected

    def test_resolve_node_info_missing_user_data(self):
        """Test _resolve_node_info with node missing user data."""
        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {}  # Missing user data
            }
        )

        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, "!a1b2c3d4", "from")
        expected = {"label": "from", "value": "!a1b2c3d4"}
        assert result == expected

    def test_resolve_node_info_missing_longname(self):
        """Test _resolve_node_info with node missing longName."""
        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {
                    "user": {}  # Missing longName
                }
            }
        )

        mock_args = Mock()
        mock_args.no_resolve = False
        capture = MeshCap(mock_args)

        result = capture._resolve_node_info(mock_interface, "!a1b2c3d4", "from")
        expected = {"label": "from", "value": "!a1b2c3d4"}
        assert result == expected


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
            "toId": "!e5f6g7h8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6g7h8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6g7h8) Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_node_resolution_unknown_to_id_fallback(self):
        """Test that an unknown toId correctly falls back to its raw ID."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!unknown123",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!a1b2c3d4) to:!unknown123 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_node_resolution_disabled(self):
        """Test that when no_resolve is True, no name resolution occurs."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6g7h8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6g7h8 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, True) == expected

    def test_node_resolution_no_interface(self):
        """Test that no resolution occurs when interface is None."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6g7h8 Text: Hello!"
        assert capture._format_packet(packet, None, False) == expected

    def test_node_resolution_missing_user_data(self):
        """Test that nodes without proper user data fall back to raw IDs."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {
                    "user": {}  # Missing longName
                },
                "!e5f6g7h8": {},  # Missing user entirely
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6g7h8 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == expected


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
            "toId": "!e5f6g7h8",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        mock_interface = MockInterface(
            {
                "!a1b2c3d4": {"user": {"longName": "Alice Node"}},
                "!e5f6g7h8": {"user": {"longName": "Bob Node"}},
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!a1b2c3d4) to:Bob Node (!e5f6g7h8) Text: Hello World!"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_new_format_with_unresolved_names(self):
        """Test that unresolved node IDs fall back to raw IDs in the new format."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!known1234",
            "toId": "!unknown567",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Testing unresolved"},
        }

        # Mock interface only has one of the two nodes
        mock_interface = MockInterface(
            {
                "!known1234": {"user": {"longName": "Known User"}}
                # '!unknown567' is not in the nodes list
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -90dBm/8.5dB Hop:0 from:Known User (!known1234) to:!unknown567 Text: Testing unresolved"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_new_format_with_no_resolve_flag(self):
        """Test that --no-resolve flag shows only raw IDs in the new format."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -88,
            "rxSnr": 10.2,
            "fromId": "!user12345",
            "toId": "!user67890",
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 40.7128, "longitude": -74.0060},
            },
        }

        # Mock interface has both nodes available for resolution
        mock_interface = MockInterface(
            {
                "!user12345": {"user": {"longName": "First User"}},
                "!user67890": {"user": {"longName": "Second User"}},
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        # With no_resolve=True, should only show raw IDs despite having resolvable names
        expected = "[2023-10-19 16:00:00] Ch:3 -88dBm/10.2dB Hop:0 from:!user12345 to:!user67890 Position: lat=40.7128, lon=-74.006"
        assert capture._format_packet(packet, mock_interface, True) == expected

    def test_format_packet_with_from_and_to(self):
        """Test formatting a packet that includes from and to integer fields."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -85,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "from": 123456789,
            "to": 987654321,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello with from/to!"},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:!a1b2c3d4 to:!e5f6g7h8 hop_from:123456789 hop_to:987654321 Text: Hello with from/to!"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_format_packet_with_source_and_dest(self):
        """Test formatting a packet that includes source and dest in decoded payload."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
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
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -90dBm/8.5dB Hop:0 from:!a1b2c3d4 to:!e5f6g7h8 hop_from:111111111 hop_to:222222222 source:333333333 dest:444444444 Text: Message with routing info"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_format_packet_without_source_and_dest(self):
        """Test formatting a packet without source and dest fields (should default to unknown)."""
        packet = {
            "rxTime": 1697731200,
            "channel": 3,
            "rxRssi": -85,
            "rxSnr": 10.0,
            "fromId": "!test1234",
            "toId": "!dest5678",
            "from": 555555555,
            "to": 666666666,
            "decoded": {
                "portnum": "POSITION_APP",
                "position": {"latitude": 37.7749, "longitude": -122.4194},
                # Note: no source or dest fields in decoded
            },
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:3 -85dBm/10.0dB Hop:0 from:!test1234 to:!dest5678 hop_from:555555555 hop_to:666666666 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, MockInterface(), False) == expected

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
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 from:Alice Node (!aaaaaaaa) to:Bob Node (!bbbbbbbb) source:Charlie Node (3435973836) dest:Delta Node (3722304989) Text: Full routing example"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_format_packet_mixed_resolvable_unresolvable(self):
        """Test formatting a packet with only some address fields resolvable."""
        packet = {
            "rxTime": 1697731200,
            "channel": 2,
            "rxRssi": -90,
            "rxSnr": 8.5,
            "fromId": "!known123",
            "toId": "!unknown99",
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
                "!known123": {"user": {"longName": "Known User"}}
                # Note: other nodes should not resolve
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -90dBm/8.5dB Hop:0 from:Known User (!known123) to:!unknown99 hop_from:1111111111 hop_to:2222222222 source:3333333333 dest:4444444444 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_format_packet_only_fromid_toid(self):
        """Test formatting a packet with only fromId and toId (backward compatibility)."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -80,
            "rxSnr": 15.0,
            "fromId": "!oldnode1",
            "toId": "!oldnode2",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Simple message"},
        }

        mock_interface = MockInterface(
            {
                "!oldnode1": {"user": {"longName": "Old Sender"}},
                "!oldnode2": {"user": {"longName": "Old Receiver"}},
            }
        )

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -80dBm/15.0dB Hop:0 from:Old Sender (!oldnode1) to:Old Receiver (!oldnode2) Text: Simple message"
        assert capture._format_packet(packet, mock_interface, False) == expected

    def test_format_encrypted_packet_comprehensive(self):
        """Test formatting an encrypted packet without decoded section."""
        packet = {
            "rxTime": 1697731200,
            "channel": 4,
            "rxRssi": -95,
            "rxSnr": 3.2,
            "fromId": "!encrypted1",
            "toId": "!encrypted2",
            "encrypted": b"this is some encrypted binary data here",
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:4 -95dBm/3.2dB Hop:0 from:!encrypted1 to:!encrypted2 Encrypted: length=39"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_format_packet_with_hop_limit(self):
        """Test formatting a packet with hop_limit field."""
        packet = {
            "rxTime": 1697731200,
            "channel": 1,
            "rxRssi": -80,
            "rxSnr": 12.0,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "hopLimit": 3,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello World!"},
        }

        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -80dBm/12.0dB Hop:3 from:!a1b2c3d4 to:!e5f6g7h8 Text: Hello World!"
        assert capture._format_packet(packet, MockInterface(), False) == expected

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
        capture = MeshCap(mock_args)

        # Expected: node numbers should be displayed directly (123456789, 987654321)
        # instead of hex format (!075bcd15, !3ade68b1)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Hop:0 hop_from:123456789 hop_to:987654321 Text: Hello World!"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == expected

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
        capture = MeshCap(mock_args)

        # Expected: should fall back to node ID since no node number is available
        expected = "[2023-10-19 16:00:00] Ch:2 -90dBm/8.5dB Hop:0 from:Old Node (!deadbeef) Text: From old capture"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == expected

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
        capture = MeshCap(mock_args)

        # Expected: resolved name with node ID fallback for first, raw node ID for second
        expected = "[2023-10-19 16:00:00] Ch:3 -85dBm/10.0dB Hop:0 from:Known Old Node (!abc12345) to:!def67890 Position: lat=40.0, lon=-74.0"
        result = capture._format_packet(packet, mock_interface, False)
        assert result == expected


class TestFormatNodeLabel:
    """Test cases for the format_node_label method."""

    def test_format_node_label_no_resolve(self):
        """Test format_node_label with no_resolve=True returns user_id."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )
        
        mock_args = Mock()
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
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="hex-only")
        assert result == "!a1b2c3d4"

    def test_format_node_label_named_only_mode_with_long_name(self):
        """Test format_node_label with named-only mode returns best name."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-only")
        assert result == "Alice Node"

    def test_format_node_label_named_only_mode_no_name_fallback(self):
        """Test format_node_label with named-only mode falls back to user_id when no name available."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {}}  # No user data
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-only")
        assert result == "!a1b2c3d4"

    def test_format_node_label_named_with_hex_mode_with_long_name(self):
        """Test format_node_label with named-with-hex mode returns name and hex."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-with-hex")
        assert result == "Alice Node(!a1b2c3d4)"

    def test_format_node_label_named_with_hex_mode_no_name_fallback(self):
        """Test format_node_label with named-with-hex mode falls back to user_id when no name available."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {}}  # No user data
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-with-hex")
        assert result == "!a1b2c3d4"

    def test_format_node_label_with_short_name_priority(self):
        """Test format_node_label prefers shortName over longName."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Long Node Name", "shortName": "Alice"}}}
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-only")
        assert result == "Alice"
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-with-hex")
        assert result == "Alice(!a1b2c3d4)"

    def test_format_node_label_with_empty_short_name(self):
        """Test format_node_label handles empty/whitespace shortName correctly."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node", "shortName": "   "}}}
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="named-only")
        assert result == "Alice Node"  # Falls back to longName since shortName is whitespace

    def test_format_node_label_integer_node_input(self):
        """Test format_node_label handles integer node input correctly."""
        mock_interface = MockInterface(
            {"!075bcd15": {"user": {"longName": "Node 123456789"}}}
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, 123456789, label_mode="named-with-hex")
        assert result == "Node 123456789(!075bcd15)"

    def test_format_node_label_no_interface(self):
        """Test format_node_label handles None interface correctly."""
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(None, "!a1b2c3d4", label_mode="named-with-hex")
        assert result == "!a1b2c3d4"  # Falls back to user_id

    def test_format_node_label_invalid_mode(self):
        """Test format_node_label raises ValueError for invalid label_mode."""
        mock_interface = MockInterface({})
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        try:
            capture.format_node_label(mock_interface, "!a1b2c3d4", label_mode="invalid-mode")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "Unknown label_mode: invalid-mode" in str(e)

    def test_format_node_label_default_mode(self):
        """Test format_node_label uses named-with-hex as default mode."""
        mock_interface = MockInterface(
            {"!a1b2c3d4": {"user": {"longName": "Alice Node"}}}
        )
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        
        result = capture.format_node_label(mock_interface, "!a1b2c3d4")
        assert result == "Alice Node(!a1b2c3d4)"
