import unittest
import threading
import time
from unittest.mock import patch, MagicMock, mock_open
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from meshcap.main import MeshCap


class TestThreadSafety(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures."""
        # Create mock args
        self.mock_args = MagicMock()
        self.mock_args.count = None
        self.mock_args.write_file = None
        self.mock_args.label_mode = "named-with-hex"
        self.mock_args.no_resolve = False
        
    def test_concurrent_packet_reception(self):
        """Test that concurrent packet reception is thread-safe."""
        capture = MeshCap(self.mock_args)
        
        # Create a sample packet for testing
        sample_packet = {
            "fromId": "!12345678",
            "toId": "!87654321", 
            "rxTime": 1640995200,
            "channel": 0,
            "rxRssi": -80,
            "rxSnr": 5.5,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Test message"},
        }
        
        # Number of concurrent threads and packets per thread
        num_threads = 10
        packets_per_thread = 50
        expected_total = num_threads * packets_per_thread
        
        def send_packets():
            """Send packets from this thread."""
            for _ in range(packets_per_thread):
                with patch("builtins.print"):  # Suppress output during test
                    capture._on_packet_received(sample_packet, None)
        
        # Create and start threads
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=send_packets)
            threads.append(thread)
            
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
            
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
            
        # Verify that all packets were counted correctly
        self.assertEqual(capture.packet_count, expected_total,
                        f"Expected {expected_total} packets, got {capture.packet_count}")
        
    def test_concurrent_file_writing(self):
        """Test that concurrent file writing is thread-safe."""
        # Mock file operations
        mock_file = MagicMock()
        
        with patch("builtins.open", mock_open()) as mock_file_open:
            mock_file_open.return_value = mock_file
            
            self.mock_args.write_file = "test.pkl"
            capture = MeshCap(self.mock_args)
            
            # Manually set the file handle (simulating opened file)
            capture.write_file_handle = mock_file
            
            sample_packet = {
                "fromId": "!12345678",
                "toId": "!87654321",
                "rxTime": 1640995200,
                "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Test"},
            }
            
            num_threads = 5
            packets_per_thread = 20
            
            def write_packets():
                """Write packets from this thread."""
                for _ in range(packets_per_thread):
                    with patch("builtins.print"), patch("pickle.dump"):
                        capture._on_packet_received(sample_packet, None)
                        
            # Create and start threads
            threads = []
            for _ in range(num_threads):
                thread = threading.Thread(target=write_packets)
                threads.append(thread)
                
            for thread in threads:
                thread.start()
                
            for thread in threads:
                thread.join()
                
            # Verify all packets were processed
            expected_total = num_threads * packets_per_thread
            self.assertEqual(capture.packet_count, expected_total)
            
    def test_clean_shutdown_with_pending_packets(self):
        """Test clean shutdown behavior when packets are still being processed."""
        self.mock_args.count = 10  # Set target count for shutdown
        capture = MeshCap(self.mock_args)
        
        sample_packet = {
            "fromId": "!12345678", 
            "toId": "!87654321",
            "rxTime": 1640995200,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Test"},
        }
        
        packets_processed_after_shutdown = 0
        
        def slow_packet_processor():
            """Process packets with delay to simulate real processing time."""
            nonlocal packets_processed_after_shutdown
            for i in range(15):  # Send more than target count
                with patch("builtins.print"):
                    capture._on_packet_received(sample_packet, None)
                    
                # Check if shutdown was triggered after target reached
                if capture.should_exit and i >= 10:
                    packets_processed_after_shutdown += 1
                    
                # Small delay to allow race conditions
                time.sleep(0.001)
                
        thread = threading.Thread(target=slow_packet_processor)
        thread.start()
        thread.join()
        
        # Verify shutdown was triggered at correct count
        self.assertTrue(capture.should_exit, "Shutdown should have been triggered")
        self.assertGreaterEqual(capture.packet_count, 10, "Should have processed at least target count")
        
    def test_file_handle_cleanup_thread_safety(self):
        """Test that file handle cleanup is thread-safe."""
        mock_file = MagicMock()
        
        self.mock_args.count = 5
        capture = MeshCap(self.mock_args)
        capture.write_file_handle = mock_file
        
        sample_packet = {
            "fromId": "!12345678",
            "toId": "!87654321", 
            "rxTime": 1640995200,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Test"},
        }
        
        def process_packets():
            """Process packets until shutdown."""
            for _ in range(10):
                with patch("builtins.print"), patch("pickle.dump"):
                    capture._on_packet_received(sample_packet, None)
                    if capture.should_exit:
                        break
                        
        # Start packet processing thread
        thread = threading.Thread(target=process_packets)
        thread.start()
        thread.join()
        
        # Verify file was closed and handle was cleared
        mock_file.close.assert_called_once()
        self.assertIsNone(capture.write_file_handle)
        
    def test_lock_prevents_race_conditions(self):
        """Test that locks prevent race conditions in shared state updates."""
        capture = MeshCap(self.mock_args)
        
        sample_packet = {
            "fromId": "!12345678",
            "toId": "!87654321",
            "rxTime": 1640995200, 
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Test"},
        }
        
        num_threads = 10
        packets_per_thread = 20
        expected_total = num_threads * packets_per_thread
        
        # Test with rapid concurrent access
        def send_packets():
            """Send packets from this thread rapidly."""
            for _ in range(packets_per_thread):
                with patch("builtins.print"):
                    capture._on_packet_received(sample_packet, None)
                    
        threads = []
        for _ in range(num_threads):
            thread = threading.Thread(target=send_packets)
            threads.append(thread)
            
        # Start all threads as close to simultaneously as possible
        for thread in threads:
            thread.start()
            
        for thread in threads:
            thread.join()
            
        # Verify final count is exactly correct (no lost updates or race conditions)
        self.assertEqual(capture.packet_count, expected_total,
                        f"Expected exactly {expected_total} packets, got {capture.packet_count}. "
                        "This indicates a race condition in packet counting.")
        
        # Additional verification: packet_count should never exceed the expected total
        # If there were race conditions, we might see duplicate increments
        self.assertLessEqual(capture.packet_count, expected_total,
                           "Packet count exceeded expected total, indicating race condition")


if __name__ == "__main__":
    unittest.main()