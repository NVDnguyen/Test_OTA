from PyQt5.QtWidgets import QPushButton, QTextEdit

def test_home_screen_exists(shopping_cart_app):
    """Test that the home screen is created."""
    assert shopping_cart_app.home_screen_page is not None

def test_home_screen_elements_exist(shopping_cart_app):
    """Test that the key elements of the home screen exist."""
    assert shopping_cart_app.view_cart_button is not None
    assert isinstance(shopping_cart_app.view_cart_button, QPushButton)
    assert shopping_cart_app.serial_output_text_edit is not None
    assert isinstance(shopping_cart_app.serial_output_text_edit, QTextEdit)
    assert shopping_cart_app.login_button is not None
    assert isinstance(shopping_cart_app.login_button, QPushButton)

# Add more tests to check:
# - Button click events
# - Serial output updates (mock the serial thread for testing)
# - UI updates based on data (mock the API client for testing)