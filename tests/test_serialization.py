"""Tests for the serialization module."""

import json
import pickle
import tempfile
from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from meshcap.serialization import PacketSerializer


class TestPacketSerializer:
    """Test cases for PacketSerializer class."""

    def test_serialize_deserialize_basic_packet(self):
        """Test basic serialization and deserialization of a simple packet."""
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "channel": 0,
            "rxRssi": -45,
            "rxSnr": 8.5,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello, world!"},
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            deserialized = PacketSerializer.deserialize_from_json(f)

        assert deserialized == packet

    def test_serialize_deserialize_with_bytes(self):
        """Test serialization of packets containing bytes objects."""
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "encrypted": b"\x01\x02\x03\x04\xff",
            "decoded": {"portnum": "TEXT_MESSAGE_APP"},
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            deserialized = PacketSerializer.deserialize_from_json(f)

        assert deserialized == packet
        assert isinstance(deserialized["encrypted"], bytes)
        assert deserialized["encrypted"] == b"\x01\x02\x03\x04\xff"

    def test_serialize_deserialize_with_datetime(self):
        """Test serialization of packets containing datetime objects."""
        now = datetime.now(timezone.utc)
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "timestamp": now,
            "decoded": {"portnum": "TEXT_MESSAGE_APP"},
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            deserialized = PacketSerializer.deserialize_from_json(f)

        assert deserialized["timestamp"] == now
        assert isinstance(deserialized["timestamp"], datetime)

    def test_serialize_deserialize_nested_structures(self):
        """Test serialization of complex nested structures."""
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "encrypted": b"secret_data",
            "metadata": {
                "timestamps": [
                    datetime(2023, 10, 19, 12, 0, 0, tzinfo=timezone.utc),
                    datetime(2023, 10, 19, 13, 0, 0, tzinfo=timezone.utc),
                ],
                "binary_chunks": [b"chunk1", b"chunk2"],
                "nested": {
                    "more_bytes": b"deep_data",
                    "tuple_data": (1, b"tuple_bytes", "string"),
                },
            },
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            deserialized = PacketSerializer.deserialize_from_json(f)

        assert deserialized == packet
        assert isinstance(deserialized["encrypted"], bytes)
        assert isinstance(deserialized["metadata"]["timestamps"][0], datetime)
        assert isinstance(deserialized["metadata"]["binary_chunks"][0], bytes)
        assert isinstance(deserialized["metadata"]["nested"]["more_bytes"], bytes)
        assert isinstance(deserialized["metadata"]["nested"]["tuple_data"], tuple)

    def test_json_format_structure(self):
        """Test that JSON format includes proper wrapper structure."""
        packet = {"rxTime": 1697731200, "fromId": "!a1b2c3d4"}

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            raw_json = json.load(f)

        assert raw_json["format"] == "meshcap-json"
        assert raw_json["version"] == "1.0"
        assert "packet" in raw_json
        assert raw_json["packet"]["rxTime"] == 1697731200

    def test_deserialize_invalid_json(self):
        """Test handling of invalid JSON format."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            f.write("invalid json content")
            f.seek(0)

            with pytest.raises(ValueError, match="Invalid JSON format"):
                PacketSerializer.deserialize_from_json(f)

    def test_deserialize_invalid_wrapper(self):
        """Test handling of invalid wrapper format."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            json.dump({"invalid": "wrapper"}, f)
            f.seek(0)

            with pytest.raises(ValueError, match="Unsupported format"):
                PacketSerializer.deserialize_from_json(f)

    def test_deserialize_missing_packet(self):
        """Test handling of missing packet data."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            json.dump({"format": "meshcap-json", "version": "1.0"}, f)
            f.seek(0)

            with pytest.raises(ValueError, match="Missing packet data"):
                PacketSerializer.deserialize_from_json(f)

    def test_deserialize_eof(self):
        """Test handling of end of file."""
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            f.seek(0)

            with pytest.raises(EOFError):
                PacketSerializer.deserialize_from_json(f)

    def test_version_mismatch_warning(self):
        """Test that version mismatch generates a warning."""
        packet = {"rxTime": 1697731200}

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            # Manually write JSON with different version
            wrapper = {"format": "meshcap-json", "version": "2.0", "packet": packet}
            json.dump(wrapper, f)
            f.seek(0)

            with patch("meshcap.serialization.logger") as mock_logger:
                deserialized = PacketSerializer.deserialize_from_json(f)
                mock_logger.warning.assert_called_once()
                assert "Version mismatch" in mock_logger.warning.call_args[0][0]

        assert deserialized == packet

    def test_unknown_special_type_warning(self):
        """Test handling of unknown special types."""
        # Create JSON with unknown special type
        raw_data = {
            "format": "meshcap-json",
            "version": "1.0",
            "packet": {
                "unknown_type": {"__type__": "unknown_type", "__value__": "some_value"}
            },
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            json.dump(raw_data, f)
            f.seek(0)

            with patch("meshcap.serialization.logger") as mock_logger:
                deserialized = PacketSerializer.deserialize_from_json(f)
                mock_logger.warning.assert_called_once()
                assert "Unknown special type" in mock_logger.warning.call_args[0][0]

        # Should preserve the original structure when type is unknown
        assert deserialized["unknown_type"]["__type__"] == "unknown_type"


class TestBackwardsCompatibility:
    """Test backwards compatibility with pickle format."""

    def test_deserialize_auto_pickle_file(self):
        """Test auto-detection of pickle format."""
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "encrypted": b"binary_data",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello"},
        }

        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as f:
            pickle.dump(packet, f)
            f.seek(0)

            deserialized = PacketSerializer.deserialize_auto(f)

        assert deserialized == packet
        assert isinstance(deserialized["encrypted"], bytes)

    def test_deserialize_auto_json_file(self):
        """Test auto-detection of JSON format."""
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "encrypted": b"binary_data",
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)

            deserialized = PacketSerializer.deserialize_auto(f)

        assert deserialized == packet
        assert isinstance(deserialized["encrypted"], bytes)

    def test_deserialize_auto_binary_mode_json(self):
        """Test auto-detection of JSON in binary mode file."""
        packet = {"rxTime": 1697731200, "fromId": "!a1b2c3d4"}

        # First create JSON data
        json_data = {"format": "meshcap-json", "version": "1.0", "packet": packet}
        json_str = json.dumps(json_data) + "\n"

        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as f:
            f.write(json_str.encode("utf-8"))
            f.seek(0)

            deserialized = PacketSerializer.deserialize_auto(f)

        assert deserialized == packet

    def test_deserialize_auto_invalid_format(self):
        """Test handling of unrecognized format."""
        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as f:
            f.write(b"invalid content that's neither pickle nor JSON")
            f.seek(0)

            with pytest.raises(ValueError, match="Format detection failed"):
                PacketSerializer.deserialize_auto(f)

    def test_deserialize_auto_eof(self):
        """Test handling of empty file."""
        with tempfile.NamedTemporaryFile(mode="w+b", delete=False) as f:
            f.seek(0)

            with pytest.raises(EOFError):
                PacketSerializer.deserialize_auto(f)


class TestSpecialTypes:
    """Test handling of special data types."""

    def test_bytes_roundtrip(self):
        """Test that bytes objects survive roundtrip serialization."""
        test_cases = [
            b"",  # empty bytes
            b"hello",  # simple string
            b"\x00\x01\x02\x03\xff",  # binary data
            b"\xe2\x9c\x93",  # UTF-8 encoded data
            bytes(range(256)),  # all possible byte values
        ]

        for test_bytes in test_cases:
            packet = {"data": test_bytes}

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
                PacketSerializer.serialize_to_json(packet, f)
                f.seek(0)
                deserialized = PacketSerializer.deserialize_from_json(f)

            assert deserialized["data"] == test_bytes
            assert isinstance(deserialized["data"], bytes)

    def test_datetime_roundtrip(self):
        """Test that datetime objects survive roundtrip serialization."""
        test_cases = [
            datetime(2023, 1, 1),
            datetime(2023, 10, 19, 12, 30, 45),
            datetime(2023, 10, 19, 12, 30, 45, 123456),
            datetime.now(),
            datetime.now(timezone.utc),
        ]

        for test_dt in test_cases:
            packet = {"timestamp": test_dt}

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
                PacketSerializer.serialize_to_json(packet, f)
                f.seek(0)
                deserialized = PacketSerializer.deserialize_from_json(f)

            assert deserialized["timestamp"] == test_dt
            assert isinstance(deserialized["timestamp"], datetime)

    def test_tuple_roundtrip(self):
        """Test that tuple objects survive roundtrip serialization."""
        test_cases = [
            (),  # empty tuple
            (1, 2, 3),  # simple tuple
            ("a", b"bytes", datetime.now()),  # mixed types
            ((1, 2), (3, 4)),  # nested tuples
        ]

        for test_tuple in test_cases:
            packet = {"data": test_tuple}

            with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
                PacketSerializer.serialize_to_json(packet, f)
                f.seek(0)
                deserialized = PacketSerializer.deserialize_from_json(f)

            assert deserialized["data"] == test_tuple
            assert isinstance(deserialized["data"], tuple)

    def test_mixed_types_in_collections(self):
        """Test special types within lists and dictionaries."""
        packet = {
            "mixed_list": [b"bytes_data", datetime(2023, 1, 1), (1, 2, 3), "string"],
            "mixed_dict": {
                "bytes_key": b"bytes_value",
                "datetime_key": datetime(2023, 1, 1),
                "tuple_key": (4, 5, 6),
            },
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            deserialized = PacketSerializer.deserialize_from_json(f)

        assert deserialized == packet
        assert isinstance(deserialized["mixed_list"][0], bytes)
        assert isinstance(deserialized["mixed_list"][1], datetime)
        assert isinstance(deserialized["mixed_list"][2], tuple)
        assert isinstance(deserialized["mixed_dict"]["bytes_key"], bytes)
        assert isinstance(deserialized["mixed_dict"]["datetime_key"], datetime)
        assert isinstance(deserialized["mixed_dict"]["tuple_key"], tuple)

    def test_realistic_meshtastic_packet(self):
        """Test with a realistic Meshtastic packet structure."""
        packet = {
            "rxTime": 1697731200,
            "fromId": "!a1b2c3d4",
            "toId": "!e5f6g7h8",
            "encrypted": b"\x01\x02\x03\x04\xff\xaa\xbb\xcc",
            "channel": 0,
            "rxRssi": -45,
            "rxSnr": 8.5,
            "hopLimit": 3,
            "wantAck": False,
            "decoded": {
                "portnum": "TEXT_MESSAGE_APP",
                "payload": b"Hello, Mesh!",
                "text": "Hello, Mesh!",
                "requestId": 1234567890,
            },
            "timestamp": datetime.now(timezone.utc),
        }

        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as f:
            PacketSerializer.serialize_to_json(packet, f)
            f.seek(0)
            deserialized = PacketSerializer.deserialize_from_json(f)

        assert deserialized == packet
        assert isinstance(deserialized["encrypted"], bytes)
        assert isinstance(deserialized["decoded"]["payload"], bytes)
        assert isinstance(deserialized["timestamp"], datetime)
