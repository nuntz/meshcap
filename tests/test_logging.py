"""Tests for logging functionality in meshcap modules."""

import logging
import io
import sys
import unittest.mock
from unittest.mock import MagicMock

import pytest

from meshcap.filter import parse_filter, evaluate_filter, FilterError
from meshcap.identifiers import NodeBook, to_node_num
from meshcap.payload_formatter import PayloadFormatter


class TestLogging:
    """Test logging functionality across meshcap modules."""

    def test_filter_logging(self, caplog):
        """Test that filter parsing and evaluation generates appropriate log messages."""
        with caplog.at_level(logging.DEBUG):
            # Test filter parsing
            rpn = parse_filter(["port", "text", "and", "src", "node", "!12345678"])
            assert "Parsing filter expression" in caplog.text
            assert "Parsed filter to RPN" in caplog.text

            # Test filter evaluation
            packet = {
                "fromId": "!12345678",
                "toId": "!87654321",
                "decoded": {"portnum": "TEXT_MESSAGE_APP"},
            }
            result = evaluate_filter(rpn, packet)
            assert "Evaluating filter against packet" in caplog.text
            assert "Filter evaluation result" in caplog.text

    def test_filter_logging_empty_filter(self, caplog):
        """Test logging for empty filter."""
        with caplog.at_level(logging.DEBUG):
            rpn = parse_filter([])
            assert "Empty filter expression" in caplog.text

            result = evaluate_filter(rpn, {})
            assert "Empty filter - matches everything" in caplog.text

    def test_filter_error_logging(self, caplog):
        """Test logging for filter errors."""
        with caplog.at_level(logging.ERROR):
            # Test invalid node conversion
            packet = {"fromId": "invalid", "toId": "!87654321"}
            rpn = [("node", "src", "!12345678")]
            result = evaluate_filter(rpn, packet)
            # Should log error for invalid node conversion
            # (This is handled in to_node_num)

    def test_node_book_logging(self, caplog):
        """Test NodeBook cache logging."""
        with caplog.at_level(logging.DEBUG):
            # Mock interface with nodes
            mock_interface = MagicMock()
            mock_interface.nodes = {
                "!12345678": {"user": {"longName": "Test Node", "shortName": "TN"}}
            }

            book = NodeBook(mock_interface)

            # First call should be cache miss
            label = book.get("!12345678")
            assert "Cache miss for node 12345678" in caplog.text
            assert "Found node data for !12345678 in interface" in caplog.text
            assert (
                "Resolved node !12345678: long_name=Test Node, short_name=TN"
                in caplog.text
            )
            assert "Caching node label for 12345678" in caplog.text

            # Clear log for second call
            caplog.clear()

            # Second call should be cache hit
            label2 = book.get("!12345678")
            assert "Cache hit for node 12345678" in caplog.text

    def test_node_book_logging_no_data(self, caplog):
        """Test NodeBook logging when no node data is found."""
        with caplog.at_level(logging.DEBUG):
            mock_interface = MagicMock()
            mock_interface.nodes = {}

            book = NodeBook(mock_interface)
            label = book.get("!12345678")
            assert "No node data found for !12345678 in interface" in caplog.text

    def test_node_book_logging_interface_error(self, caplog):
        """Test NodeBook logging when interface access fails."""
        with caplog.at_level(logging.WARNING):
            mock_interface = MagicMock()
            mock_interface.nodes = None  # This will cause AttributeError

            book = NodeBook(mock_interface)
            label = book.get("!12345678")
            assert "Could not access interface nodes" in caplog.text

    def test_to_node_num_logging(self, caplog):
        """Test logging in to_node_num function."""
        with caplog.at_level(logging.DEBUG):
            # Test int conversion
            result = to_node_num(123456789)
            assert "Converted int 123456789 to node_num" in caplog.text

            # Test string conversion
            result = to_node_num("!12345678")
            assert "Converted string '!12345678' to node_num" in caplog.text

            # Test broadcast address
            result = to_node_num("^all")
            assert "Converted broadcast address '^all' to 0xFFFFFFFF" in caplog.text

    def test_to_node_num_error_logging(self, caplog):
        """Test error logging in to_node_num function."""
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError):
                to_node_num("invalid_hex")
            assert "Failed to convert string 'invalid_hex' to node_num" in caplog.text

    def test_payload_formatter_logging(self, caplog):
        """Test PayloadFormatter logging."""
        formatter = PayloadFormatter()

        with caplog.at_level(logging.DEBUG):
            # Test with no decoded payload
            packet = {}
            result = formatter.format(packet)
            assert "No decoded payload in packet" in caplog.text

            # Test with no portnum
            packet = {"decoded": {}}
            result = formatter.format(packet)
            assert "No portnum in decoded payload" in caplog.text

            # Test with valid text message
            packet = {"decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello"}}
            result = formatter.format(packet)
            assert "Formatting payload for portnum: TEXT_MESSAGE_APP" in caplog.text
            assert "Formatted TEXT_MESSAGE_APP payload: text:Hello" in caplog.text

            caplog.clear()

            # Test with unknown portnum
            packet = {"decoded": {"portnum": "UNKNOWN_APP"}}
            result = formatter.format(packet)
            assert "No formatter available for portnum: UNKNOWN_APP" in caplog.text

    def test_payload_formatter_error_logging(self, caplog):
        """Test PayloadFormatter error logging for data conversion failures."""
        formatter = PayloadFormatter()

        with caplog.at_level(logging.WARNING):
            # Test position with invalid data
            packet = {
                "decoded": {
                    "portnum": "POSITION_APP",
                    "position": {
                        "latitude": "invalid",
                        "longitude": None,
                        "altitude": "also_invalid",
                    },
                }
            }
            result = formatter.format(packet)
            assert "Could not convert latitude invalid to float" in caplog.text
            assert "Could not convert altitude also_invalid to int" in caplog.text

            caplog.clear()

            # Test telemetry with invalid data
            packet = {
                "decoded": {
                    "portnum": "TELEMETRY_APP",
                    "telemetry": {
                        "device_metrics": {
                            "battery_level": "invalid",
                            "voltage": "bad_voltage",
                        },
                        "environment_metrics": {"temperature": "not_a_number"},
                    },
                }
            }
            result = formatter.format(packet)
            assert "Could not convert battery level invalid to int" in caplog.text
            assert "Could not convert voltage bad_voltage to float" in caplog.text
            assert "Could not convert temperature not_a_number to float" in caplog.text

    def test_logging_levels(self):
        """Test that different log levels work correctly."""
        # Create a string buffer to capture log output
        log_buffer = io.StringIO()
        handler = logging.StreamHandler(log_buffer)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))

        # Get logger and add handler
        logger = logging.getLogger("meshcap.identifiers")
        logger.addHandler(handler)
        original_level = logger.level

        try:
            # Test DEBUG level
            logger.setLevel(logging.DEBUG)
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")

            output = log_buffer.getvalue()
            assert "DEBUG: Debug message" in output
            assert "INFO: Info message" in output
            assert "WARNING: Warning message" in output
            assert "ERROR: Error message" in output

            # Reset buffer
            log_buffer.seek(0)
            log_buffer.truncate(0)

            # Test WARNING level (should only show WARNING and ERROR)
            logger.setLevel(logging.WARNING)
            logger.debug("Debug message 2")
            logger.info("Info message 2")
            logger.warning("Warning message 2")
            logger.error("Error message 2")

            output = log_buffer.getvalue()
            assert "Debug message 2" not in output
            assert "Info message 2" not in output
            assert "WARNING: Warning message 2" in output
            assert "ERROR: Error message 2" in output

        finally:
            logger.removeHandler(handler)
            logger.setLevel(original_level)
            handler.close()
