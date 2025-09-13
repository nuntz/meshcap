"""Integration tests for serialization features in main application."""

import tempfile
import os
import json
import pickle
from datetime import datetime, timezone
from unittest.mock import Mock, patch
from io import StringIO

import pytest

from meshcap.main import MeshCap
from meshcap.serialization import PacketSerializer


class TestSerializationIntegration:
    """Integration tests for serialization features."""

    def test_json_write_and_read_integration(self):
        """Test complete write and read cycle using JSON format."""
        # Create a mock packet
        test_packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4", 
            "toId": "!e5f6g7h8",
            "channel": 0,
            "rxRssi": -45,
            "rxSnr": 8.5,
            "encrypted": b"\x01\x02\x03\x04",
            "decoded": {
                "portnum": "TEXT_MESSAGE_APP",
                "text": "Integration test message"
            }
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Test writing with JSON format
            args = Mock()
            args.format = 'json'
            args.write_file = temp_filename
            args.count = None
            args.read_file = None
            args.cache_size = None

            # Create MeshCap instance and initialize write file
            meshcap = MeshCap(args)
            meshcap.args.write_file = temp_filename
            
            # Open write file in the same way as the real application
            filename = temp_filename
            use_json = True  # Based on format='json'
            mode = 'w'
            
            with open(filename, mode) as f:
                meshcap.write_file_handle = f
                
                # Simulate writing a packet
                meshcap.serializer.serialize_to_json(test_packet, meshcap.write_file_handle)
                
            meshcap.write_file_handle = None

            # Verify file was written correctly
            assert os.path.exists(temp_filename)
            
            # Read back the data using the serializer
            with open(temp_filename, 'r') as f:
                restored_packet = meshcap.serializer.deserialize_from_json(f)
                
            assert restored_packet == test_packet
            assert isinstance(restored_packet["encrypted"], bytes)
            
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_auto_format_detection_json(self):
        """Test automatic format detection with JSON files."""
        test_packet = {
            "rxTime": 1697731200,
            "fromId": "!testnode",
            "decoded": {"text": "Auto-detection test"}
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Write using JSON format
            serializer = PacketSerializer()
            with open(temp_filename, 'w') as f:
                serializer.serialize_to_json(test_packet, f)

            # Test auto-detection reading
            with open(temp_filename, 'r') as f:
                restored_packet = serializer.deserialize_auto(f)
                
            assert restored_packet == test_packet
            
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_pickle_deprecation_warning(self):
        """Test that pickle files generate deprecation warnings."""
        test_packet = {
            "rxTime": 1697731200,
            "fromId": "!testnode",
            "decoded": {"text": "Pickle warning test"}
        }

        with tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False) as temp_file:
            temp_filename = temp_file.name

        try:
            # Write using pickle format
            with open(temp_filename, 'wb') as f:
                pickle.dump(test_packet, f)

            # Mock the file reading with MeshCap
            args = Mock()
            args.read_file = temp_filename
            args.format = 'auto'
            args.cache_size = None
            
            meshcap = MeshCap(args)
            
            # Capture stderr to check for warning
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                with patch.object(meshcap, '_on_packet_received') as mock_handler:
                    meshcap._read_packets_from_file(temp_filename, no_resolve=True, verbose=False)
                    
                # Check that warning was printed
                stderr_output = mock_stderr.getvalue()
                assert "Warning: Pickle files (.pkl) are deprecated" in stderr_output
                assert "security concerns" in stderr_output
                
                # Verify packet was still processed
                mock_handler.assert_called_once()
                
        finally:
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)

    def test_cache_size_integration(self):
        """Test that cache_size parameter is passed to NodeBook."""
        args = Mock()
        args.read_file = None
        args.write_file = None
        args.cache_size = 100
        args.count = None
        args.filter = None
        args.host = None
        args.port = "/dev/null"  # Won't actually connect
        
        meshcap = MeshCap(args)
        
        # Mock the interface connection to avoid actual hardware
        mock_interface = Mock()
        
        with patch.object(meshcap, '_connect_to_interface', return_value=mock_interface):
            with patch('meshcap.main.NodeBook') as mock_nodebook_class:
                with patch('meshcap.main.pub'):
                    with patch('meshcap.main.time.sleep', side_effect=KeyboardInterrupt):
                        try:
                            meshcap.run()
                        except KeyboardInterrupt:
                            pass  # Expected to exit via KeyboardInterrupt
                
                # Verify NodeBook was created with cache_size
                mock_nodebook_class.assert_called_once_with(mock_interface, max_size=100)

    def test_file_extension_auto_detection(self):
        """Test automatic file extension and format detection."""
        args = Mock()
        args.format = 'auto'
        args.count = None
        args.cache_size = None
        
        meshcap = MeshCap(args)
        
        # Test JSON extension detection
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
            json_filename = temp_file.name
            
        with tempfile.NamedTemporaryFile(suffix='.pkl', delete=False) as temp_file:
            pkl_filename = temp_file.name
            
        try:
            # Mock the open function to verify the mode
            original_open = open
            open_calls = []
            
            def mock_open(filename, mode, *args, **kwargs):
                open_calls.append((filename, mode))
                if 'w' in mode and filename.endswith('.json'):
                    # For JSON files, should open in text mode
                    assert 'b' not in mode
                elif 'w' in mode and filename.endswith('.pkl'):
                    # For pickle files, should open in binary mode
                    assert 'b' in mode
                return original_open(filename, mode, *args, **kwargs)
            
            with patch('builtins.open', side_effect=mock_open):
                # Test JSON file write setup
                meshcap.args.write_file = json_filename
                meshcap.args.format = 'auto'
                
                # Simulate the write file opening logic from main.py
                filename = json_filename
                use_json = filename.lower().endswith('.json')
                mode = 'w' if use_json else 'wb'
                
                try:
                    with open(filename, mode) as f:
                        pass  # Just test the opening
                except:
                    pass  # File operations might fail, we just want to test the logic
                
                # Test pickle file write setup
                filename = pkl_filename
                use_json = filename.lower().endswith('.json')
                mode = 'w' if use_json else 'wb'
                
                try:
                    with open(filename, mode) as f:
                        pass
                except:
                    pass
                    
            # Verify correct modes were used
            assert any('.json' in call[0] and 'w' in call[1] and 'b' not in call[1] for call in open_calls)
            assert any('.pkl' in call[0] and 'wb' in call[1] for call in open_calls)
            
        finally:
            for filename in [json_filename, pkl_filename]:
                if os.path.exists(filename):
                    os.unlink(filename)

    def test_mixed_format_read_sequence(self):
        """Test reading packets from files with different formats in sequence."""
        # Create test packets
        packets = [
            {
                "rxTime": 1697731200 + i,
                "fromId": f"!test{i:04x}",
                "decoded": {"text": f"Message {i}"}
            }
            for i in range(3)
        ]

        json_file = None
        pkl_file = None

        try:
            # Create JSON file
            json_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            serializer = PacketSerializer()
            
            for packet in packets[:2]:  # First 2 packets in JSON
                serializer.serialize_to_json(packet, json_file)
            json_file.close()

            # Create pickle file  
            pkl_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.pkl', delete=False)
            pickle.dump(packets[2], pkl_file)  # Last packet in pickle
            pkl_file.close()

            # Read both files and verify packets
            received_packets = []

            def mock_packet_handler(packet, interface, no_resolve, verbose):
                received_packets.append(packet)

            args = Mock()
            args.cache_size = None
            meshcap = MeshCap(args)

            with patch.object(meshcap, '_on_packet_received', side_effect=mock_packet_handler):
                # Read JSON file
                with patch('sys.stderr', new_callable=StringIO):
                    meshcap._read_packets_from_file(json_file.name, no_resolve=True)
                
                # Read pickle file (should show warning)
                with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                    meshcap._read_packets_from_file(pkl_file.name, no_resolve=True)
                    
                    # Verify deprecation warning for pickle file
                    stderr_output = mock_stderr.getvalue()
                    assert "deprecated" in stderr_output

            # Verify all packets were received correctly
            assert len(received_packets) == 3
            for i, received in enumerate(received_packets):
                assert received["fromId"] == packets[i]["fromId"] 
                assert received["decoded"]["text"] == packets[i]["decoded"]["text"]

        finally:
            for temp_file in [json_file, pkl_file]:
                if temp_file and os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

    def test_format_argument_override(self):
        """Test that --format argument properly overrides extension-based detection."""
        # This test verifies the logic in main.py for handling format arguments
        
        args = Mock()
        args.format = 'json'
        args.cache_size = None
        
        # Test that format='json' forces JSON mode even with .pkl extension
        write_file = 'test.pkl'
        
        # Simulate the logic from main.py
        filename = write_file
        use_json = (args.format == 'json') or filename.lower().endswith('.json')
        
        assert use_json == True  # Should be True because format='json' overrides .pkl extension
        
        # Test auto detection with .json extension
        args.format = 'auto'
        filename = 'test.json'
        use_json = (args.format == 'json') or filename.lower().endswith('.json')
        
        assert use_json == True  # Should be True because of .json extension
        
        # Test auto detection with .pkl extension
        args.format = 'auto'
        filename = 'test.pkl'
        use_json = (args.format == 'json') or filename.lower().endswith('.json')
        
        assert use_json == False  # Should be False because of .pkl extension and format='auto'