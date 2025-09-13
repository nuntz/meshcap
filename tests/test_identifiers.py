import pytest
from meshcap.identifiers import NodeLabel, to_node_num, to_user_id, NodeBook, CacheStats


class TestToNodeNum:
    """Test cases for to_node_num function."""

    def test_int_passthrough(self):
        """Test that integers are passed through with 32-bit masking."""
        assert to_node_num(0xA2EBDC20) == 0xA2EBDC20
        assert to_node_num(123456) == 123456
        assert to_node_num(0) == 0
        assert to_node_num(0xFFFFFFFF) == 0xFFFFFFFF

    def test_int_masking_over_32bit(self):
        """Test that integers >32-bit are masked to 32-bit."""
        assert to_node_num(0x1A2EBDC20) == 0xA2EBDC20
        assert to_node_num(0x100000000) == 0
        assert to_node_num(0x1FFFFFFFF) == 0xFFFFFFFF

    def test_string_with_exclamation(self):
        """Test string conversion with leading exclamation mark."""
        assert to_node_num("!a2ebdc20") == 0xA2EBDC20
        assert to_node_num("!dc20") == 0x0000DC20
        assert to_node_num("!0") == 0x00000000

    def test_string_without_exclamation(self):
        """Test string conversion without leading exclamation mark."""
        assert to_node_num("a2ebdc20") == 0xA2EBDC20
        assert to_node_num("dc20") == 0x0000DC20
        assert to_node_num("0") == 0x00000000

    def test_string_uppercase(self):
        """Test that uppercase strings are converted correctly."""
        assert to_node_num("A2EBDC20") == 0xA2EBDC20
        assert to_node_num("!A2EBDC20") == 0xA2EBDC20
        assert to_node_num("DC20") == 0x0000DC20
        assert to_node_num("!DC20") == 0x0000DC20

    def test_string_short_padded(self):
        """Test that short hex strings are zero-padded."""
        assert to_node_num("dc20") == 0x0000DC20
        assert to_node_num("1") == 0x00000001
        assert to_node_num("ab") == 0x000000AB
        assert to_node_num("123") == 0x00000123

    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        assert to_node_num("  a2ebdc20  ") == 0xA2EBDC20
        assert to_node_num("\t!dc20\n") == 0x0000DC20
        assert to_node_num("  DC20  ") == 0x0000DC20
        assert (
            to_node_num(" ! a2ebdc20 ") == 0x0A2EBDC20
        )  # Space after ! becomes part of hex

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        assert to_node_num("00000000") == 0x00000000
        assert to_node_num("ffffffff") == 0xFFFFFFFF
        assert to_node_num("FFFFFFFF") == 0xFFFFFFFF
        assert to_node_num("!ffffffff") == 0xFFFFFFFF

    def test_invalid_types(self):
        """Test that invalid types raise TypeError."""
        with pytest.raises(TypeError):
            to_node_num(None)

        with pytest.raises(TypeError):
            to_node_num([])

        with pytest.raises(TypeError):
            to_node_num({})

    def test_invalid_hex_strings(self):
        """Test that invalid hex strings raise ValueError."""
        with pytest.raises(ValueError):
            to_node_num("xyz")

        with pytest.raises(ValueError):
            to_node_num("!xyz")

        with pytest.raises(ValueError):
            to_node_num("a2ebdc2g")  # 'g' is not valid hex

    def test_special_broadcast_addresses(self):
        """Test that special broadcast addresses are handled correctly."""
        assert to_node_num("0000^all") == 0xFFFFFFFF
        assert to_node_num("^all") == 0xFFFFFFFF
        assert to_node_num("!0000^all") == 0xFFFFFFFF
        assert to_node_num("!^all") == 0xFFFFFFFF


