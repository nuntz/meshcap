import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import meshcap.main


class TestPacketSubscription(unittest.TestCase):
    
    @patch('meshcap.main.pub')
    @patch('meshtastic.serial_interface.SerialInterface')
    @patch('sys.argv', ['meshcap', '--test-mode'])
    def test_packet_subscription_and_reception(self, mock_serial_interface, mock_pub):
        """Test that meshcap properly subscribes to packet events and receives packets."""
        # Setup mocks
        mock_interface = MagicMock()
        mock_serial_interface.return_value = mock_interface
        
        # Call main function
        meshcap.main.main()
        
        # Verify that pub.subscribe was called with the correct topic
        mock_pub.subscribe.assert_called_once()
        
        # Get the callback function that was passed to subscribe using call_args
        callback_func, topic = mock_pub.subscribe.call_args[0]
        
        # Verify the topic is correct
        self.assertEqual(topic, "meshtastic.receive")
        
        # Create a sample packet to test with
        sample_packet = {
            'fromId': '!12345678',
            'toId': '!87654321',
            'rxTime': 1640995200,
            'channel': 0,
            'rxRssi': -80,
            'rxSnr': 5.5,
            'decoded': {
                'portnum': 'TEXT_MESSAGE_APP',
                'text': 'Hello World'
            }
        }
        
        # Mock print to capture output instead of relying on the old global function
        with patch('builtins.print') as mock_print:
            # Simulate the meshtastic library calling our callback with packet and interface
            callback_func(packet=sample_packet, interface=mock_interface)
            
            # Verify that print was called (indicating the packet was processed)
            mock_print.assert_called()


if __name__ == '__main__':
    unittest.main()