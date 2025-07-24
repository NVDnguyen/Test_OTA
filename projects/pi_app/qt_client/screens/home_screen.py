# screens/home_screen.py
# Defines the UI for the home screen.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout, QLineEdit, QScrollArea, QSizePolicy, QBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal

class HomeScreen(QWidget):
    send_serial_message = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._init_scrollable_ui()

    def _init_scrollable_ui(self):
        # Create a scroll area and set its widget
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget()
        self._init_ui(content)
        scroll.setWidget(content)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(scroll)
        self.setLayout(layout)

    def _init_ui(self, parent):
        layout = QVBoxLayout(parent)
        layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins for small screens
        layout.setSpacing(10)
        
        title_label = QLabel("Welcome to Our Store!")
        title_label.setObjectName("title_label")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(title_label)

        products_info_label = QLabel("This is the home screen.\nBrowse our amazing products here (TODO: Implement product browsing).")
        products_info_label.setAlignment(Qt.AlignCenter)
        products_info_label.setWordWrap(True)
        products_info_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(products_info_label)
        
        layout.addSpacing(6)

        self.serial_output_area = QTextEdit()
        self.serial_output_area.setObjectName("serial_output_area")
        self.serial_output_area.setReadOnly(True)
        self.serial_output_area.setPlaceholderText("Serial output will appear here...")
        self.serial_output_area.setStyleSheet("font-size: 13px; min-height: 80px;")
        layout.addWidget(self.serial_output_area, 1)

        # --- Serial send controls ---
        serial_send_layout = QHBoxLayout()
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Enter message to send to serial port...")
        self.serial_input.setMinimumHeight(36)
        self.serial_input.setStyleSheet("font-size: 14px; min-height: 36px;")
        self.serial_send_button = QPushButton("Send to Serial")
        self.serial_send_button.setMinimumHeight(36)
        self.serial_send_button.setStyleSheet("font-size: 14px; min-width: 80px;")
        self.serial_send_button.clicked.connect(self._emit_serial_message)
        serial_send_layout.addWidget(self.serial_input)
        serial_send_layout.addWidget(self.serial_send_button)
        layout.addLayout(serial_send_layout)

        layout.addStretch()

        # --- Action Buttons ---
        self.action_buttons_layout = QBoxLayout(QBoxLayout.LeftToRight)
        self.view_cart_button = QPushButton("View Cart")
        self.view_cart_button.setObjectName("checkout_button")
        self.view_cart_button.setMinimumHeight(44)
        self.view_cart_button.setStyleSheet("font-size: 15px; min-width: 120px;")
        self.action_buttons_layout.addWidget(self.view_cart_button)

        self.map_button = QPushButton("Product Map")
        self.map_button.setObjectName("checkout_button")
        self.map_button.setMinimumHeight(44)
        self.map_button.setStyleSheet("font-size: 15px; min-width: 120px;")
        self.action_buttons_layout.addWidget(self.map_button)
        layout.addLayout(self.action_buttons_layout)

        self.login_button = QPushButton("Logout")
        self.login_button.setObjectName("link_button")
        self.login_button.setMinimumHeight(36)
        self.login_button.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.login_button, alignment=Qt.AlignCenter)

        parent.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Responsive: switch action buttons layout direction based on width.
        is_narrow = self.width() < 400
        current_direction = self.action_buttons_layout.direction()
        if is_narrow and current_direction != QBoxLayout.TopToBottom:
            self.action_buttons_layout.setDirection(QBoxLayout.TopToBottom)
            # Add spacing between buttons for touch
            self.action_buttons_layout.setSpacing(8)
        elif not is_narrow and current_direction != QBoxLayout.LeftToRight:
            self.action_buttons_layout.setDirection(QBoxLayout.LeftToRight)
            self.action_buttons_layout.setSpacing(4)

    def append_serial_output(self, text):
        self.serial_output_area.moveCursor(self.serial_output_area.textCursor().End)
        self.serial_output_area.insertPlainText(text)
        self.serial_output_area.moveCursor(self.serial_output_area.textCursor().End)

    def set_serial_output(self, text):
        self.serial_output_area.setPlainText(text)

    def clear_serial_output(self):
        self.serial_output_area.clear()

    def set_map_button_callback(self, callback):
        self.map_button.clicked.connect(callback)

    def set_view_cart_callback(self, callback):
        self.view_cart_button.clicked.connect(callback)

    def set_login_button_callback(self, callback):
        self.login_button.clicked.connect(callback)

    def _emit_serial_message(self):
        msg = self.serial_input.text()
        if msg:
            self.send_serial_message.emit(msg)
            self.serial_input.clear()