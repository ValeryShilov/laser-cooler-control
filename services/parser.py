import yaml
import os

# Импортируем нашу библиотеку компонентов
from ui.equipment import (
    Compressor, Condenser, Fan, Throttle, Valve, 
    Pump, Heater, Tank, ExternalPort
)

# Словарь для перевода текстового 'type' из YAML в реальный Python-класс
CLASS_MAP = {
    "Compressor": Compressor,
    "Condenser": Condenser,
    "Fan": Fan,
    "Throttle": Throttle,
    "Valve": Valve,
    "Pump": Pump,
    "Heater": Heater,
    "Tank": Tank,
    "ExternalPort": ExternalPort
}

class SchemeParser:
    def __init__(self, filepath="scheme.yaml"):
        self.filepath = filepath
        self.components = {}  # Словарь { 'id_компонента': Объект }
        self.connections = [] # Список связей

    def parse(self):
        """ Основной метод чтения и создания объектов """
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Файл схемы {self.filepath} не найден!")

        with open(self.filepath, 'r', encoding='utf-8') as file:
            data = yaml.safe_load(file)

        self._parse_components(data.get('components', []))
        self._parse_connections(data.get('connections', []))

        return self.components, self.connections

    def _parse_components(self, comp_list):
        """ Создает Python-объекты из списка компонентов YAML """
        for comp_data in comp_list:
            comp_id = comp_data['id']
            comp_type = comp_data['type']
            comp_name = comp_data.get('name', 'Без названия')
            grid_pos = comp_data.get('grid', [0, 0])

            # Ищем класс в нашем словаре
            CompClass = CLASS_MAP.get(comp_type)
            if CompClass:
                # Создаем объект. Координаты (0, 0), так как их потом задаст layout.py
                instance = CompClass(0, 0)
                instance.id = comp_id       # Сохраняем ID внутрь объекта
                instance.name = comp_name   # Перезаписываем стандартное имя из YAML
                instance.grid = grid_pos
                
                # Добавляем в словарь созданных компонентов
                self.components[comp_id] = instance
            else:
                print(f"ПРЕДУПРЕЖДЕНИЕ: Неизвестный тип компонента '{comp_type}' для ID '{comp_id}'")

    def _parse_connections(self, conn_list):
        """ Разбирает связи и порты """
        for conn_data in conn_list:
            source_str = conn_data['source']
            target_str = conn_data['target']
            conn_type = conn_data.get('type', 'freon')

            # Разделяем "comp_1.out" на компонент и порт
            source_id, source_port = self._split_port_string(source_str)
            target_id, target_port = self._split_port_string(target_str)

            self.connections.append({
                'source_id': source_id,
                'source_port': source_port,
                'target_id': target_id,
                'target_port': target_port,
                'type': conn_type
            })

    def _split_port_string(self, port_string):
        if '.' in port_string:
            parts = port_string.split('.')
            return parts[0], parts[1]
        return port_string, None

# ==========================================
# Блок для тестирования парсера (можно запускать этот файл отдельно)
# ==========================================
if __name__ == "__main__":
    parser = SchemeParser("scheme.yaml")
    components, connections = parser.parse()
    
    print(f"✅ Успешно загружено компонентов: {len(components)}")
    for cid, comp in components.items():
        print(f"  - [{cid}] -> {type(comp).__name__} ('{comp.name}')")
        
    print(f"\n✅ Успешно загружено связей: {len(connections)}")
    for conn in connections:
        src = f"{conn['source_id']}.{conn['source_port']}" if conn['source_port'] else conn['source_id']
        tgt = f"{conn['target_id']}.{conn['target_port']}" if conn['target_port'] else conn['target_id']
        print(f"  - {src} ---> {tgt} (Среда: {conn['type']})")