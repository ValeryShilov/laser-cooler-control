import pytest
from hardware.mock_adapter import MockAdapter

def test_mock_adapter_initial_state():
    adapter = MockAdapter()
    assert adapter.get_relay('pump') is False
    assert adapter.get_relay('compressor') is False
    assert adapter.get_relay('heater') is False
    assert adapter.get_relay('valve') is False
    assert adapter.get_relay('fan') is False

def test_mock_adapter_set_get_relay():
    adapter = MockAdapter()
    adapter.set_relay('pump', True)
    assert adapter.get_relay('pump') is True
    
    # Check invalid relay
    adapter.set_relay('invalid_relay', True)
    assert adapter.get_relay('invalid_relay') is False

def test_mock_adapter_sensors_running():
    adapter = MockAdapter()
    
    # State when off
    sensors_off = adapter.read_sensors()
    assert sensors_off['flow_lt'] == 0.0
    assert sensors_off['flow_ht'] == 0.0
    assert sensors_off['pressure'] == 0.0
    assert sensors_off['temp_ambient'] == 24.1
    
    # State when running (pump is on)
    adapter.set_relay('pump', True)
    sensors_on = adapter.read_sensors()
    assert sensors_on['flow_lt'] > 0.0
    assert sensors_on['flow_ht'] > 0.0
    assert sensors_on['pressure'] > 0.0
    assert sensors_on['temp_ambient'] == 25.2
