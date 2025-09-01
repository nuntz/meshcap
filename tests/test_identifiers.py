import pytest
from meshcap.identifiers import to_node_num


class TestToNodeNum:
    """Test cases for to_node_num function."""
    
    def test_int_passthrough(self):
        """Test that integers are passed through with 32-bit masking."""
        assert to_node_num(0xa2ebdc20) == 0xa2ebdc20
        assert to_node_num(123456) == 123456
        assert to_node_num(0) == 0
        assert to_node_num(0xFFFFFFFF) == 0xFFFFFFFF
    
    def test_int_masking_over_32bit(self):
        """Test that integers >32-bit are masked to 32-bit."""
        assert to_node_num(0x1a2ebdc20) == 0xa2ebdc20
        assert to_node_num(0x100000000) == 0
        assert to_node_num(0x1FFFFFFFF) == 0xFFFFFFFF
    
    def test_string_with_exclamation(self):
        """Test string conversion with leading exclamation mark."""
        assert to_node_num('!a2ebdc20') == 0xa2ebdc20
        assert to_node_num('!dc20') == 0x0000dc20
        assert to_node_num('!0') == 0x00000000
    
    def test_string_without_exclamation(self):
        """Test string conversion without leading exclamation mark."""
        assert to_node_num('a2ebdc20') == 0xa2ebdc20
        assert to_node_num('dc20') == 0x0000dc20
        assert to_node_num('0') == 0x00000000
    
    def test_string_uppercase(self):
        """Test that uppercase strings are converted correctly."""
        assert to_node_num('A2EBDC20') == 0xa2ebdc20
        assert to_node_num('!A2EBDC20') == 0xa2ebdc20
        assert to_node_num('DC20') == 0x0000dc20
        assert to_node_num('!DC20') == 0x0000dc20
    
    def test_string_short_padded(self):
        """Test that short hex strings are zero-padded."""
        assert to_node_num('dc20') == 0x0000dc20
        assert to_node_num('1') == 0x00000001
        assert to_node_num('ab') == 0x000000ab
        assert to_node_num('123') == 0x00000123
    
    def test_whitespace_handling(self):
        """Test that whitespace is properly stripped."""
        assert to_node_num('  a2ebdc20  ') == 0xa2ebdc20
        assert to_node_num('\t!dc20\n') == 0x0000dc20
        assert to_node_num('  DC20  ') == 0x0000dc20
        assert to_node_num(' ! a2ebdc20 ') == 0x0a2ebdc20  # Space after ! becomes part of hex
    
    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        assert to_node_num('00000000') == 0x00000000
        assert to_node_num('ffffffff') == 0xffffffff
        assert to_node_num('FFFFFFFF') == 0xffffffff
        assert to_node_num('!ffffffff') == 0xffffffff
    
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
            to_node_num('xyz')
        
        with pytest.raises(ValueError):
            to_node_num('!xyz')
        
        with pytest.raises(ValueError):
            to_node_num('a2ebdc2g')  # 'g' is not valid hex