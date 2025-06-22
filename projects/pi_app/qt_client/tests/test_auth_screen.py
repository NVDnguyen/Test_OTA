# tests/test_auth_screen.py
from PyQt5.QtWidgets import QLineEdit
from qt_client.screens.auth_screen import AuthScreen

def test_auth_screen_exists(shopping_cart_app):
    """Test that the auth screen is created."""
    assert shopping_cart_app.auth_screen is not None
    assert isinstance(shopping_cart_app.auth_screen, AuthScreen)

def test_card_login_fields_exist(shopping_cart_app):
    """Test that the card login fields exist."""
    auth_screen = shopping_cart_app.auth_screen
    assert auth_screen.card_id_input is not None
    assert isinstance(auth_screen.card_id_input, QLineEdit)

def test_email_login_fields_exist(shopping_cart_app):
    """Test that the email login fields exist."""
    auth_screen = shopping_cart_app.auth_screen
    assert auth_screen.login_email_input is not None
    assert isinstance(auth_screen.login_email_input, QLineEdit)
    assert auth_screen.login_password_input is not None
    assert isinstance(auth_screen.login_password_input, QLineEdit)

def test_register_fields_exist(shopping_cart_app):
    """Test that the register fields exist."""
    auth_screen = shopping_cart_app.auth_screen
    assert auth_screen.register_email_input is not None
    assert isinstance(auth_screen.register_email_input, QLineEdit)
    assert auth_screen.register_password_input is not None
    assert isinstance(auth_screen.register_password_input, QLineEdit)

# Add more tests to check:
# - Signal emission on button clicks
# - Screen switching within the auth screen
# - UI updates based on backend responses (mocked)