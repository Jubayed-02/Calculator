from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QKeySequence, QIcon, QColor, QPalette
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from calculator_engine import CalculatorEngine
from voice_controller import VoiceThread
from database import CalculatorDB

class CalculatorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = CalculatorEngine()
        self.db = CalculatorDB()
        self.voice_thread = None
        self.current_expression = ""
        self.last_result = None
        self.pro_mode = False  # Start in Simple Mode
        
        self.init_ui()
        self.setup_connections()
        self.apply_dark_theme()
    
    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Smart Calculator")
        self.setMinimumSize(380, 550)
        self.resize(400, 650)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with no margins to maximize space
        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setSpacing(5)
        self.main_layout.setContentsMargins(8, 8, 8, 8)
        
        # === Top Bar with Mode Toggle ===
        top_bar = QWidget()
        top_bar.setFixedHeight(40)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(5)
        
        # Mode Toggle Switch (Compact)
        mode_widget = QWidget()
        mode_layout = QHBoxLayout(mode_widget)
        mode_layout.setContentsMargins(0, 0, 0, 0)
        mode_layout.setSpacing(3)
        
        self.mode_label_simple = QLabel("SIMPLE")
        self.mode_label_simple.setFont(QFont("Arial", 9, QFont.Bold))
        self.mode_label_simple.setStyleSheet("color: #34c759;")
        
        self.mode_toggle = QPushButton()
        self.mode_toggle.setCheckable(True)
        self.mode_toggle.setFixedSize(40, 20)
        self.mode_toggle.setStyleSheet("""
            QPushButton {
                background-color: #3c3c3c;
                border-radius: 10px;
                border: 2px solid #555;
            }
            QPushButton:checked {
                background-color: #ff9500;
            }
        """)
        
        self.mode_label_pro = QLabel("PRO")
        self.mode_label_pro.setFont(QFont("Arial", 9, QFont.Bold))
        self.mode_label_pro.setStyleSheet("color: #888;")
        
        mode_layout.addWidget(self.mode_label_simple)
        mode_layout.addWidget(self.mode_toggle)
        mode_layout.addWidget(self.mode_label_pro)
        
        top_layout.addWidget(mode_widget)
        top_layout.addStretch()
        
        # History button
        self.history_btn = QPushButton("📜")
        self.history_btn.setToolTip("History (Ctrl+H)")
        self.history_btn.setFixedSize(35, 35)
        self.history_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #ff9500;
                border: 1px solid #555;
                border-radius: 6px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #444;
                border-color: #ff9500;
            }
        """)
        
        top_layout.addWidget(self.history_btn)
        self.main_layout.addWidget(top_bar)
        
        # === Display (Compact but readable) ===
        self.display = QLineEdit()
        self.display.setReadOnly(False)
        self.display.setAlignment(Qt.AlignRight)
        self.display.setMinimumHeight(60)
        self.display.setMaximumHeight(80)
        self.display.setFont(QFont("Segoe UI", 20, QFont.Bold))
        self.display.setPlaceholderText("0")
        self.display.setStyleSheet("""
            QLineEdit {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 2px solid #333;
                border-radius: 10px;
                padding: 10px;
                selection-background-color: #ff9500;
            }
            QLineEdit:focus {
                border-color: #ff9500;
            }
        """)
        self.main_layout.addWidget(self.display)
        
        # === Preview Label (Small) ===
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet("""
            color: #ff9500;
            padding: 2px 8px;
            font-size: 11px;
            min-height: 16px;
        """)
        self.preview_label.setAlignment(Qt.AlignRight)
        self.preview_label.setWordWrap(True)
        self.main_layout.addWidget(self.preview_label)
        
        # === History Panel (Hidden by default) ===
        self.history_panel = self.create_history_panel()
        self.history_panel.hide()
        self.main_layout.addWidget(self.history_panel)
        
        # === Pro Mode Panel (Compact, responsive grid) ===
        self.pro_panel = self.create_pro_panel()
        self.pro_panel.hide()
        self.main_layout.addWidget(self.pro_panel)
        
        # === Smart Features Bar (Compact) ===
        self.smart_bar = self.create_smart_bar()
        self.main_layout.addWidget(self.smart_bar)
        
        # === Button Grid (Takes remaining space) ===
        self.button_grid = self.create_button_grid()
        self.main_layout.addWidget(self.button_grid, 1)  # Stretch factor 1
        
        # === Status Bar ===
        self.status_bar = QStatusBar()
        self.status_bar.setFixedHeight(20)
        self.status_bar.setStyleSheet("font-size: 10px;")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
    
    def create_history_panel(self):
        """Create compact history panel"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(3)
        
        # Header (Compact)
        header = QHBoxLayout()
        history_label = QLabel("History")
        history_label.setStyleSheet("color: #ff9500; font-weight: bold; font-size: 11px;")
        header.addWidget(history_label)
        
        self.clear_history_btn = QPushButton("Clear")
        self.clear_history_btn.setFixedHeight(25)
        self.clear_history_btn.setFont(QFont("Arial", 9))
        self.clear_history_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 3px 8px;
            }
            QPushButton:hover {
                background-color: #ff5c5c;
            }
        """)
        header.addWidget(self.clear_history_btn)
        layout.addLayout(header)
        
        # Search (Compact)
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search...")
        self.history_search.textChanged.connect(self.filter_history)
        self.history_search.setFixedHeight(28)
        self.history_search.setFont(QFont("Arial", 10))
        self.history_search.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2c;
                color: white;
                border: 1px solid #444;
                border-radius: 4px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.history_search)
        
        # List (Compact)
        self.history_list = QListWidget()
        self.history_list.itemDoubleClicked.connect(self.use_history_item)
        self.history_list.setMaximumHeight(150)
        self.history_list.setFont(QFont("Arial", 10))
        self.history_list.setStyleSheet("""
            QListWidget {
                background-color: #2c2c2c;
                color: #ffffff;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #ff9500;
            }
        """)
        layout.addWidget(self.history_list)
        
        self.refresh_history()
        return widget
    
    def create_pro_panel(self):
        """Create responsive Pro mode panel with scientific functions"""
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout = QGridLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 3, 0, 3)
        
        # Make columns stretch equally
        for i in range(4):
            layout.setColumnStretch(i, 1)
        
        # Scientific functions - 2 rows of 4 buttons (more compact)
        sci_buttons = [
            # Row 1
            ('sin', 0, 0), ('cos', 0, 1), ('tan', 0, 2), ('log', 0, 3),
            # Row 2
            ('√', 1, 0), ('x²', 1, 1), ('π', 1, 2), ('e', 1, 3),
            # Row 3
            ('(', 2, 0), (')', 2, 1), ('ln', 2, 2), ('|x|', 2, 3),
        ]
        
        for text, row, col in sci_buttons:
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setMinimumHeight(35)
            btn.setFont(QFont("Segoe UI", 10, QFont.Bold))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c2c2e;
                    color: #ff9500;
                    border: 1px solid #444;
                    border-radius: 6px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3a3a3c;
                    border-color: #ff9500;
                }
                QPushButton:pressed {
                    background-color: #1e1e1e;
                }
            """)
            
            # Connect functions
            if text == '√':
                btn.clicked.connect(lambda: self.scientific_function('√'))
            elif text == 'x²':
                btn.clicked.connect(lambda: self.scientific_function('x²'))
            elif text == '|x|':
                btn.clicked.connect(lambda: self.scientific_function('abs'))
            else:
                btn.clicked.connect(lambda checked, t=text: self.scientific_function(t))
            
            layout.addWidget(btn, row, col)
        
        return widget
    
    def speak_result(self):
        """Speak the current result ONLY when user clicks the Speak button"""
        text_to_speak = self.display.text()
        
        if not text_to_speak or text_to_speak == "Error":
            if self.last_result:
                text_to_speak = str(self.last_result)
            else:
                self.preview_label.setText("Nothing to speak")
                self.status_bar.showMessage("Nothing to speak", 2000)
                return
        
        # Update UI to show speaking
        self.speak_btn.setText("🔊 Speaking...")
        self.preview_label.setText(f"🔊 Speaking: {text_to_speak}")
        self.status_bar.showMessage(f"Speaking: {text_to_speak}", 2000)
        
        # Create a temporary voice thread just for speaking
        if not self.voice_thread:
            self.voice_thread = VoiceThread()
        elif self.voice_thread.isRunning():
            self.voice_thread.terminate()
            self.voice_thread.wait()
            self.voice_thread = VoiceThread()
        
        # Speak the text
        self.voice_thread.speak(str(text_to_speak))
        
        # Reset button after delay
        words = len(str(text_to_speak).split())
        delay = max(1500, words * 400)
        QTimer.singleShot(delay, self.reset_speak_button)
        self.preview_label.setText(f"✅ Spoke: {text_to_speak}")

    def reset_speak_button(self):
        """Reset speak button to default state"""
        self.speak_btn.setText("🔊 Speak")  # Or just "🔊" if using icon-only
    def reset_speak_button(self):
        """Reset speak button to default state"""
        self.speak_btn.setText("🔊 Speak")  # Or just "🔊"
        self.preview_label.setText("✅ Ready")

    
    def create_smart_bar(self):
        """Create compact smart features bar with text labels"""
        widget = QWidget()
        widget.setFixedHeight(40)
        layout = QHBoxLayout(widget)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 2, 0, 2)
        
        # Voice Input button - Purple
        self.voice_btn = QPushButton("🎤 Voice")
        self.voice_btn.setToolTip("Voice Input - Speak calculation (Ctrl+V)")
        self.voice_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.voice_btn.setStyleSheet("""
            QPushButton {
                background-color: #7b68ee;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #9b8cf5;
            }
            QPushButton:pressed {
                background-color: #6a5acd;
            }
        """)
        self.voice_btn.clicked.connect(self.start_voice_input)
        
        # Voice Output button - Green
        self.speak_btn = QPushButton("🔊 Speak")
        self.speak_btn.setToolTip("Speak Result - Read result aloud (Ctrl+S)")
        self.speak_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.speak_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #34ce57;
            }
            QPushButton:pressed {
                background-color: #1e7e34;
            }
        """)
        self.speak_btn.clicked.connect(self.speak_result)
        
        # Clipboard button - Blue
        self.clipboard_btn = QPushButton("📋 Clip")
        self.clipboard_btn.setToolTip("Smart Clipboard - Solve from clipboard (Ctrl+B)")
        self.clipboard_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.clipboard_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #3395ff;
            }
            QPushButton:pressed {
                background-color: #0056b3;
            }
        """)
        self.clipboard_btn.clicked.connect(self.solve_clipboard)
        
        # Currency button - Orange
        self.currency_btn = QPushButton("💱 Convert")
        self.currency_btn.setToolTip("Converter - Currency & Units")
        self.currency_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.currency_btn.setStyleSheet("""
            QPushButton {
                background-color: #fd7e14;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px 2px;
            }
            QPushButton:hover {
                background-color: #fd9a4a;
            }
            QPushButton:pressed {
                background-color: #dc6502;
            }
        """)
        self.currency_btn.clicked.connect(self.show_conversion_dialog)
        
        layout.addWidget(self.voice_btn)
        layout.addWidget(self.speak_btn)
        layout.addWidget(self.clipboard_btn)
        layout.addWidget(self.currency_btn)
        
        return widget
    
    def create_button_grid(self):
        """Create responsive main button grid"""
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        grid = QGridLayout(widget)
        grid.setSpacing(4)
        grid.setContentsMargins(0, 3, 0, 0)
        
        # Make all rows and columns stretch equally
        for i in range(5):
            grid.setRowStretch(i, 1)
        for i in range(4):
            grid.setColumnStretch(i, 1)
        
        buttons = [
            ('C', 0, 0, 'clear'), ('⌫', 0, 1, 'action'), ('%', 0, 2, 'operator'), ('÷', 0, 3, 'operator'),
            ('7', 1, 0, 'number'), ('8', 1, 1, 'number'), ('9', 1, 2, 'number'), ('×', 1, 3, 'operator'),
            ('4', 2, 0, 'number'), ('5', 2, 1, 'number'), ('6', 2, 2, 'number'), ('−', 2, 3, 'operator'),
            ('1', 3, 0, 'number'), ('2', 3, 1, 'number'), ('3', 3, 2, 'number'), ('+', 3, 3, 'operator'),
            ('±', 4, 0, 'action'), ('0', 4, 1, 'number'), ('.', 4, 2, 'number'), ('=', 4, 3, 'equals')
        ]
        
        for text, row, col, btn_type in buttons:
            btn = QPushButton(text)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            btn.setFont(QFont("Segoe UI", 14, QFont.Bold))
            
            # Base style with smaller padding
            base_style = """
                border: none;
                border-radius: 8px;
                font-weight: bold;
            """
            
            if btn_type == 'number':
                btn.setStyleSheet(f"""
                    QPushButton {{{base_style}
                        background-color: #333333;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #444444; }}
                    QPushButton:pressed {{ background-color: #555555; }}
                """)
                btn.clicked.connect(lambda checked, t=text: self.append_number(t))
            elif btn_type == 'operator':
                btn.setStyleSheet(f"""
                    QPushButton {{{base_style}
                        background-color: #ff9500;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #ffaa33; }}
                    QPushButton:pressed {{ background-color: #e68600; }}
                """)
                op_map = {'÷': '/', '×': '*', '−': '-', '+': '+', '%': '%'}
                btn.clicked.connect(lambda checked, t=text: self.append_operator(op_map.get(t, t)))
            elif btn_type == 'equals':
                btn.setStyleSheet(f"""
                    QPushButton {{{base_style}
                        background-color: #34c759;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #4cd964; }}
                    QPushButton:pressed {{ background-color: #2db84d; }}
                """)
                btn.clicked.connect(self.calculate_result)
            elif text == 'C':
                btn.setStyleSheet(f"""
                    QPushButton {{{base_style}
                        background-color: #ff3b30;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #ff5c5c; }}
                    QPushButton:pressed {{ background-color: #e6352b; }}
                """)
                btn.clicked.connect(self.clear_display)
            elif text == '⌫':
                btn.setStyleSheet(f"""
                    QPushButton {{{base_style}
                        background-color: #ff9500;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #ffaa33; }}
                    QPushButton:pressed {{ background-color: #e68600; }}
                """)
                btn.clicked.connect(self.backspace)
            elif text == '±':
                btn.setStyleSheet(f"""
                    QPushButton {{{base_style}
                        background-color: #5856d6;
                        color: #ffffff;
                    }}
                    QPushButton:hover {{ background-color: #6e6cf0; }}
                    QPushButton:pressed {{ background-color: #4f4dc4; }}
                """)
                btn.clicked.connect(self.toggle_sign)
            
            grid.addWidget(btn, row, col)
        
        return widget
    
    def setup_connections(self):
        """Setup connections and shortcuts"""
        self.mode_toggle.toggled.connect(self.toggle_pro_mode)
        self.history_btn.clicked.connect(self.toggle_history)
        self.clear_history_btn.clicked.connect(self.clear_history)
        
        # Keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+H"), self).activated.connect(self.toggle_history)
        QShortcut(QKeySequence("Ctrl+V"), self).activated.connect(self.start_voice_input)
        QShortcut(QKeySequence("Ctrl+S"), self).activated.connect(self.speak_result)  # Speak
        QShortcut(QKeySequence("Ctrl+B"), self).activated.connect(self.solve_clipboard)
        QShortcut(QKeySequence("Ctrl+P"), self).activated.connect(lambda: self.mode_toggle.toggle())
        QShortcut(QKeySequence("Return"), self).activated.connect(self.calculate_result)
        QShortcut(QKeySequence("Enter"), self).activated.connect(self.calculate_result)
        QShortcut(QKeySequence("Backspace"), self).activated.connect(self.backspace)
        QShortcut(QKeySequence("Escape"), self).activated.connect(self.clear_display)
    
    def toggle_pro_mode(self, checked):
        """Toggle between Simple and Pro mode"""
        self.pro_mode = checked
        if checked:
            self.pro_panel.show()
            self.mode_label_simple.setStyleSheet("color: #888;")
            self.mode_label_pro.setStyleSheet("color: #ff9500; font-weight: bold;")
            self.setWindowTitle("Smart Calculator PRO")
            self.status_bar.showMessage("Pro Mode", 1500)
        else:
            self.pro_panel.hide()
            self.mode_label_simple.setStyleSheet("color: #34c759; font-weight: bold;")
            self.mode_label_pro.setStyleSheet("color: #888;")
            self.setWindowTitle("Smart Calculator")
            self.status_bar.showMessage("Simple Mode", 1500)
    
    def toggle_history(self):
        """Toggle history panel"""
        if self.history_panel.isVisible():
            self.history_panel.hide()
        else:
            self.history_panel.show()
            self.refresh_history()
    
    def resizeEvent(self, event):
        """Handle window resize to adjust font sizes"""
        super().resizeEvent(event)
        
        # Adjust display font based on window width
        width = self.width()
        if width < 400:
            self.display.setFont(QFont("Segoe UI", 18, QFont.Bold))
            grid_font_size = 12
        elif width < 500:
            self.display.setFont(QFont("Segoe UI", 20, QFont.Bold))
            grid_font_size = 13
        else:
            self.display.setFont(QFont("Segoe UI", 22, QFont.Bold))
            grid_font_size = 14
        
        # Update button font sizes
        for btn in self.findChildren(QPushButton):
            if btn.parent() == self.button_grid:
                btn.setFont(QFont("Segoe UI", grid_font_size, QFont.Bold))
    
    # Calculator functions
    def append_number(self, num):
        self.current_expression += num
        self.display.setText(self.current_expression)
    
    def append_operator(self, op):
        if self.current_expression and self.current_expression[-1] not in '+-*/^':
            self.current_expression += op
            self.display.setText(self.current_expression)
    
    def scientific_function(self, func):
        """Handle scientific functions"""
        func_map = {
            'sin': 'sin(', 'cos': 'cos(', 'tan': 'tan(',
            'asin': 'asin(', 'acos': 'acos(', 'atan': 'atan(',
            '√': 'sqrt(', 'x²': '^2',
            'log': 'log(', 'ln': 'ln(',
            'π': 'pi', 'e': 'E',
            '(': '(', ')': ')',
            'abs': 'abs('
        }
        self.current_expression += func_map.get(func, func)
        self.display.setText(self.current_expression)
    
    def calculate_result(self):
        """Calculate the result"""
        if not self.current_expression:
            self.current_expression = self.display.text()
        
        if not self.current_expression:
            return
        
        self.preview_label.setText(f"Calculating: {self.current_expression}")
        result = self.engine.evaluate(self.current_expression)
        
        if 'error' in result:
            self.display.setText("Error")
            self.preview_label.setText(f"❌ {result['error']}")
            self.status_bar.showMessage(result['error'], 3000)
            self.last_result = None
        else:
            result_value = str(result['value'])
            self.display.setText(result_value)
            self.preview_label.setText(f"= {result_value}")
            self.db.add_history(self.current_expression, result_value, 
                            result.get('category', 'standard'))
            self.current_expression = result_value
            self.last_result = result_value  # Store for speaking
            self.refresh_history()
            # Auto-speak REMOVED from here
    
    def clear_display(self):
        self.current_expression = ""
        self.display.clear()
        self.preview_label.clear()
    
    def backspace(self):
        self.current_expression = self.current_expression[:-1]
        self.display.setText(self.current_expression)
    
    def toggle_sign(self):
        if self.current_expression:
            if self.current_expression.startswith('-'):
                self.current_expression = self.current_expression[1:]
            else:
                self.current_expression = '-' + self.current_expression
            self.display.setText(self.current_expression)
    
    def start_voice_input(self):
        """Start voice recognition"""
        self.voice_btn.setText("🎤 Listening...")
        self.preview_label.setText("Speak now...")
        
        if self.voice_thread and self.voice_thread.isRunning():
            self.voice_thread.terminate()
        
        self.voice_thread = VoiceThread()
        self.voice_thread.text_heard.connect(self.process_voice_input)
        self.voice_thread.status_update.connect(self.status_bar.showMessage)
        self.voice_thread.start()
    
    def process_voice_input(self, text):
        """Process voice input and speak the result"""
        self.voice_btn.setText("🎤 Voice")
        
        if text and text != "ERROR":
            self.current_expression = text
            self.display.setText(text)
            self.preview_label.setText(f"✅ Heard: {text}")
            
            # Calculate directly
            result = self.engine.evaluate(self.current_expression)
            
            if 'error' not in result:
                result_value = str(result['value'])
                self.display.setText(result_value)
                self.preview_label.setText(f"= {result_value}")
                self.db.add_history(self.current_expression, result_value, 
                                result.get('category', 'standard'))
                self.current_expression = result_value
                self.last_result = result_value
                self.refresh_history()
                
                # Speak the result
                if self.voice_thread and self.voice_thread.isRunning():
                    self.voice_thread.terminate()
                    self.voice_thread.wait()
                
                self.voice_thread = VoiceThread()
                self.voice_thread.speak(f"Equals {result_value}")
                self.status_bar.showMessage(f"✅ Result: {result_value}", 2000)
            else:
                self.display.setText("Error")
                self.preview_label.setText(f"❌ {result['error']}")
                self.status_bar.showMessage(result['error'], 3000)
        else:
            self.preview_label.setText("❌ Could not understand audio")
            self.status_bar.showMessage("Could not understand audio", 2000)
    
    def solve_clipboard(self):
        """Solve from clipboard"""
        self.preview_label.setText("Reading clipboard...")
        result = self.engine.solve_clipboard()
        
        if result.get('success'):
            self.display.setText(str(result['value']))
            self.preview_label.setText(f"📋 {result.get('original_text', '')[:40]}... = {result['value']}")
            self.current_expression = str(result['value'])
            self.db.add_history(result.get('expression', 'clipboard'), 
                               result['value'], 'smart')
            self.refresh_history()
        else:
            self.preview_label.setText(f"❌ {result.get('error', 'No math found')}")
    
    def show_conversion_dialog(self):
        """Show conversion dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("💱 Smart Converter")
        dialog.setMinimumWidth(400)
        dialog.setStyleSheet("background-color: #1e1e1e;")
        
        layout = QVBoxLayout(dialog)
        layout.setSpacing(12)
        
        # Title
        title = QLabel("💱 Currency & Unit Converter")
        title.setFont(QFont("Segoe UI", 14, QFont.Bold))
        title.setStyleSheet("color: #ff9500;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Input
        input_field = QLineEdit()
        input_field.setMinimumHeight(40)
        input_field.setFont(QFont("Segoe UI", 13))
        input_field.setPlaceholderText("e.g., 100 usd to eur OR 5 km to miles")
        input_field.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2c;
                color: white;
                border: 2px solid #444;
                border-radius: 8px;
                padding: 8px;
            }
            QLineEdit:focus {
                border-color: #ff9500;
            }
        """)
        layout.addWidget(input_field)
        
        # Examples
        examples = QLabel("Examples: 100 usd to eur | 5 km to miles | 10 kg to lbs")
        examples.setStyleSheet("color: #888; font-size: 10px;")
        examples.setWordWrap(True)
        layout.addWidget(examples)
        
        # Buttons
        btn_layout = QHBoxLayout()
        convert_btn = QPushButton("Convert")
        convert_btn.setMinimumHeight(35)
        convert_btn.setStyleSheet("""
            QPushButton {
                background-color: #34c759;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4cd964;
            }
        """)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setMinimumHeight(35)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff3b30;
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff5c5c;
            }
        """)
        
        btn_layout.addWidget(convert_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        # Result
        result_label = QLabel("")
        result_label.setFont(QFont("Segoe UI", 14, QFont.Bold))
        result_label.setStyleSheet("""
            color: #34c759;
            padding: 12px;
            background-color: #2c2c2c;
            border-radius: 6px;
        """)
        result_label.setAlignment(Qt.AlignCenter)
        result_label.setWordWrap(True)
        layout.addWidget(result_label)
        
        def do_conversion():
            expr = input_field.text().strip()
            if not expr:
                result_label.setText("Please enter a conversion")
                return
            
            result = self.engine.evaluate(expr)
            if 'error' not in result:
                result_label.setText(f"{expr} = {result['value']}")
                self.display.setText(str(result['value']))
                self.current_expression = str(result['value'])
                self.db.add_history(expr, result['value'], 'conversion')
                self.refresh_history()
            else:
                result_label.setText(f"Error: {result['error']}")
        
        convert_btn.clicked.connect(do_conversion)
        cancel_btn.clicked.connect(dialog.reject)
        input_field.returnPressed.connect(do_conversion)
        
        dialog.exec_()
    
    def refresh_history(self):
        """Refresh history list"""
        self.history_list.clear()
        history_items = self.db.get_history(20)
        for expr, result, timestamp, category in history_items:
            icon = "🔄" if category == "conversion" else "📋" if category == "smart" else "📊"
            self.history_list.addItem(f"{icon} {expr} = {result}")
    
    def filter_history(self):
        """Filter history"""
        search = self.history_search.text()
        if not search:
            self.refresh_history()
            return
        
        self.history_list.clear()
        for expr, result, timestamp in self.db.search_history(search):
            self.history_list.addItem(f"📊 {expr} = {result}")
    
    def use_history_item(self, item):
        """Use history item"""
        text = item.text()
        parts = text.split('=')
        if len(parts) > 1:
            result = parts[1].strip()
            self.current_expression = result
            self.display.setText(result)
            self.preview_label.setText(f"Loaded from history")
    
    def clear_history(self):
        """Clear history"""
        reply = QMessageBox.question(self, 'Clear History', 
                                     'Clear all history?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.clear_history()
            self.refresh_history()
            self.status_bar.showMessage("History cleared", 2000)
    
    def apply_dark_theme(self):
        """Apply dark theme to entire application"""
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a1a;
            }
            QLabel {
                color: #ffffff;
            }
            QStatusBar {
                color: #888;
                font-size: 10px;
            }
        """)