class TestToUserId:
    """Test cases for to_user_id function."""

    def test_basic_conversion(self):
        """Test basic node number to user ID conversion."""
        assert to_user_id(0xA2EBDC20) == "!a2ebdc20"
        assert to_user_id(0x0000DC20) == "!0000dc20"
        assert to_user_id(0xFFFFFFFF) == "!ffffffff"
        assert to_user_id(0) == "!00000000"

    def test_masking_64bit_input(self):
        """Test that 64-bit input is properly masked to 32-bit."""
        assert to_user_id(0x1A2EBDC20) == "!a2ebdc20"
        assert to_user_id(0x100000000) == "!00000000"
        assert to_user_id(0x1FFFFFFFF) == "!ffffffff"

    def test_round_trip_conversion(self):
        """Test round-trip conversion between formats."""
        assert to_user_id(to_node_num("!a2ebdc20")) == "!a2ebdc20"
        assert to_user_id(to_node_num("!00000000")) == "!00000000"
        assert to_user_id(to_node_num("!ffffffff")) == "!ffffffff"
        assert to_user_id(to_node_num("a2ebdc20")) == "!a2ebdc20"
        assert to_user_id(to_node_num("dc20")) == "!0000dc20"


class TestNodeLabel:
    """Test NodeLabel dataclass and its best() method."""

    def test_best_prefers_short_name_over_long_name(self):
        """Test that best() returns short_name when both short and long names are available."""
        label = NodeLabel(
            node_num=123456,
            user_id="!0001e240",
            long_name="Long Device Name",
            short_name="Short",
        )
        assert label.best() == "Short"

    def test_best_prefers_long_name_over_user_id(self):
        """Test that best() returns long_name when short_name is not available."""
        label = NodeLabel(
            node_num=123456, user_id="!0001e240", long_name="Long Device Name"
        )
        assert label.best() == "Long Device Name"

    def test_best_falls_back_to_user_id(self):
        """Test that best() returns user_id when no names are available."""
        label = NodeLabel(node_num=123456, user_id="!0001e240")
        assert label.best() == "!0001e240"

    def test_best_trims_whitespace_from_short_name(self):
        """Test that best() strips whitespace from short_name."""
        label = NodeLabel(
            node_num=123456,
            user_id="!0001e240",
            long_name="Long Device Name",
            short_name="  Short  ",
        )
        assert label.best() == "Short"

    def test_best_ignores_empty_short_name(self):
        """Test that best() ignores empty or whitespace-only short_name."""
        label = NodeLabel(
            node_num=123456,
            user_id="!0001e240",
            long_name="Long Device Name",
            short_name="   ",
        )
        assert label.best() == "Long Device Name"

    def test_best_ignores_none_short_name(self):
        """Test that best() handles None short_name gracefully."""
        label = NodeLabel(
            node_num=123456,
            user_id="!0001e240",
            long_name="Long Device Name",
            short_name=None,
        )
        assert label.best() == "Long Device Name"

    def test_best_ignores_empty_string_short_name(self):
        """Test that best() ignores empty string short_name."""
        label = NodeLabel(
            node_num=123456,
            user_id="!0001e240",
            long_name="Long Device Name",
            short_name="",
        )
        assert label.best() == "Long Device Name"

    def test_frozen_dataclass(self):
        """Test that NodeLabel is frozen and immutable."""
        label = NodeLabel(node_num=123456, user_id="!0001e240")
        with pytest.raises(AttributeError):
            label.node_num = 789


class TestCacheStats:
    """Test CacheStats dataclass."""

    def test_default_values(self):
        """Test that CacheStats has reasonable defaults."""
        stats = CacheStats()
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.current_size == 0
        assert stats.max_size == 0

    def test_hit_rate_calculation(self):
        """Test hit rate calculation."""
        stats = CacheStats(hits=75, misses=25)
        assert stats.hit_rate == 75.0

        stats = CacheStats(hits=0, misses=10)
        assert stats.hit_rate == 0.0

        stats = CacheStats(hits=10, misses=0)
        assert stats.hit_rate == 100.0

    def test_hit_rate_no_data(self):
        """Test hit rate when no hits or misses recorded."""
        stats = CacheStats()
        assert stats.hit_rate == 0.0


