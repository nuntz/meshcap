from dataclasses import dataclass
from typing import Dict, Optional, Any


@dataclass(frozen=True)
class NodeLabel:
    """Represents optional labels for a Meshtastic node with deterministic fallback."""

    node_num: int
    user_id: str
    long_name: Optional[str] = None
    short_name: Optional[str] = None

    def best(self) -> str:
        """
        Return the best available name for this node.

        Fallback order:
        1. short_name (if truthy after stripping whitespace)
        2. long_name (if available)
        3. user_id
        """
        if self.short_name and self.short_name.strip():
            return self.short_name.strip()
        if self.long_name:
            return self.long_name
        return self.user_id


def to_node_num(value: int | str) -> int:
    """
    Convert Meshtastic node identifier to canonical uint32 integer format.

    Supports all standard Meshtastic node identifier formats:

    - Integers: Direct conversion, masked to 32 bits (e.g., 123456789)
    - Hexadecimal strings: 8-character hex values (e.g., "a2ebdc20")
    - Meshtastic user ID strings: Hex with "!" prefix (e.g., "!a2ebdc20")
    - Special broadcast address: "^all" or "0000^all" -> 0xFFFFFFFF
    - Whitespace is automatically stripped from string inputs
    - Hex strings are zero-padded to 8 characters and case-insensitive

    Args:
        value: Node identifier as int or string in any supported format

    Returns:
        Node identifier as uint32 integer

    Raises:
        TypeError: If value is not int or str
        ValueError: If string format is invalid hex
    """
    if isinstance(value, int):
        return value & 0xFFFFFFFF

    if isinstance(value, str):
        # Strip whitespace and remove leading '!' if present
        cleaned = value.strip()
        if cleaned.startswith("!"):
            cleaned = cleaned[1:]

        # Handle special broadcast addresses
        if cleaned.lower() in ("0000^all", "^all"):
            return 0xFFFFFFFF  # Broadcast address

        # Convert to lowercase, zero-fill to 8 characters, parse as hex
        hex_str = cleaned.lower().zfill(8)
        return int(hex_str, 16)

    raise TypeError(f"Expected int or str, got {type(value)}")


def to_user_id(node_num: int) -> str:
    """
    Convert node number to Meshtastic user ID textual format.

    Args:
        node_num: Node identifier as integer

    Returns:
        Node identifier as string in format "!%08x"
    """
    return f"!{node_num & 0xFFFFFFFF:08x}"


class NodeBook:
    """Cache for NodeLabel objects keyed by node number."""

    def __init__(self, interface: Optional[Any] = None):
        self.interface = interface
        self._cache: Dict[int, NodeLabel] = {}

    def get(self, node: int | str) -> NodeLabel:
        """
        Get NodeLabel for given node, using cache when available.

        Args:
            node: Node identifier as int or string

        Returns:
            NodeLabel for the node
        """
        node_num = to_node_num(node)

        if node_num in self._cache:
            return self._cache[node_num]

        user_id = to_user_id(node_num)
        long_name = None
        short_name = None

        # Try to resolve name from interface.nodes with schema tolerance
        if self.interface and hasattr(self.interface, "nodes"):
            try:
                # Try to find node using user_id format
                node_data = self.interface.nodes.get(user_id)
                if node_data:
                    # Get user data with fallback for different schema versions
                    user = node_data.get("user") or node_data.get("userInfo") or {}
                    # Try different field name variations
                    long_name = user.get("longName") or user.get("long_name")
                    # For short_name, check if key exists to preserve empty strings
                    if "shortName" in user:
                        short_name = user["shortName"]
                    elif "short_name" in user:
                        short_name = user["short_name"]
            except (AttributeError, TypeError):
                # Interface.nodes is not accessible or not a dict
                pass

        node_label = NodeLabel(
            node_num=node_num,
            user_id=user_id,
            long_name=long_name,
            short_name=short_name,
        )

        self._cache[node_num] = node_label
        return node_label
