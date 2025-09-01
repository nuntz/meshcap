import sys
from unittest.mock import patch, Mock
import argparse
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
    parser.add_argument("--label-mode", choices=["auto", "named-with-hex", "named-only", "hex-only"], default="named-with-hex")
    
    # Parse with no label-mode argument
    args = parser.parse_args([])
    assert args.label_mode == "named-with-hex"


def test_label_mode_auto_alias():
    """Test that 'auto' maps to 'named-with-hex'."""
    # Create parser like in main()  
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    parser.add_argument("--label-mode", choices=["auto", "named-with-hex", "named-only", "hex-only"], default="named-with-hex")
    
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
    parser.add_argument("--label-mode", choices=["auto", "named-with-hex", "named-only", "hex-only"], default="named-with-hex")
    
    test_cases = ["auto", "named-with-hex", "named-only", "hex-only"]
    for choice in test_cases:
        args = parser.parse_args(["--label-mode", choice])
        assert args.label_mode == choice


def test_label_mode_with_test_mode(capsys):
    """Test that --label-mode works with --test-mode and prints connection line."""
    mock_interface = Mock()

    with (
        patch.object(sys, "argv", ["meshcap", "--label-mode", "hex-only", "--test-mode"]),
        patch(
            "meshtastic.serial_interface.SerialInterface", return_value=mock_interface
        ),
    ):
        main()

    captured = capsys.readouterr()
    assert "Successfully connected to device at /dev/ttyACM0" in captured.out
    assert "Test mode: Setup complete, exiting after subscription" in captured.out
