"""Tests for NodeBook cache functionality."""

import pytest
from meshcap.identifiers import NodeBook, NodeLabel


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