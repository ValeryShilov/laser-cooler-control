import sys
from PySide6.QtWidgets import QApplication
from interface import ChillerPanel

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    window = ChillerPanel()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()