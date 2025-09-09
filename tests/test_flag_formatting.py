from unittest.mock import Mock

from meshcap.main import MeshCap


class TestFlagFormatting:
    def setup_method(self):
        mock_args = Mock()
        mock_args.label_mode = "named-with-hex"
        self.capture = MeshCap(mock_args)

    def test_want_ack_true_via_mqtt_false(self):
        packet = {"wantAck": True, "viaMqtt": False}
        assert self.capture._format_flags(packet) == " [A]"

    def test_want_ack_false_via_mqtt_true(self):
        packet = {"wantAck": False, "viaMqtt": True}
        assert self.capture._format_flags(packet) == " [M]"

    def test_both_flags_true(self):
        packet = {"wantAck": True, "viaMqtt": True}
        assert self.capture._format_flags(packet) == " [AM]"

    def test_both_flags_false(self):
        packet = {"wantAck": False, "viaMqtt": False}
        assert self.capture._format_flags(packet) == ""

    def test_empty_packet(self):
        packet = {}
        assert self.capture._format_flags(packet) == ""

    def test_missing_want_ack_key(self):
        packet = {"viaMqtt": True}
        assert self.capture._format_flags(packet) == " [M]"

    def test_missing_via_mqtt_key(self):
        packet = {"wantAck": True}
        assert self.capture._format_flags(packet) == " [A]"

