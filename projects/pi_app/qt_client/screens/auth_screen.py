# screens/auth_screen.py

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QFrame, QFormLayout,
                             QStackedWidget)
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        """Initializes the UI components and layout."""
        main_layout = QHBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        self.stacked_widget = QStackedWidget()

        # Create the three auth views
        self.card_login_widget = self._create_card_login_widget()
        self.email_login_widget = self._create_email_login_widget()
        self.register_widget = self._create_register_widget()

        # Add them to the stack
        self.stacked_widget.addWidget(self.card_login_widget)
        self.stacked_widget.addWidget(self.email_login_widget)
        self.stacked_widget.addWidget(self.register_widget)

        main_layout.addWidget(self.stacked_widget)
        
        self.set_default_screen()

    def _create_form_container(self, title_text, form_layout, primary_button, links_layout):
        """Helper to create a consistent container for auth forms."""
        container = QFrame()
        container.setObjectName("main_frame")
        container.setFixedWidth(450)
        
        layout = QVBoxLayout(container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel(title_text)
        title.setObjectName("title_label")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        layout.addLayout(form_layout)
        layout.addStretch()
        layout.addWidget(primary_button)
        layout.addSpacing(10)
        layout.addLayout(links_layout)
        
        return container

    def _create_card_login_widget(self):
        """Creates the widget for card-based login."""
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        self.card_id_input = QLineEdit()
        self.card_id_input.setPlaceholderText("Scan or enter your card ID")
        form_layout.addRow("Card ID:", self.card_id_input)

        login_button = QPushButton("Login with Card")
        login_button.setObjectName("checkout_button")
        login_button.clicked.connect(self._on_card_login_clicked)

        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        email_login_link = QPushButton("Login with Email instead")
        email_login_link.setObjectName("link_button")
        email_login_link.clicked.connect(self.show_email_login)
        
        guest_login_button = QPushButton("Skip to Login as Guest")
        guest_login_button.setObjectName("link_button")
        guest_login_button.clicked.connect(self._on_guest_login_clicked)
        links_layout.addWidget(guest_login_button)
        links_layout.addWidget(email_login_link)

        widget = self._create_form_container("Card Login", form_layout, login_button, links_layout)
        return widget

    def _create_email_login_widget(self):
        """Creates the widget for email/password login."""
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        self.login_email_input = QLineEdit()
        self.login_email_input.setPlaceholderText("Enter your email")
        self.login_password_input = QLineEdit()
        self.login_password_input.setPlaceholderText("Enter your password")
        self.login_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Email:", self.login_email_input)
        form_layout.addRow("Password:", self.login_password_input)

        login_button = QPushButton("Login")
        login_button.setObjectName("checkout_button")
        login_button.clicked.connect(self._on_email_login_clicked)

        links_layout = QHBoxLayout()
        links_layout.setSpacing(20)
        card_login_link = QPushButton("« Use Card Login")
        card_login_link.setObjectName("link_button")
        card_login_link.clicked.connect(self.show_card_login)
        
        register_link = QPushButton("Need an account? Register »")
        register_link.setObjectName("link_button")
        register_link.clicked.connect(self.show_register)
        
        links_layout.addWidget(card_login_link)
        links_layout.addStretch()
        links_layout.addWidget(register_link)

        widget = self._create_form_container("Email Login", form_layout, login_button, links_layout)
        return widget

    def _create_register_widget(self):
        """Creates the widget for user registration."""
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        self.register_email_input = QLineEdit()
        self.register_email_input.setPlaceholderText("Choose an email")
        self.register_password_input = QLineEdit()
        self.register_password_input.setPlaceholderText("Choose a password (min 8 chars)")
        self.register_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Email:", self.register_email_input)
        form_layout.addRow("Password:", self.register_password_input)

        register_button = QPushButton("Register")
        register_button.setObjectName("checkout_button")
        register_button.clicked.connect(self._on_register_clicked)

        links_layout = QHBoxLayout()
        links_layout.setAlignment(Qt.AlignCenter)
        login_link = QPushButton("Already have an account? Login")
        login_link.setObjectName("link_button")
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

    def set_default_screen(self):
        self.show_card_login()

    def clear_inputs(self):
        """Clears all text input fields."""
        self.card_id_input.clear()
        self.login_email_input.clear()
        self.login_password_input.clear()
        self.register_email_input.clear()
        self.register_password_input.clear()