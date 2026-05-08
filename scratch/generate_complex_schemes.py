import os
import yaml
import re

out_dir = 'tests/test_data/schemes'
os.makedirs(out_dir, exist_ok=True)

schemes = {
    'scheme_01_simple_freon.yaml': {
        'components': [
            {'id': 'comp', 'type': 'Compressor', 'name': 'Главный компрессор'},
            {'id': 'cond', 'type': 'Condenser', 'name': 'Охлаждающий конденсатор'},
            {'id': 'thr', 'type': 'Throttle', 'name': 'Электронный дроссель'},
            {'id': 'evap', 'type': 'Tank', 'name': 'Бак испарителя'}
        ],
        'connections': [
            {'source': 'comp.out', 'target': 'cond.in', 'type': 'freon'},
            {'source': 'cond.out', 'target': 'thr.in', 'type': 'freon'},
            {'source': 'thr.out', 'target': 'evap.freon_in', 'type': 'freon'},
            {'source': 'evap.freon_out', 'target': 'comp.in', 'type': 'freon'}
        ]
    },
    'scheme_02_simple_water.yaml': {
        'components': [
            {'id': 'tank', 'type': 'Tank', 'name': 'Резервуар для воды'},
            {'id': 'pump', 'type': 'Pump', 'name': 'Циркуляционный насос'},
            {'id': 'port_in', 'type': 'ExternalPort', 'name': 'Возврат воды от клиента'},
            {'id': 'port_out', 'type': 'ExternalPort', 'name': 'Подача воды клиенту'}
        ],
        'connections': [
            {'source': 'port_in.out', 'target': 'tank.water_lt_in', 'type': 'water_lt'},
            {'source': 'tank.water_out', 'target': 'pump.in', 'type': 'water_lt'},
            {'source': 'pump.out', 'target': 'port_out.in', 'type': 'water_lt'}
        ]
    },
    'scheme_03_two_pumps.yaml': {
        'components': [
            {'id': 'tank', 'type': 'Tank', 'name': 'Накопительная емкость'},
            {'id': 'pump1', 'type': 'Pump', 'name': 'Насос охлаждения лазера'},
            {'id': 'pump2', 'type': 'Pump', 'name': 'Насос охлаждения оптики'},
            {'id': 'port_in', 'type': 'ExternalPort', 'name': 'Входная магистраль'},
            {'id': 'port_out', 'type': 'ExternalPort', 'name': 'Выходная магистраль'}
        ],
        'connections': [
            {'source': 'port_in.out', 'target': 'tank.water_lt_in', 'type': 'water_lt'},
            {'source': 'tank.water_out', 'target': 'pump1.in', 'type': 'water_lt'},
            {'source': 'tank.water_out', 'target': 'pump2.in', 'type': 'water_lt'},
            {'source': 'pump1.out', 'target': 'port_out.in', 'type': 'water_lt'},
            {'source': 'pump2.out', 'target': 'port_out.in', 'type': 'water_lt'}
        ]
    },
    'scheme_04_no_bypass.yaml': {
        'components': [
            {'id': 'comp', 'type': 'Compressor', 'name': 'Компрессор без байпаса'}, 
            {'id': 'cond', 'type': 'Condenser', 'name': 'Радиатор конденсатора'},
            {'id': 'thr', 'type': 'Throttle', 'name': 'Клапан ТРВ'}, 
            {'id': 'tank', 'type': 'Tank', 'name': 'Бак-испаритель'},
            {'id': 'pump', 'type': 'Pump', 'name': 'Рабочий насос'}, 
            {'id': 'fan', 'type': 'Fan', 'name': 'Осевой вентилятор'},
            {'id': 'pin', 'type': 'ExternalPort', 'name': 'Вход'}, 
            {'id': 'pout', 'type': 'ExternalPort', 'name': 'Выход'}
        ],
        'connections': [
            {'source': 'comp.out', 'target': 'cond.in', 'type': 'freon'},
            {'source': 'cond.out', 'target': 'thr.in', 'type': 'freon'},
            {'source': 'thr.out', 'target': 'tank.freon_in', 'type': 'freon'},
            {'source': 'tank.freon_out', 'target': 'comp.in', 'type': 'freon'},
            {'source': 'fan.out', 'target': 'cond.in', 'type': 'mechanical'},
            {'source': 'pin.out', 'target': 'tank.water_lt_in', 'type': 'water_lt'},
            {'source': 'tank.water_out', 'target': 'pump.in', 'type': 'water_lt'},
            {'source': 'pump.out', 'target': 'pout.in', 'type': 'water_lt'}
        ]
    },
    'scheme_05_two_fans.yaml': {
        'components': [
            {'id': 'cond', 'type': 'Condenser', 'name': 'Двойной конденсатор'},
            {'id': 'fan1', 'type': 'Fan', 'name': 'Левый вентилятор'},
            {'id': 'fan2', 'type': 'Fan', 'name': 'Правый вентилятор'}
        ],
        'connections': [
            {'source': 'fan1.out', 'target': 'cond.in', 'type': 'mechanical'},
            {'source': 'fan2.out', 'target': 'cond.in', 'type': 'mechanical'}
        ]
    },
    'scheme_06_water_ht_only.yaml': {
        'components': [
            {'id': 'tank', 'type': 'Tank', 'name': 'Бак горячего контура'},
            {'id': 'heater', 'type': 'Heater', 'name': 'Электрический нагреватель'},
            {'id': 'pump', 'type': 'Pump', 'name': 'Циркуляционный насос HT'},
            {'id': 'port_ht_in', 'type': 'ExternalPort', 'name': 'Возврат от оптики'},
            {'id': 'port_ht_out', 'type': 'ExternalPort', 'name': 'Подача на оптику'}
        ],
        'connections': [
            {'source': 'port_ht_in.out', 'target': 'tank.water_ht_in', 'type': 'water_ht'},
            {'source': 'tank.water_out', 'target': 'pump.in', 'type': 'water_ht'},
            {'source': 'pump.out', 'target': 'heater.in', 'type': 'water_ht'},
            {'source': 'heater.out', 'target': 'port_ht_out.in', 'type': 'water_ht'}
        ]
    },
    'scheme_11_dual_compressor.yaml': {
        'components': [
            {'id': 'comp1', 'type': 'Compressor', 'name': 'Основной компрессор'},
            {'id': 'comp2', 'type': 'Compressor', 'name': 'Резервный компрессор'},
            {'id': 'cond_main', 'type': 'Condenser', 'name': 'Блок конденсатора'},
            {'id': 'fan_1', 'type': 'Fan', 'name': 'Вентилятор охлаждения 1'},
            {'id': 'fan_2', 'type': 'Fan', 'name': 'Вентилятор охлаждения 2'},
            {'id': 'thr1', 'type': 'Throttle', 'name': 'Дроссель контура А'},
            {'id': 'thr2', 'type': 'Throttle', 'name': 'Дроссель контура Б'},
            {'id': 'tank_main', 'type': 'Tank', 'name': 'Накопительный бак (Испаритель)'},
            {'id': 'pump_1', 'type': 'Pump', 'name': 'Насос подачи воды'},
            {'id': 'port_in', 'type': 'ExternalPort', 'name': 'Вход охлаждающей жидкости'},
            {'id': 'port_out', 'type': 'ExternalPort', 'name': 'Выход охлаждающей жидкости'}
        ],
        'connections': [
            {'source': 'comp1.out', 'target': 'cond_main.in', 'type': 'freon'},
            {'source': 'comp2.out', 'target': 'cond_main.in', 'type': 'freon'},
            {'source': 'cond_main.out', 'target': 'thr1.in', 'type': 'freon'},
            {'source': 'cond_main.out', 'target': 'thr2.in', 'type': 'freon'},
            {'source': 'thr1.out', 'target': 'tank_main.freon_in', 'type': 'freon'},
            {'source': 'thr2.out', 'target': 'tank_main.freon_in', 'type': 'freon'},
            {'source': 'tank_main.freon_out', 'target': 'comp1.in', 'type': 'freon'},
            {'source': 'tank_main.freon_out', 'target': 'comp2.in', 'type': 'freon'},
            {'source': 'fan_1.out', 'target': 'cond_main.in', 'type': 'mechanical'},
            {'source': 'fan_2.out', 'target': 'cond_main.in', 'type': 'mechanical'},
            {'source': 'port_in.out', 'target': 'tank_main.water_lt_in', 'type': 'water_lt'},
            {'source': 'tank_main.water_out', 'target': 'pump_1.in', 'type': 'water_lt'},
            {'source': 'pump_1.out', 'target': 'port_out.in', 'type': 'water_lt'}
        ]
    },
    'scheme_12_double_water_circuit.yaml': {
        'components': [
            {'id': 'tank', 'type': 'Tank', 'name': 'Основной бак'},
            {'id': 'pump_lt', 'type': 'Pump', 'name': 'Насос контура лазера (L)'},
            {'id': 'pump_ht', 'type': 'Pump', 'name': 'Насос контура оптики (H)'},
            {'id': 'heater_ht', 'type': 'Heater', 'name': 'ТЭН подогрева оптики'},
            {'id': 'port_lt_in', 'type': 'ExternalPort', 'name': 'Вход (от лазера)'},
            {'id': 'port_lt_out', 'type': 'ExternalPort', 'name': 'Выход (на лазер)'},
            {'id': 'port_ht_in', 'type': 'ExternalPort', 'name': 'Вход (от оптики)'},
            {'id': 'port_ht_out', 'type': 'ExternalPort', 'name': 'Выход (на оптику)'}
        ],
        'connections': [
            {'source': 'port_lt_in.out', 'target': 'tank.water_lt_in', 'type': 'water_lt'},
            {'source': 'tank.water_out', 'target': 'pump_lt.in', 'type': 'water_lt'},
            {'source': 'pump_lt.out', 'target': 'port_lt_out.in', 'type': 'water_lt'},
            {'source': 'port_ht_in.out', 'target': 'tank.water_ht_in', 'type': 'water_ht'},
            {'source': 'tank.water_out', 'target': 'pump_ht.in', 'type': 'water_ht'},
            {'source': 'pump_ht.out', 'target': 'heater_ht.in', 'type': 'water_ht'},
            {'source': 'heater_ht.out', 'target': 'port_ht_out.in', 'type': 'water_ht'}
        ]
    },
    'scheme_13_cascade_freon.yaml': {
        'components': [
            {'id': 'comp_low', 'type': 'Compressor', 'name': 'Компрессор низкого давления'},
            {'id': 'cond_mid', 'type': 'Condenser', 'name': 'Промежуточный охладитель'},
            {'id': 'comp_high', 'type': 'Compressor', 'name': 'Компрессор высокого давления'},
            {'id': 'cond_main', 'type': 'Condenser', 'name': 'Главный конденсатор'},
            {'id': 'thr', 'type': 'Throttle', 'name': 'ТРВ'},
            {'id': 'evap', 'type': 'Tank', 'name': 'Бак-испаритель'}
        ],
        'connections': [
            {'source': 'comp_low.out', 'target': 'cond_mid.in', 'type': 'freon'},
            {'source': 'cond_mid.out', 'target': 'comp_high.in', 'type': 'freon'},
            {'source': 'comp_high.out', 'target': 'cond_main.in', 'type': 'freon'},
            {'source': 'cond_main.out', 'target': 'thr.in', 'type': 'freon'},
            {'source': 'thr.out', 'target': 'evap.freon_in', 'type': 'freon'},
            {'source': 'evap.freon_out', 'target': 'comp_low.in', 'type': 'freon'}
        ]
    },
    'scheme_14_complex_bypass.yaml': {
        'components': [
            {'id': 'comp', 'type': 'Compressor', 'name': 'Спиральный компрессор'},
            {'id': 'cond', 'type': 'Condenser', 'name': 'Микроканальный конденсатор'},
            {'id': 'fan', 'type': 'Fan', 'name': 'Осевой вентилятор'},
            {'id': 'thr', 'type': 'Throttle', 'name': 'Электронный ТРВ'},
            {'id': 'valve1', 'type': 'Valve', 'name': 'Байпас горячего газа (10%)'},
            {'id': 'valve2', 'type': 'Valve', 'name': 'Байпас горячего газа (50%)'},
            {'id': 'evap', 'type': 'Tank', 'name': 'Пластинчатый испаритель'}
        ],
        'connections': [
            {'source': 'comp.out', 'target': 'cond.in', 'type': 'freon'},
            {'source': 'cond.out', 'target': 'thr.in', 'type': 'freon'},
            {'source': 'thr.out', 'target': 'evap.freon_in', 'type': 'freon'},
            {'source': 'evap.freon_out', 'target': 'comp.in', 'type': 'freon'},
            {'source': 'comp.out', 'target': 'valve1.in', 'type': 'freon_bypass'},
            {'source': 'valve1.out', 'target': 'evap.freon_in', 'type': 'freon_bypass'},
            {'source': 'comp.out', 'target': 'valve2.in', 'type': 'freon_bypass'},
            {'source': 'valve2.out', 'target': 'evap.freon_in', 'type': 'freon_bypass'},
            {'source': 'fan.out', 'target': 'cond.in', 'type': 'mechanical'}
        ]
    },
    'scheme_15_full_facility.yaml': {
        'components': [
            {'id': 'comp', 'type': 'Compressor', 'name': 'Центробежный компрессор'},
            {'id': 'cond', 'type': 'Condenser', 'name': 'Промышленный конденсатор'},
            {'id': 'thr', 'type': 'Throttle', 'name': 'Расширительный клапан'},
            {'id': 'tank_evap', 'type': 'Tank', 'name': 'Главный испарительный бак'},
            {'id': 'pump_circ', 'type': 'Pump', 'name': 'Насос рециркуляции'},
            {'id': 'pump_out', 'type': 'Pump', 'name': 'Насос подачи потребителю'},
            {'id': 'heater', 'type': 'Heater', 'name': 'Система преднагрева'},
            {'id': 'drain_valve', 'type': 'Valve', 'name': 'Дренажный клапан'},
            {'id': 'port_water_in', 'type': 'ExternalPort', 'name': 'Подвод воды'},
            {'id': 'port_water_out', 'type': 'ExternalPort', 'name': 'Отвод воды'},
            {'id': 'port_drain', 'type': 'ExternalPort', 'name': 'Слив в канализацию'}
        ],
        'connections': [
            {'source': 'comp.out', 'target': 'cond.in', 'type': 'freon'},
            {'source': 'cond.out', 'target': 'thr.in', 'type': 'freon'},
            {'source': 'thr.out', 'target': 'tank_evap.freon_in', 'type': 'freon'},
            {'source': 'tank_evap.freon_out', 'target': 'comp.in', 'type': 'freon'},
            {'source': 'port_water_in.out', 'target': 'tank_evap.water_lt_in', 'type': 'water_lt'},
            {'source': 'tank_evap.water_out', 'target': 'pump_circ.in', 'type': 'water_lt'},
            {'source': 'pump_circ.out', 'target': 'heater.in', 'type': 'water_lt'},
            {'source': 'heater.out', 'target': 'pump_out.in', 'type': 'water_lt'},
            {'source': 'pump_out.out', 'target': 'port_water_out.in', 'type': 'water_lt'},
            {'source': 'tank_evap.drain', 'target': 'drain_valve.in', 'type': 'drain'},
            {'source': 'drain_valve.out', 'target': 'port_drain.in', 'type': 'drain'}
        ]
    }
}

for filename in os.listdir(out_dir):
    if filename.endswith('.yaml') and not filename.startswith('scheme_'):
        os.remove(os.path.join(out_dir, filename))

for filename, data in schemes.items():
    filepath = os.path.join(out_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)
    
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    text = re.sub(r'name:\s+([^\"\'\n].*)$', r'name: "\1"', text, flags=re.MULTILINE)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(text)
    print(f'Created {filename}')
