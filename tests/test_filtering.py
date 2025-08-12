"""Tests for filter expression parsing and evaluation."""

import pytest
from typing import List, Union, Tuple
from meshcap.filter import (
    FilterParser,
    FilterEvaluator,
    FilterError,
    parse_filter,
    evaluate_filter,
)


class TestFilterParser:
    """Tests for the FilterParser class."""

    def test_empty_expression(self):
        """Test parsing empty expression."""
        parser = FilterParser()
        result = parser.parse([])
        assert result == []

    def test_simple_node_filter(self):
        """Test parsing simple node filter."""
        parser = FilterParser()
        result = parser.parse(["node", "A"])
        assert result == [("node", "both", "A")]

    def test_src_node_filter(self):
        """Test parsing src node filter."""
        parser = FilterParser()
        result = parser.parse(["src", "node", "A"])
        assert result == [("node", "src", "A")]

    def test_dst_node_filter(self):
        """Test parsing dst node filter."""
        parser = FilterParser()
        result = parser.parse(["dst", "node", "B"])
        assert result == [("node", "dst", "B")]

    def test_port_filter(self):
        """Test parsing port filter."""
        parser = FilterParser()
        result = parser.parse(["port", "text"])
        assert result == [("port", "portnum", "text")]

    def test_hop_limit_filters(self):
        """Test parsing hop_limit filters with different operators."""
        parser = FilterParser()

        result = parser.parse(["hop_limit", "<", "5"])
        assert result == [("hop_limit", "<", "5")]

        result = parser.parse(["hop_limit", ">", "10"])
        assert result == [("hop_limit", ">", "10")]

        result = parser.parse(["hop_limit", "=", "3"])
        assert result == [("hop_limit", "=", "3")]

    def test_priority_filter(self):
        """Test parsing priority filter."""
        parser = FilterParser()
        result = parser.parse(["priority", "HIGH"])
        assert result == [("priority", "priority", "HIGH")]

    def test_want_ack_filter(self):
        """Test parsing want_ack filter."""
        parser = FilterParser()
        result = parser.parse(["want_ack"])
        assert result == [("want_ack", "wantAck", "true")]

    def test_is_encrypted_filter(self):
        """Test parsing 'is encrypted' filter."""
        parser = FilterParser()
        result = parser.parse(["is", "encrypted"])
        assert result == [("encryption", "status", "encrypted")]

    def test_is_plaintext_filter(self):
        """Test parsing 'is plaintext' filter."""
        parser = FilterParser()
        result = parser.parse(["is", "plaintext"])
        assert result == [("encryption", "status", "plaintext")]

    def test_encrypted_shorthand(self):
        """Test parsing 'encrypted' shorthand."""
        parser = FilterParser()
        result = parser.parse(["encrypted"])
        assert result == [("encryption", "status", "encrypted")]

    def test_plaintext_shorthand(self):
        """Test parsing 'plaintext' shorthand."""
        parser = FilterParser()
        result = parser.parse(["plaintext"])
        assert result == [("encryption", "status", "plaintext")]

    def test_simple_and_expression(self):
        """Test parsing simple AND expression."""
        parser = FilterParser()
        result = parser.parse(["node", "A", "and", "port", "text"])
        assert result == [("node", "both", "A"), ("port", "portnum", "text"), "and"]

    def test_simple_or_expression(self):
        """Test parsing simple OR expression."""
        parser = FilterParser()
        result = parser.parse(["port", "text", "or", "port", "position"])
        assert result == [
            ("port", "portnum", "text"),
            ("port", "portnum", "position"),
            "or",
        ]

    def test_not_expression(self):
        """Test parsing NOT expression."""
        parser = FilterParser()
        result = parser.parse(["not", "encrypted"])
        assert result == [("encryption", "status", "encrypted"), "not"]

    def test_complex_expression_with_parentheses(self):
        """Test parsing complex expression with parentheses."""
        parser = FilterParser()
        result = parser.parse(
            [
                "src",
                "node",
                "A",
                "and",
                "(",
                "port",
                "text",
                "or",
                "port",
                "position",
                ")",
            ]
        )
        expected = [
            ("node", "src", "A"),
            ("port", "portnum", "text"),
            ("port", "portnum", "position"),
            "or",
            "and",
        ]
        assert result == expected

    def test_operator_precedence(self):
        """Test operator precedence (and has higher precedence than or)."""
        parser = FilterParser()
        result = parser.parse(["node", "A", "or", "node", "B", "and", "port", "text"])
        expected = [
            ("node", "both", "A"),
            ("node", "both", "B"),
            ("port", "portnum", "text"),
            "and",
            "or",
        ]
        assert result == expected

    def test_not_precedence(self):
        """Test NOT has highest precedence."""
        parser = FilterParser()
        result = parser.parse(["not", "encrypted", "and", "node", "A"])
        expected = [
            ("encryption", "status", "encrypted"),
            "not",
            ("node", "both", "A"),
            "and",
        ]
        assert result == expected

    def test_invalid_node_syntax(self):
        """Test error handling for invalid node syntax."""
        parser = FilterParser()
        with pytest.raises(FilterError, match="'node' primitive requires a value"):
            parser.parse(["node"])

    def test_invalid_src_syntax(self):
        """Test error handling for invalid src syntax."""
        parser = FilterParser()
        with pytest.raises(FilterError, match="'src' must be followed by 'node'"):
            parser.parse(["src", "invalid"])

    def test_invalid_hop_limit_operator(self):
        """Test error handling for invalid hop_limit operator."""
        parser = FilterParser()
        with pytest.raises(FilterError, match="Invalid hop_limit operator"):
            parser.parse(["hop_limit", "!=", "5"])

    def test_invalid_is_syntax(self):
        """Test error handling for invalid 'is' syntax."""
        parser = FilterParser()
        with pytest.raises(
            FilterError, match="'is' must be followed by 'encrypted' or 'plaintext'"
        ):
            parser.parse(["is", "invalid"])

    def test_mismatched_parentheses(self):
        """Test error handling for mismatched parentheses."""
        parser = FilterParser()
        with pytest.raises(FilterError, match="Mismatched parentheses"):
            parser.parse(["(", "node", "A"])

        with pytest.raises(FilterError, match="Mismatched parentheses"):
            parser.parse(["node", "A", ")"])

    def test_user_filter_parsing(self):
        """Test parsing user filter expressions."""
        parser = FilterParser()

        # Simple user filter
        result = parser.parse(["user", "Alice"])
        assert result == [("user", "both", "Alice")]

        # Source user filter
        result = parser.parse(["src", "user", "Bob"])
        assert result == [("user", "src", "Bob")]

        # Destination user filter
        result = parser.parse(["dst", "user", "Charlie"])
        assert result == [("user", "dst", "Charlie")]

        # Test invalid syntax - should raise FilterError
        with pytest.raises(
            FilterError, match="'src' must be followed by 'node' or 'user'"
        ):
            parser.parse(["src", "name", "Eve"])


