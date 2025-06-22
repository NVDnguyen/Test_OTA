import pytest
from PyQt5.QtWidgets import QApplication
from qt_client.main import ShoppingCartApp  # Replace with your actual import

@pytest.fixture(scope="session")
def qapp():
    """Fixture for the QApplication."""
    app = QApplication.instance() if QApplication.instance() else QApplication([])
    yield app

@pytest.fixture
def shopping_cart_app(qapp):
    """Fixture for the main ShoppingCartApp window."""
    return ShoppingCartApp()