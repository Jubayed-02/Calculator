import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from ui.main_window import CalculatorWindow

# Add this after imports but before main()
import traceback
import sys

def exception_hook(exctype, value, tb):
    print(''.join(traceback.format_exception(exctype, value, tb)))
    sys.exit(1)

sys.excepthook = exception_hook

def main():
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Create and show calculator
    calculator = CalculatorWindow()
    calculator.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()