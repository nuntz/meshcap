import logging
from dataclasses import dataclass
from typing import Optional, Any, Union
from collections import OrderedDict

logger = logging.getLogger(__name__)


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


def to_node_num(value: Union[int, str]) -> int:
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
        result = value & 0xFFFFFFFF
        logger.debug(f"Converted int {value} to node_num {result:08x}")
        return result

    if isinstance(value, str):
        # Strip whitespace and remove leading '!' if present
        cleaned = value.strip()
        if cleaned.startswith("!"):
            cleaned = cleaned[1:]

        # Handle special broadcast addresses
        if cleaned.lower() in ("0000^all", "^all"):
            logger.debug(f"Converted broadcast address '{value}' to 0xFFFFFFFF")
            return 0xFFFFFFFF  # Broadcast address

        # Convert to lowercase, zero-fill to 8 characters, parse as hex
        hex_str = cleaned.lower().zfill(8)
        try:
            result = int(hex_str, 16)
            logger.debug(f"Converted string '{value}' to node_num {result:08x}")
            return result
        except ValueError as e:
            logger.error(f"Failed to convert string '{value}' to node_num: {e}")
            raise

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


@dataclass
class CacheStats:
    """Statistics for the NodeBook LRU cache."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0
    current_size: int = 0
    max_size: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate cache hit rate as a percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class NodeBook:
    """Cache for NodeLabel objects keyed by node number with LRU eviction."""

    def __init__(
        self, interface: Optional[Any] = None, max_cache_size: int = 1000
    ) -> None:
        self.interface: Optional[Any] = interface
        self._cache: OrderedDict[int, NodeLabel] = OrderedDict()
        self._max_cache_size: int = max_cache_size
        self._stats: CacheStats = CacheStats(max_size=max_cache_size)

    def get(self, node: Union[int, str]) -> NodeLabel:
        """
        Get NodeLabel for given node, using cache when available.

        Args:
            node: Node identifier as int or string

        Returns:
            NodeLabel for the node
        """
        node_num = to_node_num(node)

        if node_num in self._cache:
            logger.debug(f"Cache hit for node {node_num:08x}")
            # Move to end (most recently used)
            self._cache.move_to_end(node_num)
            self._stats.hits += 1
            return self._cache[node_num]

        logger.debug(f"Cache miss for node {node_num:08x}, resolving node info")
        self._stats.misses += 1

        user_id = to_user_id(node_num)
        long_name = None
        short_name = None

        # Try to resolve name from interface.nodes with schema tolerance
        if self.interface and hasattr(self.interface, "nodes"):
            try:
                # Try to find node using user_id format
                node_data = self.interface.nodes.get(user_id)
                if node_data:
                    logger.debug(f"Found node data for {user_id} in interface")
                    # Get user data with fallback for different schema versions
                    user = node_data.get("user") or node_data.get("userInfo") or {}
                    # Try different field name variations
                    long_name = user.get("longName") or user.get("long_name")
                    # For short_name, check if key exists to preserve empty strings
                    if "shortName" in user:
                        short_name = user["shortName"]
                    elif "short_name" in user:
                        short_name = user["short_name"]
                    logger.debug(
                        f"Resolved node {user_id}: long_name={long_name}, short_name={short_name}"
                    )
                else:
                    logger.debug(f"No node data found for {user_id} in interface")
            except (AttributeError, TypeError) as e:
                # Interface.nodes is not accessible or not a dict
                logger.warning(f"Could not access interface nodes for {user_id}: {e}")
                pass

        node_label = NodeLabel(
            node_num=node_num,
            user_id=user_id,
            long_name=long_name,
            short_name=short_name,
        )

        logger.debug(f"Caching node label for {node_num:08x}: {node_label.best()}")

        # Check if we need to evict entries to stay within size limit
        while len(self._cache) >= self._max_cache_size:
            evicted_node_num, evicted_label = self._cache.popitem(last=False)
            self._stats.evictions += 1
            logger.debug(
                f"Cache evicted node {evicted_node_num:08x}: {evicted_label.best()}"
            )

        self._cache[node_num] = node_label
        self._stats.current_size = len(self._cache)
        return node_label

    def get_cache_stats(self) -> CacheStats:
        """
        Get current cache statistics.

        Returns:
            CacheStats object containing hit/miss counts, evictions, and size info
        """
        self._stats.current_size = len(self._cache)
        return self._stats

    def clear_cache(self) -> None:
        """Clear all cached entries and reset statistics."""
        self._cache.clear()
        self._stats = CacheStats(max_size=self._max_cache_size)
