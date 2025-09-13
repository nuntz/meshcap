"""Test constants module."""

import pytest
from meshcap import constants


class TestConstants:
    """Test that constants are properly defined."""

    def test_port_constants_exist(self):
        """Test that all port constants are defined."""
        assert hasattr(constants, "TEXT_MESSAGE_APP")
        assert hasattr(constants, "POSITION_APP")
        assert hasattr(constants, "NODEINFO_APP")
        assert hasattr(constants, "ROUTING_APP")
        assert hasattr(constants, "ADMIN_APP")
        assert hasattr(constants, "TELEMETRY_APP")

    def test_network_constants_exist(self):
        """Test that network constants are defined."""
        assert hasattr(constants, "DEFAULT_SERIAL_PORT")
        assert hasattr(constants, "DEFAULT_TCP_PORT")
        assert constants.DEFAULT_SERIAL_PORT == "/dev/ttyACM0"
        assert constants.DEFAULT_TCP_PORT == 4403

    def test_timing_constants_exist(self):
        """Test that timing constants are defined."""
        assert hasattr(constants, "SLEEP_INTERVAL")
        assert constants.SLEEP_INTERVAL == 0.1

    def test_node_id_constants_exist(self):
        """Test that node ID constants are defined."""
        assert hasattr(constants, "NODE_ID_MASK")
        assert hasattr(constants, "BROADCAST_ADDRESS")
        assert constants.NODE_ID_MASK == 0xFFFFFFFF
        assert constants.BROADCAST_ADDRESS == 0xFFFFFFFF

    def test_precision_constants_exist(self):
        """Test that precision constants are defined."""
        assert hasattr(constants, "POSITION_PRECISION")
        assert hasattr(constants, "ALTITUDE_PRECISION")
        assert hasattr(constants, "TEMPERATURE_PRECISION")
        assert hasattr(constants, "VOLTAGE_PRECISION")

        assert constants.POSITION_PRECISION == 4
        assert constants.ALTITUDE_PRECISION == 0
        assert constants.TEMPERATURE_PRECISION == 1
        assert constants.VOLTAGE_PRECISION == 2

    def test_constants_have_correct_types(self):
        """Test that constants have the expected types."""
        assert isinstance(constants.DEFAULT_SERIAL_PORT, str)
        assert isinstance(constants.DEFAULT_TCP_PORT, int)
        assert isinstance(constants.SLEEP_INTERVAL, float)
        assert isinstance(constants.NODE_ID_MASK, int)
        assert isinstance(constants.BROADCAST_ADDRESS, int)
        assert isinstance(constants.POSITION_PRECISION, int)
        assert isinstance(constants.ALTITUDE_PRECISION, int)
        assert isinstance(constants.TEMPERATURE_PRECISION, int)
        assert isinstance(constants.VOLTAGE_PRECISION, int)
