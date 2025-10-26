import pytest
from unittest.mock import MagicMock


def test_block_catflap(mock_gpiozero):
    from catflap_prey_detector.hardware import rfid_jammer
    
    rfid_jammer.relay = mock_gpiozero
    rfid_jammer.block_catflap()
    
    expected_call_count = 1
    assert mock_gpiozero.on.call_count == expected_call_count


def test_unblock_catflap(mock_gpiozero):
    from catflap_prey_detector.hardware import rfid_jammer
    
    rfid_jammer.relay = mock_gpiozero
    rfid_jammer.unblock_catflap()
    
    expected_call_count = 1
    assert mock_gpiozero.off.call_count == expected_call_count

