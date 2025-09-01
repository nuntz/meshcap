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