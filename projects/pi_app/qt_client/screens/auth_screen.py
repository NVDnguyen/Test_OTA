# screens/auth_screen.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QFormLayout,
                             QStackedWidget, QScrollArea)
from PyQt5.QtCore import pyqtSignal, Qt

class AuthScreen(QWidget):
    """
    A QWidget that provides a stacked layout for handling different
    authentication methods: Card Login, Email/Password Login, and Registration.
    """
    card_login_attempt = pyqtSignal(str)
    email_login_attempt = pyqtSignal(str, str)
    guest_login_attempt = pyqtSignal()
    register_attempt = pyqtSignal(str, str)

    login_success = pyqtSignal(str, str, str)  # identity, role, message
    login_failure = pyqtSignal(str)
    logout_success = pyqtSignal()
    api_error = pyqtSignal(str)
    token_refresh_needed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initializes the UI components and layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.stacked_widget = QStackedWidget()

        # Create the three auth views
        self.card_login_widget = self._create_card_login_widget()
        self.email_login_widget = self._create_email_login_widget()
        self.register_widget = self._create_register_widget()

        # Add them to the stack
        self.stacked_widget.addWidget(self.card_login_widget)
        self.stacked_widget.addWidget(self.email_login_widget)
        self.stacked_widget.addWidget(self.register_widget)

        self.scroll_area.setWidget(self.stacked_widget)
        main_layout.addWidget(self.scroll_area)
        
        self.set_default_screen()
        
        # Responsive font size
        self.resizeEvent = self._on_resize
        self._on_resize()

    def _on_resize(self, event=None):
        width = self.width()
        # Responsive font size: shrink on small screens
        font_size = max(10, min(16, width // 35))
        title_font_size = max(12, min(22, width // 20))
        self.setStyleSheet(f"""
            QLabel#title_label {{ font-size: {title_font_size}px; }}
            QLineEdit, QPushButton {{ font-size: {font_size}px; }}
        """)

    def _create_form_container(self, title_text, form_layout, primary_button, links_layout):
        """Helper to create a consistent container for auth forms."""
        container = QFrame()
        container.setObjectName("main_frame")
        container.setMinimumWidth(120)
        container.setMaximumWidth(420)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)  # More compact margins
        layout.setSpacing(7)  # More compact spacing

        title = QLabel(title_text)
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addLayout(form_layout)
        layout.addStretch()
        primary_button.setMinimumHeight(44)
        layout.addWidget(primary_button)
        layout.addSpacing(4)
        layout.addLayout(links_layout)
        
        return container

    def _create_card_login_widget(self):
        """Creates the widget for card-based login."""
        form_layout = QFormLayout()
        form_layout.setSpacing(7)
        self.card_id_input = QLineEdit()
        self.card_id_input.setPlaceholderText("Scan or enter your card ID")
        self.card_id_input.setMinimumHeight(40)
        self.card_id_input.setSizePolicy(self.card_id_input.sizePolicy().horizontalPolicy(), 1)
        form_layout.addRow("Card ID:", self.card_id_input)

        login_button = QPushButton("Login with Card")
        login_button.setObjectName("checkout_button")
        login_button.setMinimumHeight(44)
        login_button.setSizePolicy(login_button.sizePolicy().horizontalPolicy(), 1)
        login_button.clicked.connect(self._on_card_login_clicked)

        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        links_layout.setSpacing(6)
        email_login_link = QPushButton("Login with Email instead")
        email_login_link.setObjectName("link_button")
        email_login_link.setMinimumHeight(32)
        email_login_link.setSizePolicy(email_login_link.sizePolicy().horizontalPolicy(), 1)
        email_login_link.clicked.connect(self.show_email_login)
        guest_login_button = QPushButton("Skip to Login as Guest")
        guest_login_button.setObjectName("link_button")
        guest_login_button.setMinimumHeight(32)
        guest_login_button.setSizePolicy(guest_login_button.sizePolicy().horizontalPolicy(), 1)
        guest_login_button.clicked.connect(self._on_guest_login_clicked)
        links_layout.addWidget(guest_login_button)
        links_layout.addWidget(email_login_link)

        widget = self._create_form_container("Card Login", form_layout, login_button, links_layout)
        return widget

    def _create_email_login_widget(self):
        """Creates the widget for email/password login."""
        form_layout = QFormLayout()
        form_layout.setSpacing(7)
        self.login_email_input = QLineEdit()
        self.login_email_input.setPlaceholderText("Enter your email")
        self.login_email_input.setMinimumHeight(40)
        self.login_email_input.setSizePolicy(self.login_email_input.sizePolicy().horizontalPolicy(), 1)
        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Enter your password")
        self.login_password_input.setEchoMode(QLineEdit.Password)
        self.login_password_input.setMinimumHeight(40)
        self.login_password_input.setSizePolicy(self.login_password_input.sizePolicy().horizontalPolicy(), 1)
        form_layout.addRow("Email:", self.login_email_input)
        form_layout.addRow("Password:", self.login_password_input)

        login_button = QPushButton("Login")
        login_button.setObjectName("checkout_button")
        login_button.setMinimumHeight(44)
        login_button.setSizePolicy(login_button.sizePolicy().horizontalPolicy(), 1)
        login_button.clicked.connect(self._on_email_login_clicked)

        links_layout = QHBoxLayout()
        links_layout.setSpacing(6)
        card_login_link = QPushButton("« Use Card Login")
        card_login_link.setObjectName("link_button")
        card_login_link.setMinimumHeight(32)
        card_login_link.setSizePolicy(card_login_link.sizePolicy().horizontalPolicy(), 1)
        card_login_link.clicked.connect(self.show_card_login)
        register_link = QPushButton("Need an account? Register »")
        register_link.setObjectName("link_button")
        register_link.setMinimumHeight(32)
        register_link.setSizePolicy(register_link.sizePolicy().horizontalPolicy(), 1)
        register_link.clicked.connect(self.show_register)
        links_layout.addWidget(card_login_link)
        links_layout.addStretch()
        links_layout.addWidget(register_link)

        widget = self._create_form_container("Email Login", form_layout, login_button, links_layout)
        return widget

    def _create_register_widget(self):
        """Creates the widget for user registration."""
        form_layout = QFormLayout()
        form_layout.setSpacing(7)
        self.register_email_input = QLineEdit()
        self.register_email_input.setPlaceholderText("Choose an email")
        self.register_email_input.setMinimumHeight(40)
        self.register_email_input.setSizePolicy(self.register_email_input.sizePolicy().horizontalPolicy(), 1)
        self.register_password_input = QLineEdit()
        self.register_password_input.setPlaceholderText("Choose a password (min 8 chars)")
        self.register_password_input.setEchoMode(QLineEdit.Password)
        self.register_password_input.setMinimumHeight(40)
        self.register_password_input.setSizePolicy(self.register_password_input.sizePolicy().horizontalPolicy(), 1)
        form_layout.addRow("Email:", self.register_email_input)
        form_layout.addRow("Password:", self.register_password_input)

        register_button = QPushButton("Register")
        register_button.setObjectName("checkout_button")
        register_button.setMinimumHeight(44)
        register_button.setSizePolicy(register_button.sizePolicy().horizontalPolicy(), 1)
        register_button.clicked.connect(self._on_register_clicked)

        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        links_layout.setSpacing(6)
        login_link = QPushButton("Already have an account? Login")
        login_link.setObjectName("link_button")
        login_link.setMinimumHeight(32)
        login_link.setSizePolicy(login_link.sizePolicy().horizontalPolicy(), 1)
        login_link.clicked.connect(self.show_email_login)
        links_layout.addWidget(login_link)

        widget = self._create_form_container("Create Account", form_layout, register_button, links_layout)
        return widget

    def _on_card_login_clicked(self):
        card_id = self.card_id_input.text().strip()
        if card_id:
            self.card_login_attempt.emit(card_id)

    def _on_email_login_clicked(self):
        email = self.login_email_input.text().strip()
        password = self.login_password_input.text()
        if email and password:
            self.email_login_attempt.emit(email, password)

    def _on_register_clicked(self):
        email = self.register_email_input.text().strip()
        password = self.register_password_input.text()
        if email and password:
            self.register_attempt.emit(email, password)

    def _on_guest_login_clicked(self):
        self.guest_login_attempt.emit()

    def show_card_login(self):
        self.stacked_widget.setCurrentWidget(self.card_login_widget)

    def show_email_login(self):
        self.stacked_widget.setCurrentWidget(self.email_login_widget)

    def show_register(self):
        self.stacked_widget.setCurrentWidget(self.register_widget)

    def handle_login_success(self, identity, role, message):
        self.login_success.emit(identity, role, message)
        self.clear_inputs()
        self.set_default_screen()

    def handle_login_failure(self, error_message):
        self.login_failure.emit(error_message)

    def handle_logout_success(self):
        self.logout_success.emit()
        self.set_default_screen()

    def handle_api_error(self, error_message):
        self.api_error.emit(error_message)

    def handle_token_refresh_needed(self):
        self.token_refresh_needed.emit()

    def set_default_screen(self):
        self.stacked_widget.setCurrentWidget(self.card_login_widget)
        self.clear_inputs()

    def clear_inputs(self):
        """Clears all text input fields."""
        self.card_id_input.clear()
        self.login_email_input.clear()
        self.login_password_input.clear()
        self.register_email_input.clear()
        self.register_password_input.clear()

    def guest_login(self):
        # Simulate guest login success immediately
        self.handle_login_success("guest", "guest", "Logged in as guest.")