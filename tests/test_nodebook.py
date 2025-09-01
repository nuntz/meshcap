"""Tests for NodeBook cache functionality."""

import pytest
from meshcap.identifiers import NodeBook, NodeLabel


class MockInterface:
    """Mock interface for testing NodeBook."""
    
    def __init__(self, nodes=None):
        self.nodes = nodes or {}


class TestNodeBook:
    """Tests for NodeBook class."""

    def test_get_returns_stable_nodelabel(self):
        """Test that get() returns a stable NodeLabel for the same node."""
        book = NodeBook()
        
        # Test with integer node
        node_num = 123456789
        label1 = book.get(node_num)
        label2 = book.get(node_num)
        
        assert label1 == label2
        assert label1.node_num == node_num
        assert label1.user_id == "!075bcd15"
        assert label1.long_name is None
        assert label1.short_name is None
        
        # Test with string node
        node_str = "!075bcd15"
        label3 = book.get(node_str)
        
        assert label3 == label1  # Should be same as integer version
        assert label3.node_num == node_num

    def test_cache_is_used_same_object_identity(self):
        """Test that cache is used and returns same object identity for repeats."""
        book = NodeBook()
        
        node_num = 987654321
        
        # First call should create and cache
        label1 = book.get(node_num)
        
        # Second call should return same object from cache
        label2 = book.get(node_num)
        
        # Should be exact same object (not just equal)
        assert label1 is label2
        
        # Verify it has expected values
        assert label1.node_num == node_num
        assert label1.user_id == "!3ade68b1"

    def test_get_with_different_formats(self):
        """Test that get() works with different node formats but uses cache."""
        book = NodeBook()
        
        # These should all resolve to the same node
        formats = [
            123456789,
            "!075bcd15",  
            "075bcd15",
            "75bcd15",  # without leading zeros
        ]
        
        labels = [book.get(fmt) for fmt in formats]
        
        # All should be the same object (cached)
        for label in labels[1:]:
            assert label is labels[0]
        
        # All should have same node_num
        for label in labels:
            assert label.node_num == 123456789
            assert label.user_id == "!075bcd15"

    def test_interface_parameter_stored(self):
        """Test that interface parameter is stored correctly."""
        mock_interface = object()
        book = NodeBook(interface=mock_interface)
        
        assert book.interface is mock_interface
        
        # Should still work normally
        label = book.get(42)
        assert label.node_num == 42
        assert label.user_id == "!0000002a"

    def test_no_interface_default_behavior(self):
        """Test default behavior when no interface is provided."""
        book = NodeBook()
        
        assert book.interface is None
        
        label = book.get(999)
        assert label.node_num == 999
        assert label.user_id == "!000003e7"
        assert label.long_name is None
        assert label.short_name is None


class TestNodeBookNameResolution:
    """Tests for NodeBook name resolution with schema tolerance."""
    
    def test_get_with_mock_interface_resolves_names(self):
        """Test that NodeBook.get() resolves names from interface.nodes."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"user": {"longName": "ShutterBug", "shortName": "👍"}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name == "ShutterBug" 
        assert result.short_name == "👍"
        assert result.best() == "👍"
    
    def test_get_with_no_interface_fallback(self):
        """Test that NodeBook.get() falls back gracefully when no interface."""
        nodebook = NodeBook(interface=None)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name is None
        assert result.short_name is None
        assert result.best() == "!a2ebdc20"
    
    def test_get_with_missing_nodes_attribute(self):
        """Test that NodeBook.get() handles interface without nodes attribute."""
        class MockInterfaceWithoutNodes:
            pass
            
        nodebook = NodeBook(interface=MockInterfaceWithoutNodes())
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name is None
        assert result.short_name is None
        assert result.best() == "!a2ebdc20"
    
    def test_get_with_unresolvable_node(self):
        """Test that NodeBook.get() handles node not in interface.nodes."""
        mock_interface = MockInterface(nodes={})  # Empty nodes dict
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!12345678")  # Valid hex node ID
        
        assert result.user_id == "!12345678"
        assert result.long_name is None
        assert result.short_name is None
        assert result.best() == "!12345678"
    
    def test_get_with_missing_user_data(self):
        """Test that NodeBook.get() handles node with missing user data."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {}}  # Node exists but no user data
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name is None
        assert result.short_name is None
        assert result.best() == "!a2ebdc20"
    
    def test_get_with_alternative_schema_userinfo(self):
        """Test that NodeBook.get() handles alternative 'userInfo' schema."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"userInfo": {"longName": "AltSchema", "shortName": "Alt"}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name == "AltSchema"
        assert result.short_name == "Alt"
        assert result.best() == "Alt"
    
    def test_get_with_alternative_field_names(self):
        """Test that NodeBook.get() handles alternative field names (snake_case)."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"user": {"long_name": "SnakeCase", "short_name": "🐍"}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name == "SnakeCase"
        assert result.short_name == "🐍"
        assert result.best() == "🐍"
    
    def test_get_caches_resolved_results(self):
        """Test that NodeBook.get() caches resolved results for performance."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"user": {"longName": "Cached", "shortName": "C"}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        
        # First call should resolve from interface
        result1 = nodebook.get("!a2ebdc20")
        assert result1.best() == "C"
        
        # Modify interface to verify caching
        mock_interface.nodes["!a2ebdc20"]["user"]["shortName"] = "Modified"
        
        # Second call should return cached result
        result2 = nodebook.get("!a2ebdc20")
        assert result2.best() == "C"  # Should still be original value
        
        # Should be the same object reference
        assert result1 is result2
    
    def test_get_with_integer_node_input_resolved(self):
        """Test that NodeBook.get() works with integer node input and resolution."""
        # 0xa2ebdc20 = 2733366304 in decimal (corrected calculation)
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"user": {"longName": "IntegerNode", "shortName": "I"}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get(0xa2ebdc20)  # Use hex literal to avoid confusion
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name == "IntegerNode"
        assert result.short_name == "I"
        assert result.best() == "I"
    
    def test_get_with_only_long_name(self):
        """Test that NodeBook.get() works when only longName is available."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"user": {"longName": "OnlyLong"}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name == "OnlyLong"
        assert result.short_name is None
        assert result.best() == "OnlyLong"
    
    def test_get_with_empty_short_name_fallback(self):
        """Test that NodeBook.get() falls back to longName when shortName is empty."""
        mock_interface = MockInterface(
            nodes={"!a2ebdc20": {"user": {"longName": "FallbackLong", "shortName": ""}}}
        )
        
        nodebook = NodeBook(interface=mock_interface)
        result = nodebook.get("!a2ebdc20")
        
        assert result.user_id == "!a2ebdc20"
        assert result.long_name == "FallbackLong"
        assert result.short_name == ""
        assert result.best() == "FallbackLong"  # Should fallback due to empty shortName