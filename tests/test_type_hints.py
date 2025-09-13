"""Test file to validate type hints in identifiers module work correctly with mypy."""

from meshcap.identifiers import NodeLabel, NodeBook, to_node_num, to_user_id


def test_type_hints_compatibility() -> None:
    """Test that the type hints work correctly with various input types."""
    
    # Test to_node_num with different input types
    assert to_node_num(123456789) == 123456789
    assert to_node_num("a2ebdc20") == 0xa2ebdc20
    assert to_node_num("!a2ebdc20") == 0xa2ebdc20
    
    # Test to_user_id
    user_id: str = to_user_id(123456789)
    assert user_id.startswith("!")
    
    # Test NodeLabel creation and usage
    label: NodeLabel = NodeLabel(
        node_num=123456789,
        user_id="!075bcd15",
        long_name="Test Node",
        short_name="TN"
    )
    
    best_name: str = label.best()
    assert best_name == "TN"
    
    # Test NodeBook
    book: NodeBook = NodeBook(interface=None)
    retrieved_label: NodeLabel = book.get(123456789)
    assert isinstance(retrieved_label, NodeLabel)
    
    # Test with string input
    retrieved_label2: NodeLabel = book.get("!075bcd15")
    assert isinstance(retrieved_label2, NodeLabel)


def test_optional_types() -> None:
    """Test handling of optional types."""
    
    # NodeLabel with minimal data
    label: NodeLabel = NodeLabel(
        node_num=123,
        user_id="!0000007b",
        long_name=None,
        short_name=None
    )
    
    # The best() method should return user_id when names are None
    assert label.best() == "!0000007b"
    
    # Test NodeBook with interface
    class MockInterface:
        nodes = {"!0000007b": {"user": {"longName": "Mock Node"}}}
    
    book_with_interface: NodeBook = NodeBook(interface=MockInterface())
    label_from_interface: NodeLabel = book_with_interface.get(123)
    assert label_from_interface.long_name == "Mock Node"


if __name__ == "__main__":
    test_type_hints_compatibility()
    test_optional_types()
    print("All type hint tests passed!")