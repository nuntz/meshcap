"""Safe serialization module for Meshtastic packets.

This module provides JSON-based serialization to replace pickle usage,
addressing security concerns while maintaining backwards compatibility.
"""

import json
import pickle
import base64
from datetime import datetime
from typing import Any, Dict, IO, Union
import logging
from google.protobuf.json_format import MessageToDict
from google.protobuf.message import Message

logger = logging.getLogger(__name__)

# Format version for future compatibility
SERIALIZATION_FORMAT_VERSION = "1.0"


class PacketSerializer:
    """Safe serialization class for Meshtastic packets using JSON format."""

    @staticmethod
    def _encode_special_types(obj: Any) -> Any:
        """Recursively encode special types for JSON serialization.

        Args:
            obj: Object to encode

        Returns:
            JSON-serializable version of the object
        """
        if isinstance(obj, bytes):
            return {
                "__type__": "bytes",
                "__value__": base64.b64encode(obj).decode("utf-8"),
            }
        elif isinstance(obj, datetime):
            return {"__type__": "datetime", "__value__": obj.isoformat()}
        elif isinstance(obj, Message):
            # Handle protobuf Message objects
            return {
                "__type__": "protobuf",
                "__class__": obj.__class__.__name__,
                "__value__": MessageToDict(obj, preserving_proto_field_name=True),
            }
        elif isinstance(obj, dict):
            return {
                k: PacketSerializer._encode_special_types(v) for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [PacketSerializer._encode_special_types(item) for item in obj]
        elif isinstance(obj, tuple):
            return {
                "__type__": "tuple",
                "__value__": [
                    PacketSerializer._encode_special_types(item) for item in obj
                ],
            }
        else:
            return obj

    @staticmethod
    def _decode_special_types(obj: Any) -> Any:
        """Recursively decode special types from JSON deserialization.

        Args:
            obj: Object to decode

        Returns:
            Object with special types restored
        """
        if isinstance(obj, dict):
            if "__type__" in obj and "__value__" in obj:
                type_name = obj["__type__"]
                value = obj["__value__"]

                if type_name == "bytes":
                    return base64.b64decode(value.encode("utf-8"))
                elif type_name == "datetime":
                    return datetime.fromisoformat(value)
                elif type_name == "tuple":
                    return tuple(
                        PacketSerializer._decode_special_types(item) for item in value
                    )
                elif type_name == "protobuf":
                    # For protobuf objects, return the dictionary representation
                    # The original protobuf class info is preserved in __class__ if needed
                    return PacketSerializer._decode_special_types(value)
                else:
                    logger.warning(f"Unknown special type encountered: {type_name}")
                    return obj
            else:
                return {
                    k: PacketSerializer._decode_special_types(v) for k, v in obj.items()
                }
        elif isinstance(obj, list):
            return [PacketSerializer._decode_special_types(item) for item in obj]
        else:
            return obj

    @staticmethod
    def serialize_to_json(packet: Dict[str, Any], file_handle: IO[str]) -> None:
        """Serialize a packet to JSON format with version header.

        Args:
            packet: The packet dictionary to serialize
            file_handle: File handle opened in text mode for writing
        """
        # Create wrapper with version info
        wrapper = {
            "format": "meshcap-json",
            "version": SERIALIZATION_FORMAT_VERSION,
            "packet": PacketSerializer._encode_special_types(packet),
        }

        json.dump(wrapper, file_handle)
        file_handle.write("\n")  # Add newline for readability
        file_handle.flush()

    @staticmethod
    def deserialize_from_json(file_handle: IO[str]) -> Dict[str, Any]:
        """Deserialize a packet from JSON format.

        Args:
            file_handle: File handle opened in text mode for reading

        Returns:
            The deserialized packet dictionary

        Raises:
            EOFError: If end of file is reached
            ValueError: If JSON format is invalid or unsupported version
        """
        line = file_handle.readline()
        if not line:
            raise EOFError("End of file reached")

        try:
            wrapper = json.loads(line.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        # Validate format
        if not isinstance(wrapper, dict):
            raise ValueError("Invalid wrapper format: expected dictionary")

        if wrapper.get("format") != "meshcap-json":
            raise ValueError(f"Unsupported format: {wrapper.get('format')}")

        version = wrapper.get("version")
        if version != SERIALIZATION_FORMAT_VERSION:
            logger.warning(
                f"Version mismatch: expected {SERIALIZATION_FORMAT_VERSION}, got {version}"
            )

        packet = wrapper.get("packet")
        if packet is None:
            raise ValueError("Missing packet data in wrapper")

        return PacketSerializer._decode_special_types(packet)

    @staticmethod
    def deserialize_auto(file_handle: IO[Union[str, bytes]]) -> Dict[str, Any]:
        """Automatically detect format and deserialize packet.

        This method supports both JSON and pickle formats for backwards compatibility.

        Args:
            file_handle: File handle opened for reading (binary or text)

        Returns:
            The deserialized packet dictionary

        Raises:
            EOFError: If end of file is reached
            ValueError: If format cannot be detected or is invalid
        """
        # Save current position to reset if needed
        start_pos = file_handle.tell()

        try:
            # Try to read as text first to detect JSON
            if hasattr(file_handle, "mode") and "b" in file_handle.mode:
                # Binary mode - try to detect pickle first
                try:
                    file_handle.seek(start_pos)
                    packet = pickle.load(file_handle)
                    logger.debug("Successfully loaded packet using pickle format")
                    return packet
                except (pickle.PickleError, EOFError) as e:
                    # Not pickle format, try JSON
                    logger.debug(f"Pickle failed: {e}, trying JSON")
                    file_handle.seek(start_pos)

                    # Read as bytes and decode to string
                    line = file_handle.readline()
                    if not line:
                        raise EOFError("End of file reached")

                    try:
                        line_str = line.decode("utf-8").strip()
                        wrapper = json.loads(line_str)
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        # Not valid JSON either
                        raise ValueError(
                            "Unable to detect valid format (not pickle or JSON)"
                        )
            else:
                # Text mode - try JSON first
                try:
                    file_handle.seek(start_pos)
                    return PacketSerializer.deserialize_from_json(file_handle)
                except (ValueError, EOFError) as e:
                    logger.debug(f"JSON failed: {e}, trying pickle")
                    file_handle.seek(start_pos)

                    # Convert to binary for pickle
                    if hasattr(file_handle, "buffer"):
                        packet = pickle.load(file_handle.buffer)
                        logger.debug("Successfully loaded packet using pickle format")
                        return packet
                    else:
                        raise ValueError(
                            "Unable to read pickle from text mode file handle"
                        )
        except EOFError:
            # If we get EOFError, just re-raise it directly
            raise
        except Exception as e:
            file_handle.seek(start_pos)
            raise ValueError(f"Format detection failed: {e}")

        # If we get here, format detection failed
        file_handle.seek(start_pos)

        # Try JSON format parsing directly
        try:
            wrapper = json.loads(line_str)
            if wrapper.get("format") == "meshcap-json":
                packet = wrapper.get("packet")
                if packet is None:
                    raise ValueError("Missing packet data in wrapper")
                return PacketSerializer._decode_special_types(packet)
        except (NameError, json.JSONDecodeError, ValueError):
            pass

        raise ValueError("Unable to detect valid packet format")
