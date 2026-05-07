from core.models import SystemState, SystemMode

def test_system_mode_enum(test_log):
    test_log.check("SystemMode.OFF", SystemMode.OFF.value, "off")
    test_log.check("SystemMode.AUTO", SystemMode.AUTO.value, "auto")
    test_log.check("SystemMode.MANUAL", SystemMode.MANUAL.value, "manual")

def test_system_state_defaults(test_log):
    state = SystemState()
    test_log.check("Режим по умолчанию", state.mode, SystemMode.OFF)
    test_log.check("ТЭН по умолчанию", state.heater_on, False, op="is")
    test_log.check("Клапан по умолчанию", state.valve_open, False, op="is")
    test_log.check("Температура LT", state.temp_lt, 25.0)
    test_log.check("Температура HT", state.temp_ht, 30.0)
    test_log.check("Температура воздуха", state.temp_ambient, 24.1)
    test_log.check("Проток LT", state.flow_lt, 0.0)
    test_log.check("Проток HT", state.flow_ht, 0.0)
    test_log.check("Давление", state.pressure, 0.0)
    test_log.check("Уровень воды", state.water_level, 0.85)

def test_system_state_initialization(test_log):
    state = SystemState(
        mode=SystemMode.AUTO,
        heater_on=True,
        valve_open=True,
        temp_lt=20.5,
        flow_lt=15.0
    )
    test_log.check("Режим", state.mode, SystemMode.AUTO)
    test_log.check("ТЭН", state.heater_on, True, op="is")
    test_log.check("Клапан", state.valve_open, True, op="is")
    test_log.check("Температура LT", state.temp_lt, 20.5)
    test_log.check("Проток LT", state.flow_lt, 15.0)
