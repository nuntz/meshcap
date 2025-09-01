from dataclasses import dataclass
from typing import Optional


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
    
    Args:
        value: Node identifier as int or string (hex format, optionally prefixed with '!')
        
    Returns:
        Node identifier as uint32 integer
    """
    if isinstance(value, int):
        return value & 0xFFFFFFFF
    
    if isinstance(value, str):
        # Strip whitespace and remove leading '!' if present
        cleaned = value.strip()
        if cleaned.startswith('!'):
            cleaned = cleaned[1:]
        
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