class TestNodeBook:
    """Test NodeBook LRU cache functionality."""

    def test_initialization(self):
        """Test NodeBook initialization with default and custom cache sizes."""
        # Default cache size
        book = NodeBook()
        assert book._max_cache_size == 1000
        assert len(book._cache) == 0

        # Custom cache size
        book = NodeBook(max_cache_size=500)
        assert book._max_cache_size == 500
        assert len(book._cache) == 0

    def test_basic_cache_functionality(self):
        """Test basic cache hit/miss functionality."""
        book = NodeBook(max_cache_size=10)

        # First access should be a miss
        label1 = book.get(123456)
        assert label1.node_num == 123456
        assert label1.user_id == "!0001e240"

        stats = book.get_cache_stats()
        assert stats.hits == 0
        assert stats.misses == 1
        assert stats.current_size == 1

        # Second access should be a hit
        label2 = book.get(123456)
        assert label1 == label2

        stats = book.get_cache_stats()
        assert stats.hits == 1
        assert stats.misses == 1
        assert stats.current_size == 1

    def test_cache_size_limit_respected(self):
        """Test that cache size limit is respected with eviction."""
        book = NodeBook(max_cache_size=3)

        # Fill cache to capacity
        book.get(1)
        book.get(2)
        book.get(3)

        stats = book.get_cache_stats()
        assert stats.current_size == 3
        assert stats.evictions == 0

        # Add one more item, should cause eviction
        book.get(4)

        stats = book.get_cache_stats()
        assert stats.current_size == 3  # Still at max capacity
        assert stats.evictions == 1  # One eviction occurred

        # The first item (1) should have been evicted (LRU)
        # Accessing it should be a cache miss
        initial_misses = stats.misses
        book.get(1)
        stats = book.get_cache_stats()
        assert stats.misses == initial_misses + 1

    def test_lru_eviction_order(self):
        """Test that LRU eviction works correctly."""
        book = NodeBook(max_cache_size=2)

        # Fill cache
        book.get(1)
        book.get(2)

        # Access first item to make it most recently used
        book.get(1)

        # Add third item, should evict item 2 (least recently used)
        book.get(3)

        stats = book.get_cache_stats()
        assert stats.evictions == 1
        assert stats.current_size == 2

        # Item 1 should still be in cache (was accessed recently)
        initial_hits = stats.hits
        book.get(1)
        stats = book.get_cache_stats()
        assert stats.hits == initial_hits + 1

        # Item 2 should have been evicted (cache miss)
        initial_misses = stats.misses
        book.get(2)
        stats = book.get_cache_stats()
        assert stats.misses == initial_misses + 1

    def test_cache_statistics_accuracy(self):
        """Test that cache statistics are accurately maintained."""
        book = NodeBook(max_cache_size=5)

        # Generate some cache activity
        for i in range(10):  # Will cause evictions
            book.get(i)

        stats = book.get_cache_stats()

        # Should have had 5 evictions (cache size is 5, but we accessed 10 items)
        assert stats.evictions == 5
        assert stats.current_size == 5
        assert stats.misses == 10  # All first accesses were misses
        assert stats.hits == 0  # No repeated accesses yet

        # Access some items again to generate hits
        book.get(9)  # Should be a hit
        book.get(8)  # Should be a hit

        stats = book.get_cache_stats()
        assert stats.hits == 2
        assert stats.misses == 10

    def test_clear_cache(self):
        """Test cache clearing functionality."""
        book = NodeBook(max_cache_size=5)

        # Fill cache and generate some activity
        for i in range(3):
            book.get(i)
        book.get(0)  # Generate a hit

        stats = book.get_cache_stats()
        assert stats.current_size == 3
        assert stats.hits == 1
        assert stats.misses == 3

        # Clear cache
        book.clear_cache()

        stats = book.get_cache_stats()
        assert stats.current_size == 0
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.evictions == 0
        assert stats.max_size == 5  # Should preserve max_size

    def test_string_and_int_node_identifiers(self):
        """Test that both string and int node identifiers work with cache."""
        book = NodeBook(max_cache_size=5)

        # Access same node with different identifier formats
        label1 = book.get(123456)
        label2 = book.get("!0001e240")  # Same node as hex string
        label3 = book.get("0001e240")  # Same node without !

        # All should return the same cached object
        assert label1 == label2 == label3

        stats = book.get_cache_stats()
        assert stats.hits == 2  # Second and third were cache hits
        assert stats.misses == 1  # Only first was a miss
        assert stats.current_size == 1  # Only one unique node cached
