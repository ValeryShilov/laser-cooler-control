import sys
from PySide6.QtWidgets import QApplication
from ui.main_window import ChillerPanel
from hardware.mock_adapter import MockAdapter

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    adapter = MockAdapter()
    window = ChillerPanel(adapter)
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()