"""
CSS-стили интерфейса чиллера.

Вынесены из main_window.py для соблюдения SRP.
"""


MAIN_STYLE = """
    QMainWindow { background-color: #f2f4f7; }
    QGroupBox { font-weight: bold; font-size: 14px; border: 1px solid #c4c8cc; border-radius: 6px; margin-top: 15px; padding-top: 15px; background-color: #ffffff; }
    QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; color: #333; }
    QPushButton { background-color: #4CAF50; color: white; border: none; padding: 10px 15px; font-size: 13px; font-weight: bold; border-radius: 4px; }
    QPushButton:hover { background-color: #45a049; }
    QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
    QDoubleSpinBox, QComboBox { padding: 5px; border: 1px solid #ccc; border-radius: 4px; font-size: 13px; }
    QDoubleSpinBox:disabled { background-color: #eeeeee; color: #999999; }
    QTabWidget::pane { border: 1px solid #c4c8cc; border-radius: 6px; background-color: #ffffff; }
    QTabBar::tab { background-color: #e6e9ed; border: 1px solid #c4c8cc; border-bottom: none; border-top-left-radius: 6px; border-top-right-radius: 6px; padding: 8px 20px; font-weight: bold; color: #555; }
    QTabBar::tab:selected { background-color: #ffffff; border-bottom: 1px solid #ffffff; color: #000; }
"""

STOP_BUTTON_STYLE = """
    QPushButton { background-color: #F44336; }
    QPushButton:hover { background-color: #D32F2F; }
    QPushButton:disabled { background-color: #cfd8dc; color: #90a4ae; }
"""
