from unittest.mock import patch, Mock
import pytest
from meshcap.main import MeshCap


def test_connect_to_interface_serial_success(capsys):
    """Test successful connection to device via serial interface."""
    mock_args = Mock()
    mock_args.host = None
    mock_args.port = "/dev/ttyUSB0"
    mock_interface = Mock()
    capture = MeshCap(mock_args)

    with patch(
        "meshtastic.serial_interface.SerialInterface", return_value=mock_interface
    ):
        result = capture._connect_to_interface()

    assert result is mock_interface
    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyUSB0" in captured.out


def test_connect_to_interface_serial_failure():
    """Test serial connection failure with Exception."""
    mock_args = Mock()
    mock_args.host = None
    mock_args.port = "/dev/ttyUSB0"
    capture = MeshCap(mock_args)
    error_message = "Connection failed: Device not found"

    with patch(
        "meshtastic.serial_interface.SerialInterface",
        side_effect=Exception(error_message),
    ):
        with pytest.raises(SystemExit) as exc_info:
            capture._connect_to_interface()

    assert exc_info.value.code == 1


def test_connect_to_interface_serial_failure_error_message(capsys):
    """Test that serial failure prints correct error message to stderr."""
    mock_args = Mock()
    mock_args.host = None
    mock_args.port = "/dev/ttyUSB0"
    capture = MeshCap(mock_args)
    error_message = "Connection failed: Device not found"

    with patch(
        "meshtastic.serial_interface.SerialInterface",
        side_effect=Exception(error_message),
    ):
        with pytest.raises(SystemExit):
            capture._connect_to_interface()

    captured = capsys.readouterr()
    assert f"Error: Connection to device failed: {error_message}" in captured.err


def test_connect_to_interface_tcp_success(capsys):
    """Test successful connection to device via TCP interface."""
    mock_args = Mock()
    mock_args.host = "myradio.local"
    mock_args.tcp_port = 4403
    mock_interface = Mock()
    capture = MeshCap(mock_args)

    with patch(
        "meshtastic.tcp_interface.TCPInterface", return_value=mock_interface
    ):
        result = capture._connect_to_interface()

    assert result is mock_interface
    captured = capsys.readouterr()
    assert "Successfully connected to device at myradio.local:4403" in captured.out


def test_connect_to_interface_tcp_connection_refused():
    """Test TCP connection failure with ConnectionRefusedError."""
    mock_args = Mock()
    mock_args.host = "192.168.1.100"
    mock_args.tcp_port = 4403
    capture = MeshCap(mock_args)
    error_message = "Connection refused"

    with patch(
        "meshtastic.tcp_interface.TCPInterface",
        side_effect=ConnectionRefusedError(error_message),
    ):
        with pytest.raises(SystemExit) as exc_info:
            capture._connect_to_interface()

    assert exc_info.value.code == 1


def test_connect_to_interface_tcp_connection_refused_error_message(capsys):
    """Test that TCP connection refused prints specific error message to stderr."""
    mock_args = Mock()
    mock_args.host = "192.168.1.100"
    mock_args.tcp_port = 4403
    capture = MeshCap(mock_args)
    error_message = "Connection refused"

    with patch(
        "meshtastic.tcp_interface.TCPInterface",
        side_effect=ConnectionRefusedError(error_message),
    ):
        with pytest.raises(SystemExit):
            capture._connect_to_interface()

    captured = capsys.readouterr()
    assert "Error: TCP connection refused to 192.168.1.100:4403: Connection refused" in captured.err
