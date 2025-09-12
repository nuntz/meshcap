"""Filter expression parser and evaluator for Meshtastic packets.

This module implements a filter engine that allows filtering packets based on various criteria
using logical expressions with 'and', 'or', 'not', and parentheses for precedence.
"""

from typing import List, Union, Tuple, Any, Dict

from meshcap.identifiers import to_node_num
from . import constants


class FilterError(Exception):
    """Exception raised for filter parsing or evaluation errors."""

    pass


class FilterParser:
    """Parser that converts infix filter expressions to Reverse Polish Notation (RPN)."""

    # Operator precedence (higher number = higher precedence)
    PRECEDENCE = {"or": 1, "and": 2, "not": 3}

    # Right-associative operators
    RIGHT_ASSOCIATIVE = {"not"}

    def __init__(self):
        self.tokens = []
        self.position = 0

    def parse(self, expression: List[str]) -> List[Union[Tuple[str, str, str], str]]:
        """Parse an infix expression into RPN using the Shunting-yard algorithm.

        Args:
            expression: List of tokens from command line (e.g., ['src', 'node', 'A', 'and', 'port', 'text'])

        Returns:
            RPN stack as list of primitives (tuples) and operators (strings)

        Raises:
            FilterError: If the expression is malformed
        """
        if not expression:
            return []

        self.tokens = expression
        self.position = 0

        output_queue = []
        operator_stack = []

        while self.position < len(self.tokens):
            token = self._current_token()

            if token in self.PRECEDENCE:
                # Handle operators
                self._handle_operator(token, operator_stack, output_queue)
                self.position += 1
            elif token == "(":
                operator_stack.append(token)
                self.position += 1
            elif token == ")":
                self._handle_closing_paren(operator_stack, output_queue)
                self.position += 1
            else:
                # Handle primitives
                primitive = self._parse_primitive()
                if primitive:
                    output_queue.append(primitive)
                    self.position += 1  # _parse_primitive already advanced to the last token of the primitive
                else:
                    # Unrecognized token
                    raise FilterError(f"Unrecognized token: '{token}'")

        # Pop remaining operators
        while operator_stack:
            op = operator_stack.pop()
            if op in ("(", ")"):
                raise FilterError("Mismatched parentheses")
            output_queue.append(op)

        return output_queue

    def _current_token(self) -> str:
        """Get current token."""
        return self.tokens[self.position] if self.position < len(self.tokens) else ""

    def _peek_token(self, offset: int = 1) -> str:
        """Peek at token at current position + offset."""
        pos = self.position + offset
        return self.tokens[pos] if pos < len(self.tokens) else ""

    def _handle_operator(
        self, token: str, operator_stack: List[str], output_queue: List[Any]
    ):
        """Handle operator according to Shunting-yard algorithm."""
        while (
            operator_stack
            and operator_stack[-1] != "("
            and operator_stack[-1] in self.PRECEDENCE
            and (
                self.PRECEDENCE[operator_stack[-1]] > self.PRECEDENCE[token]
                or (
                    self.PRECEDENCE[operator_stack[-1]] == self.PRECEDENCE[token]
                    and token not in self.RIGHT_ASSOCIATIVE
                )
            )
        ):
            output_queue.append(operator_stack.pop())
        operator_stack.append(token)

    def _handle_closing_paren(self, operator_stack: List[str], output_queue: List[Any]):
        """Handle closing parenthesis."""
        while operator_stack and operator_stack[-1] != "(":
            output_queue.append(operator_stack.pop())

        if not operator_stack:
            raise FilterError("Mismatched parentheses")

        operator_stack.pop()  # Remove the '('

    def _parse_primitive(self) -> Union[Tuple[str, str, str], None]:
        """Parse a filter primitive from current position.

        Returns:
            Tuple of (primitive_type, field, value) or None if no primitive found
        """
        token = self._current_token()

        if token == "node":
            # node <value>
            if self.position + 1 >= len(self.tokens):
                raise FilterError("'node' primitive requires a value")
            value = self._peek_token()
            self.position += 1  # Advance to value position
            return ("node", "both", value)

        elif token == "user":
            # user <value>
            if self.position + 1 >= len(self.tokens):
                raise FilterError("'user' primitive requires a value")
            value = self._peek_token()
            self.position += 1  # Advance to value position
            return ("user", "both", value)

        elif token in ("src", "dst"):
            # src node <value> or dst node <value> or src user <value> or dst user <value>
            next_token = self._peek_token()
            if next_token == "node":
                if self.position + 2 >= len(self.tokens):
                    raise FilterError(f"'{token} node' primitive requires a value")
                value = self._peek_token(2)
                self.position += 2  # Advance to value position
                return ("node", token, value)
            elif next_token == "user":
                if self.position + 2 >= len(self.tokens):
                    raise FilterError(f"'{token} user' primitive requires a value")
                value = self._peek_token(2)
                self.position += 2  # Advance to value position
                return ("user", token, value)
            else:
                raise FilterError(f"'{token}' must be followed by 'node' or 'user'")

        elif token == "port":
            # port <value>
            if self.position + 1 >= len(self.tokens):
                raise FilterError("'port' primitive requires a value")
            value = self._peek_token()
            self.position += 1  # Advance to value position
            return ("port", "portnum", value)

        elif token == "hop_limit":
            # hop_limit <op> <value>
            if self.position + 2 >= len(self.tokens):
                raise FilterError("'hop_limit' primitive requires operator and value")
            op = self._peek_token()
            value = self._peek_token(2)
            if op not in ("<", ">", "="):
                raise FilterError(f"Invalid hop_limit operator: {op}")
            self.position += 2  # Advance to value position
            return ("hop_limit", op, value)

        elif token == "priority":
            # priority <value>
            if self.position + 1 >= len(self.tokens):
                raise FilterError("'priority' primitive requires a value")
            value = self._peek_token()
            self.position += 1  # Advance to value position
            return ("priority", "priority", value)

        elif token == "want_ack":
            # want_ack (no value needed)
            return ("want_ack", "wantAck", "true")

        elif token in ("is", "encrypted", "plaintext"):
            # Handle "is encrypted" and "is plaintext"
            if token == "is":
                next_token = self._peek_token()
                if next_token == "encrypted":
                    self.position += 1  # Advance to 'encrypted' position
                    return ("encryption", "status", "encrypted")
                elif next_token == "plaintext":
                    self.position += 1  # Advance to 'plaintext' position
                    return ("encryption", "status", "plaintext")
                else:
                    raise FilterError(
                        f"'is' must be followed by 'encrypted' or 'plaintext', got '{next_token}'"
                    )
            elif token == "encrypted":
                return ("encryption", "status", "encrypted")
            elif token == "plaintext":
                return ("encryption", "status", "plaintext")

        return None


