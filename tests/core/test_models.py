import pytest
from core.models import SystemState, SystemMode

def test_system_mode_enum():
    assert SystemMode.OFF.value == "off"
    assert SystemMode.AUTO.value == "auto"
    assert SystemMode.MANUAL.value == "manual"

def test_system_state_defaults():
    state = SystemState()
    assert state.mode == SystemMode.OFF
    assert state.heater_on is False
    assert state.valve_open is False
    assert state.temp_lt == 25.0
    assert state.temp_ht == 30.0
    assert state.temp_ambient == 24.1
    assert state.flow_lt == 0.0
    assert state.flow_ht == 0.0
    assert state.pressure == 0.0
    assert state.water_level == 0.85

def test_system_state_initialization():
    state = SystemState(
        mode=SystemMode.AUTO,
        heater_on=True,
        valve_open=True,
        temp_lt=20.5,
        flow_lt=15.0
    )
    assert state.mode == SystemMode.AUTO
    assert state.heater_on is True
    assert state.valve_open is True
    assert state.temp_lt == 20.5
    assert state.flow_lt == 15.0
