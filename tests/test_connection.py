from unittest.mock import patch, Mock
import pytest
from meshcap.main import MeshCap


def test_connect_to_device_success(capsys):
    """Test successful connection to device."""
    mock_args = Mock()
    mock_interface = Mock()
    capture = MeshCap(mock_args)
    
    with patch('meshtastic.serial_interface.SerialInterface', return_value=mock_interface):
        result = capture._connect_to_device('/dev/ttyUSB0')
    
    assert result is mock_interface
    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyUSB0" in captured.out


def test_connect_to_device_failure():
    """Test connection failure with Exception."""
    mock_args = Mock()
    capture = MeshCap(mock_args)
    error_message = "Connection failed: Device not found"
    
    with patch('meshtastic.serial_interface.SerialInterface', side_effect=Exception(error_message)):
        with pytest.raises(SystemExit) as exc_info:
            capture._connect_to_device('/dev/ttyUSB0')
    
    assert exc_info.value.code == 1


def test_connect_to_device_failure_error_message(capsys):
    """Test that failure prints correct error message to stderr."""
    mock_args = Mock()
    capture = MeshCap(mock_args)
    error_message = "Connection failed: Device not found"
    
    with patch('meshtastic.serial_interface.SerialInterface', side_effect=Exception(error_message)):
        with pytest.raises(SystemExit):
            capture._connect_to_device('/dev/ttyUSB0')
    
    captured = capsys.readouterr()
    assert f"Error: Connection to device failed: {error_message}" in captured.err