class FilterEvaluator:
    """Evaluates RPN filter expressions against packet data."""

    def evaluate_rpn(
        self,
        rpn_stack: List[Union[Tuple[str, str, str], str]],
        packet: Dict[str, Any],
        interface: Any = None,
    ) -> bool:
        """Evaluate an RPN expression against a packet.

        Args:
            rpn_stack: RPN expression from parser
            packet: Packet dictionary to evaluate
            interface: Optional Meshtastic interface object

        Returns:
            True if packet matches filter, False otherwise

        Raises:
            FilterError: If evaluation fails
        """
        if not rpn_stack:
            return True  # Empty filter matches everything

        eval_stack = []

        for item in rpn_stack:
            if isinstance(item, tuple):
                # Primitive - evaluate and push result
                result = self._evaluate_primitive(item, packet, interface)
                eval_stack.append(result)
            elif item == "and":
                if len(eval_stack) < 2:
                    raise FilterError("'and' operator requires two operands")
                b = eval_stack.pop()
                a = eval_stack.pop()
                eval_stack.append(a and b)
            elif item == "or":
                if len(eval_stack) < 2:
                    raise FilterError("'or' operator requires two operands")
                b = eval_stack.pop()
                a = eval_stack.pop()
                eval_stack.append(a or b)
            elif item == "not":
                if len(eval_stack) < 1:
                    raise FilterError("'not' operator requires one operand")
                a = eval_stack.pop()
                eval_stack.append(not a)
            else:
                raise FilterError(f"Unknown operator or primitive: {item}")

        if len(eval_stack) != 1:
            raise FilterError(
                "Invalid expression - evaluation stack should contain exactly one result"
            )

        return eval_stack[0]

    def _evaluate_primitive(
        self,
        primitive: Tuple[str, str, str],
        packet: Dict[str, Any],
        interface: Any = None,
    ) -> bool:
        """Evaluate a single primitive against a packet.

        Args:
            primitive: Tuple of (primitive_type, field, value)
            packet: Packet dictionary
            interface: Optional Meshtastic interface object

        Returns:
            True if primitive matches, False otherwise
        """
        prim_type, field, value = primitive

        if prim_type == "node":
            return self._eval_node(field, value, packet)
        elif prim_type == "user":
            return self._eval_user(field, value, packet, interface)
        elif prim_type == "port":
            return self._eval_port(value, packet)
        elif prim_type == "hop_limit":
            return self._eval_hop_limit(field, value, packet)
        elif prim_type == "priority":
            return self._eval_priority(value, packet)
        elif prim_type == "want_ack":
            return self._eval_want_ack(packet)
        elif prim_type == "encryption":
            return self._eval_encryption(value, packet)
        else:
            raise FilterError(f"Unknown primitive type: {prim_type}")

    def _eval_node(self, field: str, value: str, packet: Dict[str, Any]) -> bool:
        """Evaluate node primitive."""
        # Get node IDs from packet, checking both new and legacy field names
        from_id = packet.get("fromId") or packet.get("from") or ""
        to_id = packet.get("toId") or packet.get("to") or ""

        # Convert to canonical representations - handle ValueError for invalid formats
        try:
            from_n = to_node_num(from_id)
            to_n = to_node_num(to_id)
            val_n = to_node_num(value)
        except ValueError:
            # If any conversion fails, the filter doesn't match
            return False

        if field == "src":
            return from_n == val_n
        elif field == "dst":
            return to_n == val_n
        elif field == "both":
            return from_n == val_n or to_n == val_n

        return False

    def _eval_user(
        self, field: str, value: str, packet: Dict[str, Any], interface: Any
    ) -> bool:
        """Evaluate user primitive."""
        # Return False if interface or interface.nodes is not available
        if not interface or not hasattr(interface, "nodes") or not interface.nodes:
            return False

        from_id = packet.get("fromId", "")
        to_id = packet.get("toId", "")

        def check_user_match(node_id: str) -> bool:
            """Check if a node ID matches the user filter value."""
            if not node_id or node_id not in interface.nodes:
                return False

            node_info = interface.nodes[node_id]
            user_info = node_info.get("user", {})
            if not user_info:
                return False

            # Check both possible field names for long and short names
            long_name = user_info.get("longName", "") or user_info.get("long_name", "")
            short_name = user_info.get("shortName", "") or user_info.get(
                "short_name", ""
            )

            return long_name == value or short_name == value

        if field == "src":
            return check_user_match(from_id)
        elif field == "dst":
            return check_user_match(to_id)
        elif field == "both":
            return check_user_match(from_id) or check_user_match(to_id)

        return False

    def _eval_port(self, value: str, packet: Dict[str, Any]) -> bool:
        """Evaluate port primitive."""
        decoded = packet.get("decoded", {})
        portnum = decoded.get("portnum", "")

        # Handle common port names
        port_mapping = {
            "text": constants.TEXT_MESSAGE_APP,
            "position": constants.POSITION_APP,
            "nodeinfo": constants.NODEINFO_APP,
            "routing": constants.ROUTING_APP,
            "admin": constants.ADMIN_APP,
            "telemetry": constants.TELEMETRY_APP,
        }

        expected_port = port_mapping.get(value.lower(), value)
        return portnum == expected_port

    def _eval_hop_limit(self, op: str, value: str, packet: Dict[str, Any]) -> bool:
        """Evaluate hop_limit primitive."""
        try:
            target_value = int(value)
        except ValueError:
            raise FilterError(f"Invalid hop_limit value: {value}")

        hop_limit = packet.get("hopLimit", 0)

        if op == "<":
            return hop_limit < target_value
        elif op == ">":
            return hop_limit > target_value
        elif op == "=":
            return hop_limit == target_value

        return False

    def _eval_priority(self, value: str, packet: Dict[str, Any]) -> bool:
        """Evaluate priority primitive."""
        priority = packet.get("priority", "UNSET")
        return priority == value.upper()

    def _eval_want_ack(self, packet: Dict[str, Any]) -> bool:
        """Evaluate want_ack primitive."""
        return packet.get("wantAck", False)

    def _eval_encryption(self, value: str, packet: Dict[str, Any]) -> bool:
        """Evaluate encryption status primitive."""
        has_decoded = "decoded" in packet and packet["decoded"]
        has_encrypted = "encrypted" in packet and packet["encrypted"]

        if value == "encrypted":
            return has_encrypted and not has_decoded
        elif value == "plaintext":
            return has_decoded and not has_encrypted

        return False


# Convenience functions for main module
def parse_filter(expression: List[str]) -> List[Union[Tuple[str, str, str], str]]:
    """Parse a filter expression into RPN format.

    Args:
        expression: List of tokens from command line

    Returns:
        RPN stack

    Raises:
        FilterError: If parsing fails
    """
    parser = FilterParser()
    return parser.parse(expression)


def evaluate_filter(
    rpn_stack: List[Union[Tuple[str, str, str], str]],
    packet: Dict[str, Any],
    interface: Any = None,
) -> bool:
    """Evaluate an RPN filter expression against a packet.

    Args:
        rpn_stack: RPN expression from parse_filter()
        packet: Packet dictionary to evaluate
        interface: Optional Meshtastic interface object

    Returns:
        True if packet matches filter, False otherwise

    Raises:
        FilterError: If evaluation fails
    """
    evaluator = FilterEvaluator()
    return evaluator.evaluate_rpn(rpn_stack, packet, interface)
