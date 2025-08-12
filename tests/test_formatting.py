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
            'rxTime': 1697731200,  # 2023-10-19 16:00:00 UTC
            'channel': 5,
            'rxRssi': -85,
            'rxSnr': 12.5,
            'fromId': '!a1b2c3d4',
            'toId': '!e5f6g7h8',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello World!'
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:5 -85dBm/12.5dB !a1b2c3d4→!e5f6g7h8 Text: Hello World!"
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_position_packet(self):
        """Test formatting a position packet."""
        packet = {
            'rxTime': 1697731200,
            'channel': 2,
            'rxRssi': -92,
            'rxSnr': 8.0,
            'fromId': '!12345678',
            'toId': '!87654321',
            'decoded': {
                'portnum': 'POSITION_APP',
                'position': {
                    'latitude': 37.7749,
                    'longitude': -122.4194
                }
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -92dBm/8.0dB !12345678→!87654321 Position: lat=37.7749, lon=-122.4194"
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_encrypted_packet(self):
        """Test formatting an encrypted packet."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -78,
            'rxSnr': 15.2,
            'fromId': '!aaaabbbb',
            'toId': '!ccccdddd',
            'encrypted': b'some encrypted data here'
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -78dBm/15.2dB !aaaabbbb→!ccccdddd Encrypted: length=24"
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_encrypted_packet_no_decoded(self):
        """Test formatting a packet with no decoded field."""
        packet = {
            'rxTime': 1697731200,
            'channel': 3,
            'rxRssi': -95,
            'rxSnr': 5.5,
            'fromId': '!11111111',
            'toId': '!22222222',
            'encrypted': b'encrypted'
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:3 -95dBm/5.5dB !11111111→!22222222 Encrypted: length=9"
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_other_portnum_packet(self):
        """Test formatting a packet with an unknown portnum."""
        packet = {
            'rxTime': 1697731200,
            'channel': 4,
            'rxRssi': -88,
            'rxSnr': 10.0,
            'fromId': '!abcd1234',
            'toId': '!5678efgh',
            'decoded': {
                'portnum': 'UNKNOWN_APP',
                'data': {'some': 'data'}
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:4 -88dBm/10.0dB !abcd1234→!5678efgh UNKNOWN_APP: [UNKNOWN_APP]"
        assert capture._format_packet(packet, MockInterface(), False) == expected

    def test_other_portnum_packet_verbose(self):
        """Test formatting a packet with an unknown portnum in verbose mode."""
        packet = {
            'rxTime': 1697731200,
            'channel': 4,
            'rxRssi': -88,
            'rxSnr': 10.0,
            'fromId': '!abcd1234',
            'toId': '!5678efgh',
            'decoded': {
                'portnum': 'UNKNOWN_APP',
                'data': {'some': 'data'}
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:4 -88dBm/10.0dB !abcd1234→!5678efgh UNKNOWN_APP: {'portnum': 'UNKNOWN_APP', 'data': {'some': 'data'}}"
        assert capture._format_packet(packet, MockInterface(), False, verbose=True) == expected
    
    def test_missing_fields_defaults(self):
        """Test formatting a packet with missing fields using defaults."""
        packet = {}
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[1970-01-01 00:00:00] Ch:0 0dBm/0dB unknown→unknown Encrypted: length=0"
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_empty_text_message(self):
        """Test formatting a text message packet with empty text."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -80,
            'rxSnr': 12.0,
            'fromId': '!test1234',
            'toId': '!dest5678',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': ''
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -80dBm/12.0dB !test1234→!dest5678 Text: "
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_position_packet_missing_coordinates(self):
        """Test formatting a position packet with missing coordinates."""
        packet = {
            'rxTime': 1697731200,
            'channel': 2,
            'rxRssi': -90,
            'rxSnr': 7.5,
            'fromId': '!pos12345',
            'toId': '!target678',
            'decoded': {
                'portnum': 'POSITION_APP',
                'position': {}
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:2 -90dBm/7.5dB !pos12345→!target678 Position: lat=0, lon=0"
        assert capture._format_packet(packet, MockInterface(), False) == expected
    
    def test_decoded_with_empty_portnum(self):
        """Test formatting a packet with decoded field but empty portnum."""
        packet = {
            'rxTime': 1697731200,
            'channel': 3,
            'rxRssi': -85,
            'rxSnr': 9.0,
            'fromId': '!empty1234',
            'toId': '!empty5678',
            'decoded': {},
            'encrypted': b'test'
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:3 -85dBm/9.0dB !empty1234→!empty5678 Encrypted: length=4"
        assert capture._format_packet(packet, MockInterface(), False) == expected


class TestNodeResolution:
    """Test cases for node name resolution functionality."""
    
    def test_node_resolution_known_ids(self):
        """Test that known fromId is correctly resolved to its longName."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -85,
            'rxSnr': 12.0,
            'fromId': '!a1b2c3d4',
            'toId': '!e5f6g7h8',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello!'
            }
        }
        
        mock_interface = MockInterface({
            '!a1b2c3d4': {
                'user': {
                    'longName': 'Alice Node'
                }
            },
            '!e5f6g7h8': {
                'user': {
                    'longName': 'Bob Node'
                }
            }
        })
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Alice Node→Bob Node Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == expected
    
    def test_node_resolution_unknown_to_id_fallback(self):
        """Test that an unknown toId correctly falls back to its raw ID."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -85,
            'rxSnr': 12.0,
            'fromId': '!a1b2c3d4',
            'toId': '!unknown123',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello!'
            }
        }
        
        mock_interface = MockInterface({
            '!a1b2c3d4': {
                'user': {
                    'longName': 'Alice Node'
                }
            }
        })
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB Alice Node→!unknown123 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == expected
    
    def test_node_resolution_disabled(self):
        """Test that when no_resolve is True, no name resolution occurs."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -85,
            'rxSnr': 12.0,
            'fromId': '!a1b2c3d4',
            'toId': '!e5f6g7h8',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello!'
            }
        }
        
        mock_interface = MockInterface({
            '!a1b2c3d4': {
                'user': {
                    'longName': 'Alice Node'
                }
            },
            '!e5f6g7h8': {
                'user': {
                    'longName': 'Bob Node'
                }
            }
        })
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB !a1b2c3d4→!e5f6g7h8 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, True) == expected
    
    def test_node_resolution_no_interface(self):
        """Test that no resolution occurs when interface is None."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -85,
            'rxSnr': 12.0,
            'fromId': '!a1b2c3d4',
            'toId': '!e5f6g7h8',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello!'
            }
        }
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB !a1b2c3d4→!e5f6g7h8 Text: Hello!"
        assert capture._format_packet(packet, None, False) == expected
    
    def test_node_resolution_missing_user_data(self):
        """Test that nodes without proper user data fall back to raw IDs."""
        packet = {
            'rxTime': 1697731200,
            'channel': 1,
            'rxRssi': -85,
            'rxSnr': 12.0,
            'fromId': '!a1b2c3d4',
            'toId': '!e5f6g7h8',
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello!'
            }
        }
        
        mock_interface = MockInterface({
            '!a1b2c3d4': {
                'user': {}  # Missing longName
            },
            '!e5f6g7h8': {}  # Missing user entirely
        })
        
        mock_args = Mock()
        capture = MeshCap(mock_args)
        expected = "[2023-10-19 16:00:00] Ch:1 -85dBm/12.0dB !a1b2c3d4→!e5f6g7h8 Text: Hello!"
        assert capture._format_packet(packet, mock_interface, False) == expected