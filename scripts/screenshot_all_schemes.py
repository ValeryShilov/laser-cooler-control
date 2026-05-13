"""
Скрипт для создания скриншотов всех тестовых YAML-схем с отладочной сеткой и bounding box.

Использование:
    python scripts/screenshot_all_schemes.py
    python scripts/screenshot_all_schemes.py --no-debug       # без сетки
    python scripts/screenshot_all_schemes.py --filter pos_full  # только файлы с подстрокой

Результат сохраняется в reports/screenshots/
"""
import sys
import os
import argparse
from pathlib import Path

# Корень проекта — на уровень выше scripts/
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from ui.main_window import ChillerPanel
from ui.mnemonic import ChillerMnemonic
from hardware.mock_adapter import MockAdapter


SCHEMES_DIR = ROOT / "tests" / "test_data" / "schemes"
OUTPUT_DIR = ROOT / "tests" / "test_data" / "schemes_grid"


def render_scheme(app, adapter, yaml_path: Path, output_path: Path, debug: bool):
    """Рендерит одну схему и сохраняет скриншот."""
    window = ChillerPanel(adapter)
    window.resize(1500, 700)
    mnemonic = window.findChild(ChillerMnemonic)

    # Переинициализируем парсер на нужную схему
    mnemonic.parser.__init__(str(yaml_path))

    try:
        mnemonic.components, mnemonic.connections = mnemonic.parser.parse()
    except Exception as e:
        print(f"  ⚠ SKIP (parse error): {e}")
        window.close()
        return False

    mnemonic.layout_engine.layout(mnemonic.components, mnemonic.connections)
    window.show()
    mnemonic._compute_sync()

    if debug:
        mnemonic.toggle_debug()

    mnemonic.repaint()
    app.processEvents()

    pixmap = mnemonic.grab()
    pixmap.save(str(output_path))
    window.close()
    return True


def main():
    parser = argparse.ArgumentParser(description="Скриншоты всех тестовых YAML-схем")
    parser.add_argument("--no-debug", action="store_true",
                        help="Без отладочной сетки и bounding box")
    parser.add_argument("--filter", type=str, default="",
                        help="Фильтр по имени файла (подстрока)")
    parser.add_argument("--neg", action="store_true",
                        help="Включить neg_ файлы (по умолчанию пропускаются)")
    args = parser.parse_args()

    debug = not args.no_debug

    # Собираем YAML-файлы
    yaml_files = sorted(SCHEMES_DIR.glob("*.yaml"))
    if args.filter:
        yaml_files = [f for f in yaml_files if args.filter in f.name]
    if not args.neg:
        yaml_files = [f for f in yaml_files if not f.name.startswith("neg_")]

    if not yaml_files:
        print("Нет файлов для обработки.")
        return

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    app = QApplication(sys.argv)
    adapter = MockAdapter()

    print(f"Обработка {len(yaml_files)} схем → {OUTPUT_DIR}/")
    print(f"Режим отладки: {'ВКЛ (сетка + bounding box)' if debug else 'ВЫКЛ'}")
    print("=" * 60)

    ok_count = 0
    fail_count = 0

    for yaml_path in yaml_files:
        name = yaml_path.stem
        suffix = "_debug" if debug else ""
        output_path = OUTPUT_DIR / f"{name}{suffix}.png"

        print(f"  {name} ... ", end="", flush=True)
        success = render_scheme(app, adapter, yaml_path, output_path, debug)
        if success:
            ok_count += 1
            print(f"✓ → {output_path.name}")
        else:
            fail_count += 1

    print("=" * 60)
    print(f"Готово: {ok_count} ✓, {fail_count} ⚠")
    print(f"Скриншоты: {OUTPUT_DIR.resolve()}")

    app.quit()


if __name__ == "__main__":
    main()
