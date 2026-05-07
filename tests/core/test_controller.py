import pytest
from core.controller import SystemController
from core.models import SystemState, SystemMode
from hardware.mock_adapter import MockAdapter

def test_controller_initial_state():
    adapter = MockAdapter()
    controller = SystemController(adapter)
    assert controller.mode == SystemMode.OFF

def test_controller_start_stop():
    adapter = MockAdapter()
    controller = SystemController(adapter)
    emitted_states = []
    
    controller.state_changed.connect(lambda state: emitted_states.append(state))
    
    controller.start()
    assert controller.mode == SystemMode.AUTO
    assert len(emitted_states) == 1
    assert emitted_states[-1].mode == SystemMode.AUTO
    assert emitted_states[-1].heater_on is True  # При старте ТЭН включается
    assert emitted_states[-1].valve_open is False

    controller.stop()
    assert controller.mode == SystemMode.OFF
    assert len(emitted_states) == 2
    assert emitted_states[-1].mode == SystemMode.OFF
    assert emitted_states[-1].heater_on is False

def test_controller_set_mode():
    adapter = MockAdapter()
    controller = SystemController(adapter)
    emitted_states = []
    controller.state_changed.connect(lambda state: emitted_states.append(state))

    controller.start()
    controller.set_mode(SystemMode.MANUAL)
    
    assert controller.mode == SystemMode.MANUAL
    assert emitted_states[-1].mode == SystemMode.MANUAL

def test_controller_manual_relay():
    adapter = MockAdapter()
    controller = SystemController(adapter)
    emitted_states = []
    controller.state_changed.connect(lambda state: emitted_states.append(state))
    
    controller.set_mode(SystemMode.MANUAL)

    controller.set_relay("heater", True)
    assert emitted_states[-1].heater_on is True
    
    controller.set_relay("valve", True)
    assert emitted_states[-1].valve_open is True
