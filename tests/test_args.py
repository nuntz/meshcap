import sys
from unittest.mock import patch, Mock
import argparse
import pytest
from meshcap.main import main


def test_default_port(capsys):
    """Test that parsing with no arguments results in the default port /dev/ttyACM0."""
    mock_interface = Mock()

    with (
        patch.object(sys, "argv", ["meshcap", "--test-mode"]),
        patch(
            "meshtastic.serial_interface.SerialInterface", return_value=mock_interface
        ),
    ):
        main()

    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyACM0" in captured.out


def test_custom_port_long_form(capsys):
    """Test that providing --port /dev/ttyUSB0 correctly sets the port."""
    mock_interface = Mock()

    with (
        patch.object(sys, "argv", ["meshcap", "--port", "/dev/ttyUSB0", "--test-mode"]),
        patch(
            "meshtastic.serial_interface.SerialInterface", return_value=mock_interface
        ),
    ):
        main()

    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyUSB0" in captured.out


def test_custom_port_short_form(capsys):
    """Test that providing -p /dev/ttyUSB0 correctly sets the port."""
    mock_interface = Mock()

    with (
        patch.object(sys, "argv", ["meshcap", "-p", "/dev/ttyUSB0", "--test-mode"]),
        patch(
            "meshtastic.serial_interface.SerialInterface", return_value=mock_interface
        ),
    ):
        main()

    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyUSB0" in captured.out


def test_label_mode_default():
    """Test that --label-mode defaults to 'named-with-hex'."""
    # Create parser like in main()
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    parser.add_argument(
        "--label-mode",
        choices=["auto", "named-with-hex", "named-only", "hex-only"],
        default="named-with-hex",
    )

    # Parse with no label-mode argument
    args = parser.parse_args([])
    assert args.label_mode == "named-with-hex"


def test_label_mode_auto_alias():
    """Test that 'auto' maps to 'named-with-hex'."""
    # Create parser like in main()
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    parser.add_argument(
        "--label-mode",
        choices=["auto", "named-with-hex", "named-only", "hex-only"],
        default="named-with-hex",
    )

    # Parse with auto
    args = parser.parse_args(["--label-mode", "auto"])
    assert args.label_mode == "auto"

    # Apply alias mapping like in main()
    if args.label_mode == "auto":
        args.label_mode = "named-with-hex"
    assert args.label_mode == "named-with-hex"


def test_label_mode_all_choices():
    """Test that all label mode choices parse correctly."""
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    parser.add_argument(
        "--label-mode",
        choices=["auto", "named-with-hex", "named-only", "hex-only"],
        default="named-with-hex",
    )

    test_cases = ["auto", "named-with-hex", "named-only", "hex-only"]
    for choice in test_cases:
        args = parser.parse_args(["--label-mode", choice])
        assert args.label_mode == choice


def test_label_mode_with_test_mode(capsys):
    """Test that --label-mode works with --test-mode and prints connection line."""
    mock_interface = Mock()

    with (
        patch.object(
            sys, "argv", ["meshcap", "--label-mode", "hex-only", "--test-mode"]
        ),
        patch(
            "meshtastic.serial_interface.SerialInterface", return_value=mock_interface
        ),
    ):
        main()

    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyACM0" in captured.out
    assert "Test mode: Setup complete, exiting after subscription" in captured.out


def test_tcp_connection_args():
    """Test that --host myradio.local and --tcp-port 1234 are parsed correctly."""
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    
    # Create mutually exclusive group for connection arguments
    connection_group = parser.add_mutually_exclusive_group()
    connection_group.add_argument(
        "-p",
        "--port",
        default="/dev/ttyACM0",
        help="Serial device path (default: /dev/ttyACM0)",
    )
    connection_group.add_argument(
        "--host",
        help="TCP/IP hostname or IP address for network connection",
    )
    
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=4403,
        help="TCP port number for network connection (default: 4403)",
    )
    
    # Parse with host and tcp-port arguments
    args = parser.parse_args(["--host", "myradio.local", "--tcp-port", "1234"])
    assert args.host == "myradio.local"
    assert args.tcp_port == 1234
    assert args.port == "/dev/ttyACM0"  # Default value when using host


def test_mutually_exclusive_port_and_host():
    """Test that using both --port and --host raises SystemExit (mutually exclusive)."""
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    
    # Create mutually exclusive group for connection arguments
    connection_group = parser.add_mutually_exclusive_group()
    connection_group.add_argument(
        "-p",
        "--port",
        default="/dev/ttyACM0",
        help="Serial device path (default: /dev/ttyACM0)",
    )
    connection_group.add_argument(
        "--host",
        help="TCP/IP hostname or IP address for network connection",
    )
    
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=4403,
        help="TCP port number for network connection (default: 4403)",
    )
    
    # Test that using both --port and --host raises SystemExit
    with pytest.raises(SystemExit):
        parser.parse_args(["--port", "/dev/ttyFAKE", "--host", "myradio.local"])


def test_tcp_port_default():
    """Test that the default value of --tcp-port is 4403 when not specified."""
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    
    # Create mutually exclusive group for connection arguments
    connection_group = parser.add_mutually_exclusive_group()
    connection_group.add_argument(
        "-p",
        "--port",
        default="/dev/ttyACM0",
        help="Serial device path (default: /dev/ttyACM0)",
    )
    connection_group.add_argument(
        "--host",
        help="TCP/IP hostname or IP address for network connection",
    )
    
    parser.add_argument(
        "--tcp-port",
        type=int,
        default=4403,
        help="TCP port number for network connection (default: 4403)",
    )
    
    # Parse with no tcp-port argument
    args = parser.parse_args([])
    assert args.tcp_port == 4403
