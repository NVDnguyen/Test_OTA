from PyQt5.QtWidgets import QLabel, QPushButton
from qt_client.widgets.product_widget import ProductWidget  # Replace with your actual import

def test_product_widget_elements_exist(shopping_cart_app):
    """Test that the key elements of the ProductWidget exist."""
    # Create a dummy product for testing
    product_data = {"id": 1, "name": "Test Product", "subtitle": "Test Subtitle", "price": 10.0, "quantity": 1}
    product_widget = ProductWidget(product_data)
    
    assert product_widget.name_label is not None
    assert isinstance(product_widget.name_label, QLabel)
    assert product_widget.subtitle_label is not None
    assert isinstance(product_widget.subtitle_label, QLabel)
    assert product_widget.price_label is not None
    assert isinstance(product_widget.price_label, QLabel)
    assert product_widget.quantity_label is not None
    assert isinstance(product_widget.quantity_label, QLabel)
    assert product_widget.remove_button is not None
    assert isinstance(product_widget.remove_button, QPushButton)

# Add more tests to check:
# - Data is displayed correctly
# - Button click events
# - UI updates based on data changes