class TestFilterEvaluator:
    """Tests for the FilterEvaluator class."""

    def create_mock_interface(self):
        """Create a mock interface with user data for testing."""

        class MockInterface:
            def __init__(self):
                self.nodes = {
                    "!1111": {"user": {"longName": "Alice", "shortName": "A"}},
                    "!2222": {"user": {"longName": "Bob", "shortName": "B"}},
                }

        return MockInterface()

    def create_packet(self, **kwargs):
        """Helper to create test packets."""
        default = {
            "fromId": "nodeA",
            "toId": "nodeB",
            "hopLimit": 3,
            "priority": "UNSET",
            "wantAck": False,
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello world"},
        }
        default.update(kwargs)
        return default

    def test_empty_filter(self):
        """Test that empty filter matches everything."""
        evaluator = FilterEvaluator()
        packet = self.create_packet()
        assert evaluator.evaluate_rpn([], packet) is True

    def test_node_filter_both(self):
        """Test node filter matching either src or dst."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(fromId="nodeA", toId="nodeB")

        # Should match source
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "both", "nodeA")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # Should match destination
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "both", "nodeB")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # Should not match unknown node
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "both", "nodeC")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_src_node_filter(self):
        """Test src node filter."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(fromId="nodeA", toId="nodeB")

        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "src", "nodeA")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "src", "nodeB")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_dst_node_filter(self):
        """Test dst node filter."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(fromId="nodeA", toId="nodeB")

        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "dst", "nodeB")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "dst", "nodeA")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_port_filter(self):
        """Test port filter with various port types."""
        evaluator = FilterEvaluator()

        # Text message
        packet = self.create_packet(decoded={"portnum": "TEXT_MESSAGE_APP"})
        rpn: List[Union[Tuple[str, str, str], str]] = [("port", "portnum", "text")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # Position
        packet = self.create_packet(decoded={"portnum": "POSITION_APP"})
        rpn: List[Union[Tuple[str, str, str], str]] = [("port", "portnum", "position")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # Exact match
        packet = self.create_packet(decoded={"portnum": "ADMIN_APP"})
        rpn: List[Union[Tuple[str, str, str], str]] = [("port", "portnum", "ADMIN_APP")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # No match
        packet = self.create_packet(decoded={"portnum": "TEXT_MESSAGE_APP"})
        rpn: List[Union[Tuple[str, str, str], str]] = [("port", "portnum", "position")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_hop_limit_filter(self):
        """Test hop_limit filter with different operators."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(hopLimit=5)

        # Less than
        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", "<", "10")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", "<", "3")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

        # Greater than
        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", ">", "3")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", ">", "10")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

        # Equal to
        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", "=", "5")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", "=", "3")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_priority_filter(self):
        """Test priority filter."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(priority="HIGH")

        rpn: List[Union[Tuple[str, str, str], str]] = [("priority", "priority", "HIGH")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [("priority", "priority", "LOW")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_want_ack_filter(self):
        """Test want_ack filter."""
        evaluator = FilterEvaluator()

        packet = self.create_packet(wantAck=True)
        rpn: List[Union[Tuple[str, str, str], str]] = [("want_ack", "wantAck", "true")]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        packet = self.create_packet(wantAck=False)
        rpn: List[Union[Tuple[str, str, str], str]] = [("want_ack", "wantAck", "true")]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_encryption_filter(self):
        """Test encryption status filters."""
        evaluator = FilterEvaluator()

        # Plaintext packet (has decoded, no encrypted)
        packet = self.create_packet(decoded={"portnum": "TEXT_MESSAGE_APP"})

        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("encryption", "status", "plaintext")
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("encryption", "status", "encrypted")
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False

        # Encrypted packet (has encrypted, no decoded)
        packet = {"encrypted": b"somedata"}

        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("encryption", "status", "encrypted")
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("encryption", "status", "plaintext")
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_and_operator(self):
        """Test AND operator."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(
            fromId="nodeA", decoded={"portnum": "TEXT_MESSAGE_APP"}
        )

        # Both conditions true
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeA"),
            ("port", "portnum", "text"),
            "and",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # First true, second false
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeA"),
            ("port", "portnum", "position"),
            "and",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False

        # First false, second true
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeB"),
            ("port", "portnum", "text"),
            "and",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False

        # Both false
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeB"),
            ("port", "portnum", "position"),
            "and",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_or_operator(self):
        """Test OR operator."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(
            fromId="nodeA", decoded={"portnum": "TEXT_MESSAGE_APP"}
        )

        # Both conditions true
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeA"),
            ("port", "portnum", "text"),
            "or",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # First true, second false
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeA"),
            ("port", "portnum", "position"),
            "or",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # First false, second true
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeB"),
            ("port", "portnum", "text"),
            "or",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True

        # Both false
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeB"),
            ("port", "portnum", "position"),
            "or",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False

    def test_not_operator(self):
        """Test NOT operator."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(fromId="nodeA")

        # True becomes False
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "src", "nodeA"), "not"]
        assert evaluator.evaluate_rpn(rpn, packet) is False

        # False becomes True
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "src", "nodeB"), "not"]
        assert evaluator.evaluate_rpn(rpn, packet) is True

    def test_complex_expression(self):
        """Test complex expression evaluation."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(
            fromId="nodeA",
            toId="nodeB",
            decoded={"portnum": "TEXT_MESSAGE_APP"},
            hopLimit=5,
        )

        # (src node nodeA and port text) or hop_limit > 10
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeA"),
            ("port", "portnum", "text"),
            "and",
            ("hop_limit", ">", "10"),
            "or",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is True  # First part is true

        # (src node nodeB and port text) or hop_limit > 10
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeB"),
            ("port", "portnum", "text"),
            "and",
            ("hop_limit", ">", "10"),
            "or",
        ]
        assert evaluator.evaluate_rpn(rpn, packet) is False  # Both parts are false

    def test_invalid_hop_limit_value(self):
        """Test error handling for invalid hop_limit value."""
        evaluator = FilterEvaluator()
        packet = self.create_packet(hopLimit=5)

        rpn: List[Union[Tuple[str, str, str], str]] = [("hop_limit", ">", "invalid")]
        with pytest.raises(FilterError, match="Invalid hop_limit value"):
            evaluator.evaluate_rpn(rpn, packet)

    def test_insufficient_operands(self):
        """Test error handling for insufficient operands."""
        evaluator = FilterEvaluator()
        packet = self.create_packet()

        # Not enough operands for 'and'
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "src", "nodeA"), "and"]
        with pytest.raises(FilterError, match="'and' operator requires two operands"):
            evaluator.evaluate_rpn(rpn, packet)

        # Not enough operands for 'not'
        rpn: List[Union[Tuple[str, str, str], str]] = ["not"]
        with pytest.raises(FilterError, match="'not' operator requires one operand"):
            evaluator.evaluate_rpn(rpn, packet)

    def test_invalid_expression_result(self):
        """Test error handling for invalid expression (wrong stack size)."""
        evaluator = FilterEvaluator()
        packet = self.create_packet()

        # Too many operands
        rpn: List[Union[Tuple[str, str, str], str]] = [
            ("node", "src", "nodeA"),
            ("port", "portnum", "text"),
        ]
        with pytest.raises(FilterError, match="Invalid expression"):
            evaluator.evaluate_rpn(rpn, packet)

    def test_user_filter_evaluation(self):
        """Test user filter evaluation with mock interface."""
        evaluator = FilterEvaluator()
        mock_interface = self.create_mock_interface()

        # Test src user Alice matches packet from !1111
        packet = self.create_packet(fromId="!1111", toId="!2222")
        rpn: List[Union[Tuple[str, str, str], str]] = [("user", "src", "Alice")]
        assert evaluator.evaluate_rpn(rpn, packet, mock_interface) is True

        # Test dst user B (short name) matches packet to !2222
        packet = self.create_packet(fromId="!1111", toId="!2222")
        rpn: List[Union[Tuple[str, str, str], str]] = [("user", "dst", "B")]
        assert evaluator.evaluate_rpn(rpn, packet, mock_interface) is True

        # Test user Bob matches packet from !2222 (both direction)
        packet = self.create_packet(fromId="!2222", toId="!1111")
        rpn: List[Union[Tuple[str, str, str], str]] = [("user", "both", "Bob")]
        assert evaluator.evaluate_rpn(rpn, packet, mock_interface) is True

        # Test user Bob matches packet to !2222 (both direction)
        packet = self.create_packet(fromId="!1111", toId="!2222")
        rpn: List[Union[Tuple[str, str, str], str]] = [("user", "both", "Bob")]
        assert evaluator.evaluate_rpn(rpn, packet, mock_interface) is True

        # Test user Charlie does not match any packet
        packet = self.create_packet(fromId="!1111", toId="!2222")
        rpn: List[Union[Tuple[str, str, str], str]] = [("user", "both", "Charlie")]
        assert evaluator.evaluate_rpn(rpn, packet, mock_interface) is False

        # Test filter returns False if interface is None
        rpn: List[Union[Tuple[str, str, str], str]] = [("user", "src", "Alice")]
        assert evaluator.evaluate_rpn(rpn, packet, None) is False


class TestConvenienceFunctions:
    """Tests for the convenience functions."""

    def test_parse_filter_function(self):
        """Test parse_filter convenience function."""
        result = parse_filter(["node", "A", "and", "port", "text"])
        expected = [("node", "both", "A"), ("port", "portnum", "text"), "and"]
        assert result == expected

    def test_evaluate_filter_function(self):
        """Test evaluate_filter convenience function."""
        rpn: List[Union[Tuple[str, str, str], str]] = [("node", "src", "nodeA")]
        packet = {"fromId": "nodeA", "toId": "nodeB"}

        assert evaluate_filter(rpn, packet) is True

        packet = {"fromId": "nodeB", "toId": "nodeC"}
        assert evaluate_filter(rpn, packet) is False


class TestIntegrationScenarios:
    """Integration tests with realistic scenarios."""

    def test_text_message_filter(self):
        """Test filtering for text messages from specific node."""
        expression = ["src", "node", "!12345678", "and", "port", "text"]
        rpn = parse_filter(expression)

        # Matching packet
        packet = {
            "fromId": "!12345678",
            "toId": "!87654321",
            "decoded": {"portnum": "TEXT_MESSAGE_APP", "text": "Hello world"},
        }
        assert evaluate_filter(rpn, packet) is True

        # Wrong source
        packet["fromId"] = "!99999999"
        assert evaluate_filter(rpn, packet) is False

        # Wrong port
        packet["fromId"] = "!12345678"
        packet["decoded"]["portnum"] = "POSITION_APP"
        assert evaluate_filter(rpn, packet) is False

    def test_high_priority_or_ack_required(self):
        """Test filtering for high priority OR ack required packets."""
        expression = ["priority", "HIGH", "or", "want_ack"]
        rpn = parse_filter(expression)

        # High priority packet
        packet = {
            "priority": "HIGH",
            "wantAck": False,
            "fromId": "nodeA",
            "toId": "nodeB",
        }
        assert evaluate_filter(rpn, packet) is True

        # Want ack packet
        packet = {
            "priority": "UNSET",
            "wantAck": True,
            "fromId": "nodeA",
            "toId": "nodeB",
        }
        assert evaluate_filter(rpn, packet) is True

        # Neither condition
        packet = {
            "priority": "UNSET",
            "wantAck": False,
            "fromId": "nodeA",
            "toId": "nodeB",
        }
        assert evaluate_filter(rpn, packet) is False

    def test_complex_parentheses_expression(self):
        """Test complex expression with parentheses."""
        expression = [
            "(",
            "src",
            "node",
            "A",
            "or",
            "dst",
            "node",
            "A",
            ")",
            "and",
            "(",
            "port",
            "text",
            "or",
            "port",
            "position",
            ")",
        ]
        rpn = parse_filter(expression)

        # Node A sending text message
        packet = {
            "fromId": "A",
            "toId": "B",
            "decoded": {"portnum": "TEXT_MESSAGE_APP"},
        }
        assert evaluate_filter(rpn, packet) is True

        # Node B sending position to A
        packet = {"fromId": "B", "toId": "A", "decoded": {"portnum": "POSITION_APP"}}
        assert evaluate_filter(rpn, packet) is True

        # Node A sending admin message (should not match)
        packet = {"fromId": "A", "toId": "B", "decoded": {"portnum": "ADMIN_APP"}}
        assert evaluate_filter(rpn, packet) is False

        # Node C sending text (should not match)
        packet = {
            "fromId": "C",
            "toId": "B",
            "decoded": {"portnum": "TEXT_MESSAGE_APP"},
        }
        assert evaluate_filter(rpn, packet) is False

    def test_encrypted_high_hop_limit_filter(self):
        """Test filter for encrypted packets with high hop limit."""
        expression = ["encrypted", "and", "hop_limit", ">", "5"]
        rpn = parse_filter(expression)

        # Encrypted packet with high hop limit
        packet = {
            "encrypted": b"encrypted_data",
            "hopLimit": 7,
            "fromId": "nodeA",
            "toId": "nodeB",
        }
        assert evaluate_filter(rpn, packet) is True

        # Encrypted packet with low hop limit
        packet["hopLimit"] = 3
        assert evaluate_filter(rpn, packet) is False

        # Plaintext packet with high hop limit
        packet = {
            "decoded": {"portnum": "TEXT_MESSAGE_APP"},
            "hopLimit": 7,
            "fromId": "nodeA",
            "toId": "nodeB",
        }
        assert evaluate_filter(rpn, packet) is False
