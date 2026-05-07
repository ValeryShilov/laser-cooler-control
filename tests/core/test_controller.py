from core.controller import SystemController
from core.models import SystemState, SystemMode
from hardware.mock_adapter import MockAdapter

def test_controller_initial_state(test_log):
    adapter = MockAdapter()
    controller = SystemController(adapter)
    test_log.check("Режим при создании", controller.mode, SystemMode.OFF)

def test_controller_start_stop(test_log):
    adapter = MockAdapter()
    controller = SystemController(adapter)
    emitted_states = []
    controller.state_changed.connect(lambda state: emitted_states.append(state))

    controller.start()
    test_log.check("Режим после start()", controller.mode, SystemMode.AUTO)
    test_log.check("Количество сигналов после start()", len(emitted_states), 1)
    test_log.check("Режим в сигнале", emitted_states[-1].mode, SystemMode.AUTO)
    test_log.check("ТЭН включен при старте", emitted_states[-1].heater_on, True, op="is")
    test_log.check("Клапан выключен при старте", emitted_states[-1].valve_open, False, op="is")

    controller.stop()
    test_log.check("Режим после stop()", controller.mode, SystemMode.OFF)
    test_log.check("Количество сигналов после stop()", len(emitted_states), 2)
    test_log.check("Режим в сигнале после stop()", emitted_states[-1].mode, SystemMode.OFF)
    test_log.check("ТЭН выключен после stop()", emitted_states[-1].heater_on, False, op="is")

def test_controller_set_mode(test_log):
    adapter = MockAdapter()
    controller = SystemController(adapter)
    emitted_states = []
    controller.state_changed.connect(lambda state: emitted_states.append(state))

    controller.start()
    controller.set_mode(SystemMode.MANUAL)

    test_log.check("Режим контроллера", controller.mode, SystemMode.MANUAL)
    test_log.check("Режим в последнем сигнале", emitted_states[-1].mode, SystemMode.MANUAL)

def test_controller_manual_relay(test_log):
    adapter = MockAdapter()
    controller = SystemController(adapter)
    emitted_states = []
    controller.state_changed.connect(lambda state: emitted_states.append(state))

    controller.set_mode(SystemMode.MANUAL)

    controller.set_relay("heater", True)
    test_log.check("ТЭН включен вручную", emitted_states[-1].heater_on, True, op="is")

    controller.set_relay("valve", True)
    test_log.check("Клапан включен вручную", emitted_states[-1].valve_open, True, op="is")
