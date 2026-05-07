from hardware.mock_adapter import MockAdapter

def test_mock_adapter_initial_state(test_log):
    adapter = MockAdapter()
    test_log.check("Реле pump", adapter.get_relay('pump'), False, op="is")
    test_log.check("Реле compressor", adapter.get_relay('compressor'), False, op="is")
    test_log.check("Реле heater", adapter.get_relay('heater'), False, op="is")
    test_log.check("Реле valve", adapter.get_relay('valve'), False, op="is")
    test_log.check("Реле fan", adapter.get_relay('fan'), False, op="is")

def test_mock_adapter_set_get_relay(test_log):
    adapter = MockAdapter()
    adapter.set_relay('pump', True)
    test_log.check("Реле pump после включения", adapter.get_relay('pump'), True, op="is")

    adapter.set_relay('invalid_relay', True)
    test_log.check("Несуществующее реле", adapter.get_relay('invalid_relay'), False, op="is")

def test_mock_adapter_sensors_running(test_log):
    adapter = MockAdapter()

    sensors_off = adapter.read_sensors()
    test_log.check("Проток LT (выкл)", sensors_off['flow_lt'], 0.0)
    test_log.check("Проток HT (выкл)", sensors_off['flow_ht'], 0.0)
    test_log.check("Давление (выкл)", sensors_off['pressure'], 0.0)
    test_log.check("Температура воздуха (выкл)", sensors_off['temp_ambient'], 24.1)

    adapter.set_relay('pump', True)
    sensors_on = adapter.read_sensors()
    test_log.check("Проток LT (вкл)", sensors_on['flow_lt'], 0.0, op="gt")
    test_log.check("Проток HT (вкл)", sensors_on['flow_ht'], 0.0, op="gt")
    test_log.check("Давление (вкл)", sensors_on['pressure'], 0.0, op="gt")
    test_log.check("Температура воздуха (вкл)", sensors_on['temp_ambient'], 25.2)
