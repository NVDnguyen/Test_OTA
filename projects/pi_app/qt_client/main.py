# main.py
# The main application logic (activity).

import sys
import time
import json     # For formatting data for POST requests
from decimal import Decimal # For precise financial calculations
import requests # For making HTTP requests to the backend
import signal

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QStackedWidget, QWidget, QVBoxLayout, QPushButton, QMessageBox, QInputDialog
from PyQt5.QtCore import pyqtSlot, Qt, QTimer

# Import the UI definition and stylesheet
from utils.api_client import ApiClient
from utils.serial_reader import SerialReaderThread
from config.settings import settings
from config.stylesheet import STYLESHEET
from screens.home_screen import create_home_screen_widget
from screens.auth_screen import AuthScreen
from screens.qr_payment_dialog import QRPaymentDialog
from screens.cart_screen import CartScreen
from screens.map_screen import MapScreen
from widgets.product_widget import ProductWidget

class ShoppingCartApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.api_client = ApiClient(base_url=settings.API_BASE_URL, parent=self)

        # --- Data Model ---
        # This will be populated from the backend API
        self.products_in_cart = []

        # --- UI Setup ---
        self.setWindowTitle("Shopping Application")
        self.setGeometry(100, 100, 1200, 650) # Adjusted height slightly for potential home screen content
        self.setMinimumSize(400, 300)  # Ensure window is resizable

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Create Home Screen Page FIRST, as it contains the serial output widget
        self.home_screen_page, self.view_cart_button, self.serial_output_text_edit, self.login_button, self.map_button = create_home_screen_widget()
        self.stacked_widget.addWidget(self.home_screen_page)
        
        # Create Cart Screen Page
        self.cart_screen_page = CartScreen()
        self.stacked_widget.addWidget(self.cart_screen_page)

        # Create Authentication Screen (handles card, email/pass, register)
        self.auth_screen = AuthScreen(parent=self)
        self.stacked_widget.addWidget(self.auth_screen)

        # Create Map Screen (for product search on map)
        self.map_screen = MapScreen(api_base_url=settings.API_BASE_URL)
        self.stacked_widget.addWidget(self.map_screen)

        # Fetch data after UI elements are initialized
        self.fetch_products_from_api()
        self.populate_cart()

        # --- Connect Signals to Slots (Event Handling) ---
        self.cart_screen_page.shipping_combo.currentIndexChanged.connect(self.update_totals)
        self.cart_screen_page.continue_shopping_button.clicked.connect(self.show_home_screen)
        self.view_cart_button.clicked.connect(self.show_cart_screen)
        self.login_button.clicked.connect(self._on_login_button_clicked)
        self.cart_screen_page.checkout_button.clicked.connect(self.handle_checkout_initiation)
        self.map_button.clicked.connect(self.show_map_screen)

        # Connect ApiClient signals to ShoppingCartApp slots
        self.api_client.login_success.connect(self.on_login_success)
        self.api_client.login_failure.connect(self.on_login_failure)
        self.api_client.logout_success.connect(self.on_logout_success)
        self.api_client.api_error.connect(self.on_api_error)
        self.api_client.token_refresh_needed.connect(self.on_token_refresh_needed)

        self.auth_screen.card_login_attempt.connect(self.api_client.card_login)
        self.auth_screen.email_login_attempt.connect(self.api_client.login)
        self.auth_screen.guest_login_attempt.connect(self.api_client.guest_login)
        self.auth_screen.register_attempt.connect(self.api_client.register)

        # We will connect product widget signals when they are created

        # --- Final UI Updates ---
        self.update_totals() # Update totals after cart is populated
        
        # --- Setup and Start Serial Thread ---
        self.serial_thread = SerialReaderThread(
            port=settings.SERIAL_PORT,
            baudrate=settings.SERIAL_BAUDRATE
        )
        self.serial_thread.new_data_received.connect(self.append_serial_output)
        self.serial_thread.error_occurred.connect(self.append_serial_output) # Also display errors
        self.serial_thread.finished_signal.connect(self.on_serial_thread_finished)
        self.serial_thread.start()

        # Start on login screen initially
        self.show_login_screen() # Always start at login

        # Remove the demo map_btn and container (no longer needed)

    def _on_login_button_clicked(self):
        """Handles the click on the Login/Register button on the home screen."""
        # If already logged in, offer logout or card login
        if self.api_client.current_user_identity:
            reply = QMessageBox.question(self, 'Logged In', 
                                         f"You are logged in as {self.api_client.current_user_identity}.\nDo you want to log out?",
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.api_client.logout()
        else:
            # If not logged in, switch to the auth screen
            self.show_login_screen()

    # --- ApiClient Signal Handlers ---
    @pyqtSlot(str, str, str)
    def on_login_success(self, identity, role, message):
        self.append_serial_output(f"{message} Identity: {identity}, Role: {role}.\n")
        # QMessageBox.information(self, "Login/Register Success", message)  # Dialog removed
        self.auth_screen.clear_inputs()
        self.show_home_screen()

    @pyqtSlot(str)
    def on_login_failure(self, error_message):
        self.append_serial_output(f"Authentication failed: {error_message}\n")
        QMessageBox.warning(self, "Authentication Failed", error_message)

    @pyqtSlot()
    def on_logout_success(self):
        self.append_serial_output("Logged out successfully.\n")
        QMessageBox.information(self, "Logout", "You have been logged out.")
        self.show_login_screen()

    @pyqtSlot(str)
    def on_api_error(self, error_message):
        self.append_serial_output(f"API Error: {error_message}\n")
        # QMessageBox.critical(self, "API Error", error_message) # Uncomment for more aggressive error popups

    @pyqtSlot()
    def on_token_refresh_needed(self):
        self.append_serial_output("Access token expired. Attempting to refresh...\n")

    def fetch_products_from_api(self):
        """Fetches the initial product list from the backend API."""
        try:
            # In a production app, this URL should be in a config file.
            # The timeout is important to prevent the UI from freezing indefinitely.
            response = self.api_client.get("/api/products")
            
            # The API returns a list of products. We'll treat them as items in the cart
            # to match the original application's behavior.
            self.products_in_cart = response.json()
            print("Successfully fetched products from API.")
        except requests.exceptions.RequestException as e:
            print(f"Error fetching products from API: {e}. Using offline data.")
            self.append_serial_output(f"Could not connect to backend. Using offline data.\nError: {e}\n")


    def populate_cart(self):
        """Create and add product widgets to the cart layout."""
        # Use the method from CartScreen to clear the layout
        self.cart_screen_page.clear_products_layout()
                 
        for product_data in self.products_in_cart:
            product_widget = ProductWidget(product_data)
            
            # Connect the buttons of this specific widget to handlers
            product_widget.plus_button.clicked.connect(lambda _, p=product_data: self.change_quantity(p['id'], 1))
            product_widget.minus_button.clicked.connect(lambda _, p=product_data: self.change_quantity(p['id'], -1))
            product_widget.remove_button.clicked.connect(lambda _, p=product_data: self.remove_product(p['id']))
            
            self.cart_screen_page.products_layout.addWidget(product_widget)
    
    def change_quantity(self, product_id, change):
        """Handle clicks on the '+' and '-' buttons."""
        for product in self.products_in_cart:
            if product['id'] == product_id:
                if product['quantity'] + change >= 0: # Allow quantity to be 0, remove if it becomes 0
                    product['quantity'] += change
                break
        
        # Refresh the UI
        self.populate_cart()
        self.update_totals()

    def remove_product(self, product_id):
        """Handle clicks on the 'Remove' button."""
        self.products_in_cart = [p for p in self.products_in_cart if p['id'] != product_id]

        # Refresh the UI
        self.populate_cart()
        self.update_totals()

    def show_home_screen(self):
        self.stacked_widget.setCurrentWidget(self.home_screen_page)
        self.setWindowTitle("Home - Shopping Application")

    def show_cart_screen(self):
        self.populate_cart() # Ensure cart display is up-to-date
        self.update_totals() # Ensure totals are up-to-date
        self.stacked_widget.setCurrentWidget(self.cart_screen_page)
        self.setWindowTitle("Your Cart - Shopping Application")

    def handle_checkout_initiation(self):
        """Gathers cart data and sends it to the backend checkout endpoint."""
        print("Checkout button clicked. Preparing data...")
        # Recalculate totals using Decimal for precision, as done in update_totals
        subtotal_decimal = Decimal(0)
        for p in self.products_in_cart:
            subtotal_decimal += Decimal(str(p['price'])) * Decimal(p['quantity'])
        
        shipping_cost_float = self.cart_screen_page.shipping_combo.currentData()
        shipping_cost_decimal = Decimal(str(shipping_cost_float)) if shipping_cost_float is not None else Decimal(0)

        total_cost_decimal = subtotal_decimal + shipping_cost_decimal

        # Convert back to float for the payload, ensuring they are derived from precise Decimal calculations
        subtotal_for_payload = float(subtotal_decimal)
        shipping_cost_for_payload = float(shipping_cost_decimal)
        total_cost_for_payload = float(total_cost_decimal)

        # Prepare the payload for the API
        payload = {
            "items": self.products_in_cart,
            "shipping_cost": shipping_cost_for_payload,
            "subtotal": subtotal_for_payload,
            "total_cost": total_for_payload,
        }
        
        print(f"Sending to backend: {json.dumps(payload, indent=2)}")
        self.append_serial_output("Sending checkout request to server...\n")

        try:
            response = self.api_client.post("/api/orders/checkout", json_data=payload)
            response_data = response.json()
            print(f"Backend response: {response_data}")
            self.append_serial_output(f"Checkout initiated! Order ID: {response_data.get('order_id')}.\n")

            # Display QR code and start polling
            self.show_qr_payment_dialog(response_data.get('order_id'), response_data.get('qr_svg'))
        except requests.exceptions.RequestException as e:
            print(f"Error during checkout: {e}")
            self.append_serial_output(f"Error during checkout: {e}\n")
            QMessageBox.critical(self, "Checkout Failed", f"Could not initiate checkout: {e}")

    def show_login_screen(self):
        self.auth_screen.set_default_screen() # Reset to card login
        self.stacked_widget.setCurrentWidget(self.auth_screen)
        self.setWindowTitle("Login / Register - Shopping Application")

    def show_qr_payment_dialog(self, order_id, qr_svg_string):
        """Displays the QR payment dialog, which handles its own polling."""
        self.qr_dialog = QRPaymentDialog(order_id, qr_svg_string, self.api_client, self)
        
        self.qr_dialog.exec_() # Show as modal dialog

    def show_map_screen(self):
        self.stacked_widget.setCurrentWidget(self.map_screen)

    @pyqtSlot(str)
    def append_serial_output(self, text):
        """Appends text to the serial output QTextEdit on the home screen."""
        self.serial_output_text_edit.moveCursor(self.serial_output_text_edit.textCursor().End)
        self.serial_output_text_edit.insertPlainText(text)
        self.serial_output_text_edit.moveCursor(self.serial_output_text_edit.textCursor().End)


    def update_totals(self):
        """Recalculate and display all totals."""
        # Use Decimal for precise calculations to avoid floating point errors
        subtotal_decimal = Decimal(0)
        for p in self.products_in_cart:
            # Ensure price is treated as Decimal for calculation
            subtotal_decimal += Decimal(str(p['price'])) * Decimal(p['quantity'])
        
        shipping_cost_float = self.cart_screen_page.shipping_combo.currentData()
        shipping_cost_decimal = Decimal(str(shipping_cost_float)) if shipping_cost_float is not None else Decimal(0)

        total_cost_decimal = subtotal_decimal + shipping_cost_decimal
        
        # Convert back to float for display and payload, but the calculation was precise
        subtotal = float(subtotal_decimal)
        total_cost = float(total_cost_decimal)
        item_count = sum(p['quantity'] for p in self.products_in_cart)
        self.cart_screen_page.item_count_label.setText(f"{item_count} Items")
        self.cart_screen_page.subtotal_label.setText(f"£{subtotal:.2f}")
        self.cart_screen_page.total_cost_label.setText(f"£{total_cost:.2f}")
        
        # Also update the items count in the summary panel
        # Access the label directly via the attribute set in ui.py
        if hasattr(self.cart_screen_page, 'summary_items_header_label') and self.cart_screen_page.summary_items_header_label:
            self.cart_screen_page.summary_items_header_label.setText(f"ITEMS {item_count}")
        else:
            print("Warning: summary_items_header_label not found in UI. Summary item count might not update.")

    def on_serial_thread_finished(self):
        print("Serial reader thread has finished.")

    def closeEvent(self, event):
        """Ensure the serial thread is stopped cleanly when the application closes."""
        print("Closing application, stopping serial thread...")
        self.serial_thread.stop()
        self.serial_thread.wait() # Wait for the thread to finish
        super().closeEvent(event)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET) # Apply the global stylesheet
    
    window = ShoppingCartApp()
    window.show()
    
    sys.exit(app.exec_())
