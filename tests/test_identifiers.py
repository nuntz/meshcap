import pytest
from meshcap.identifiers import NodeLabel, to_node_num, to_user_id


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
