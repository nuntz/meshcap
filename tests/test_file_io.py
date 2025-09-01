import sys
import tempfile
import os
import pickle
from unittest.mock import patch, Mock
import pytest
from meshcap.main import main, MeshCap


def create_mock_packet(from_id="!12345678", to_id="!87654321", text="Test message"):
    """Create a mock packet for testing."""
    return {
        "fromId": from_id,
        "toId": to_id,
        "rxTime": 1234567890,
        "channel": 1,
        "rxRssi": -50,
        "rxSnr": 10.5,
        "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": text},
    }


def test_counter_exits_after_target_count(capsys):
    """Test that the program exits after receiving the specified number of packets."""
    # Create mock args with count=3
    mock_args = Mock()
    mock_args.count = 3
    mock_args.label_mode = "named-with-hex"

    # Instantiate MeshCap
    capture = MeshCap(mock_args)

    mock_packets = [create_mock_packet(text=f"Message {i}") for i in range(5)]
    mock_interface = Mock()
    mock_interface.nodes = {}

    # Call _on_packet_received directly and check should_exit flag on 3rd packet
    for i, packet in enumerate(mock_packets):
        capture._on_packet_received(packet, mock_interface, no_resolve=True)
        if i == 2:  # Third packet should trigger exit flag
            assert capture.should_exit
            break

    captured = capsys.readouterr()
    assert "Processed 3 matching packets. Exiting..." in captured.out


def test_file_io_integration():
    """Integration test for writing packets to file and reading them back."""
    mock_packets = [
        create_mock_packet(from_id="!11111111", text="First message"),
        create_mock_packet(from_id="!22222222", text="Second message"),
        create_mock_packet(from_id="!33333333", text="Third message"),
    ]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_filename = temp_file.name

    try:
        # Test writer functionality using MeshCap class
        with open(temp_filename, "wb") as write_file:
            # Create mock args
            mock_args = Mock()
            mock_args.count = None
            mock_args.write_file = temp_filename
            mock_args.label_mode = "named-with-hex"

            # Instantiate MeshCap and manually assign file handle
            capture = MeshCap(mock_args)
            capture.write_file_handle = write_file

            mock_interface = Mock()
            mock_interface.nodes = {}

            # Write packets to file
            for packet in mock_packets:
                capture._on_packet_received(packet, mock_interface, no_resolve=True)

        # Verify packets were written to file
        with open(temp_filename, "rb") as f:
            written_packets = []
            try:
                while True:
                    written_packets.append(pickle.load(f))
            except EOFError:
                pass

        assert len(written_packets) == 3
        assert written_packets[0]["decoded"]["text"] == "First message"
        assert written_packets[1]["decoded"]["text"] == "Second message"
        assert written_packets[2]["decoded"]["text"] == "Third message"

        # Test reader functionality
        with (
            patch.object(sys, "argv", ["meshcap", "--read-file", temp_filename]),
            patch("builtins.print") as mock_print,
        ):
            main()

            # Check that packets were processed and printed
            print_calls = mock_print.call_args_list
            assert len(print_calls) >= 4  # 3 packets + header and footer messages

            # Verify the content of printed messages
            printed_output = "".join([str(call[0][0]) for call in print_calls])
            assert "First message" in printed_output
            assert "Second message" in printed_output
            assert "Third message" in printed_output
            assert "Processed 3 packets" in printed_output

    finally:
        # Clean up temporary file
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)


def test_read_nonexistent_file():
    """Test that reading from a nonexistent file exits with error."""
    with (
        patch.object(sys, "argv", ["meshcap", "--read-file", "/nonexistent/file.pkl"]),
        pytest.raises(SystemExit) as exc_info,
    ):
        main()

    assert exc_info.value.code == 1


def test_write_file_with_count():
    """Test combining write file and count features."""
    mock_packets = [create_mock_packet(text=f"Message {i}") for i in range(10)]

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_filename = temp_file.name

    try:
        # Test writer with count using MeshCap class
        with open(temp_filename, "wb") as write_file:
            # Create mock args with count
            mock_args = Mock()
            mock_args.count = 5
            mock_args.write_file = temp_filename
            mock_args.label_mode = "named-with-hex"

            # Instantiate MeshCap and manually assign file handle
            capture = MeshCap(mock_args)
            capture.write_file_handle = write_file

            mock_interface = Mock()
            mock_interface.nodes = {}

            # Process packets - should set exit flag on 5th packet
            for i, packet in enumerate(mock_packets):
                capture._on_packet_received(packet, mock_interface, no_resolve=True)
                if i == 4:  # Fifth packet should trigger exit flag
                    assert capture.should_exit
                    break

        # Verify exactly 5 packets were written
        with open(temp_filename, "rb") as f:
            written_packets = []
            try:
                while True:
                    written_packets.append(pickle.load(f))
            except EOFError:
                pass

        assert len(written_packets) == 5

    finally:
        if os.path.exists(temp_filename):
            os.unlink(temp_filename)


def test_no_resolve_with_none_interface():
    """Test that packets can be formatted when interface is None."""
    mock_args = Mock()
    mock_args.label_mode = "named-with-hex"
    capture = MeshCap(mock_args)
    packet = create_mock_packet()

    # Test with no_resolve=True and None interface
    formatted = capture._format_packet(packet, None, no_resolve=True)
    assert "from:!12345678 to:!87654321" in formatted
    assert "Test message" in formatted

    # Test with no_resolve=False but None interface (should still work)
    formatted = capture._format_packet(packet, None, no_resolve=False)
    assert "from:!12345678 to:!87654321" in formatted
    assert "Test message" in formatted
