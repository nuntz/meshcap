import sys
from unittest.mock import patch, Mock
from meshcap.main import main


def test_default_port(capsys):
    """Test that parsing with no arguments results in the default port /dev/ttyACM0."""
    mock_interface = Mock()
    
    with patch.object(sys, 'argv', ['meshcap', '--test-mode']), \
         patch('meshtastic.serial_interface.SerialInterface', return_value=mock_interface):
        main()
    
    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyACM0" in captured.out


def test_custom_port_long_form(capsys):
    """Test that providing --port /dev/ttyUSB0 correctly sets the port."""
    mock_interface = Mock()
    
    with patch.object(sys, 'argv', ['meshcap', '--port', '/dev/ttyUSB0', '--test-mode']), \
         patch('meshtastic.serial_interface.SerialInterface', return_value=mock_interface):
        main()
    
    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyUSB0" in captured.out


def test_custom_port_short_form(capsys):
    """Test that providing -p /dev/ttyUSB0 correctly sets the port."""
    mock_interface = Mock()
    
    with patch.object(sys, 'argv', ['meshcap', '-p', '/dev/ttyUSB0', '--test-mode']), \
         patch('meshtastic.serial_interface.SerialInterface', return_value=mock_interface):
        main()
    
    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyUSB0" in captured.out