# home_screen.py
# Defines the UI for the home screen.

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QTextEdit
from PyQt5.QtCore import Qt

def create_home_screen_widget():
    """Creates and returns the home screen widget, its 'View Cart' button, and the serial output text area."""
    home_widget = QWidget()
    layout = QVBoxLayout(home_widget)
    layout.setContentsMargins(50, 50, 50, 50)
    layout.setSpacing(20)
    
    title_label = QLabel("Welcome to Our Store!")
    title_label.setObjectName("title_label") # Reuse existing style from stylesheet
    title_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(title_label)

    products_info_label = QLabel("This is the home screen.\nBrowse our amazing products here (TODO: Implement product browsing).")
    products_info_label.setAlignment(Qt.AlignCenter)
    layout.addWidget(products_info_label)
    
    layout.addSpacing(20)

    serial_output_area = QTextEdit()
    serial_output_area.setObjectName("serial_output_area")
    serial_output_area.setReadOnly(True)
    serial_output_area.setPlaceholderText("Serial output will appear here...")
    layout.addWidget(serial_output_area, 1) # Give it some stretch factor

    layout.addStretch()

    view_cart_button = QPushButton("View Cart / Checkout")
    view_cart_button.setObjectName("checkout_button") # Reuse style from stylesheet
    view_cart_button.setMinimumHeight(40)
    layout.addWidget(view_cart_button, alignment=Qt.AlignCenter)
    
    login_button = QPushButton("Login / Register")
    login_button.setObjectName("link_button")
    login_button.setMinimumHeight(40)
    layout.addWidget(login_button, alignment=Qt.AlignCenter)
    
    return home_widget, view_cart_button, serial_output_area, login_button