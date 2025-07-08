# main.py
# The main application logic (activity).

import sys
import time
import json     # For formatting data for POST requests
from decimal import Decimal # For precise financial calculations
import requests # For making HTTP requests to the backend
import signal
from contextlib import contextmanager
import logging

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QStackedWidget, QWidget, QVBoxLayout, QPushButton, QMessageBox, QInputDialog, QDialog, QSizePolicy, QHBoxLayout, QProgressBar
from PyQt5.QtCore import pyqtSlot, Qt, QTimer

# Import the UI definition and stylesheet
from utils.api_client import ApiClient
from utils.serial_controller import SerialReaderThread, SerialWriterThread
from config.settings import settings
from config.stylesheet import STYLESHEET
from screens.home_screen import HomeScreen
from screens.auth_screen import AuthScreen
from screens.cart_screen import CartScreen
from screens.map_screen import MapScreen
from screens.camera_scan_screen import CameraScanScreen
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
        self.home_screen = HomeScreen()
        self.stacked_widget.addWidget(self.home_screen)
        
        # Create Cart Screen Page
        self.cart_screen_page = CartScreen()
        self.stacked_widget.addWidget(self.cart_screen_page)

        # Create Authentication Screen (handles card, email/pass, register)
        self.auth_screen = AuthScreen(parent=self)
        self.stacked_widget.addWidget(self.auth_screen)

        # Create Map Screen (for product search on map)
        self.map_screen = MapScreen(api_base_url=settings.API_BASE_URL, return_home_callback=lambda : self.stacked_widget.setCurrentWidget(self.home_screen))
        self.stacked_widget.addWidget(self.map_screen)

        # Fetch data after UI elements are initialized
        self.fetch_products_from_api()
        self.populate_cart()

        # --- Connect Signals to Slots (Event Handling) ---
        self.cart_screen_page.shipping_combo.currentIndexChanged.connect(self.update_totals)
        self.cart_screen_page.set_continue_shopping_callback(self.show_home_screen)
        self.home_screen.set_map_button_callback(self.show_map_screen)
        self.home_screen.set_view_cart_callback(lambda: self.show_cart_screen(self.products_in_cart))
        self.home_screen.set_login_button_callback(self._on_login_button_clicked)
        self.cart_screen_page.set_checkout_callback(self.handle_checkout_initiation)
        self.cart_screen_page.barcode_scanned.connect(self.handle_barcode_scanned)
        self.cart_screen_page.quantity_changed.connect(self.handle_quantity_changed)
        self.cart_screen_page.product_removed.connect(self.handle_product_removed)

        # --- ApiClient Signal Handlers ---
        # Connect all relevant ApiClient signals to ShoppingCartApp slots for robust error handling and feedback
        self.api_client.login_success.connect(self.on_login_success)
        self.api_client.login_failure.connect(self.on_login_failure)
        self.api_client.logout_success.connect(self.on_logout_success)
        self.api_client.api_error.connect(self.on_api_error)
        self.api_client.token_refresh_needed.connect(self.on_token_refresh_needed)
        self.api_client.tokens_set.connect(self.on_tokens_set)

        # Connect AuthScreen signals to main window slots
        self.auth_screen.login_success.connect(self.on_login_success)
        self.auth_screen.login_failure.connect(self.on_login_failure)
        self.auth_screen.logout_success.connect(self.on_logout_success)
        self.auth_screen.api_error.connect(self.on_api_error)
        self.auth_screen.token_refresh_needed.connect(self.on_token_refresh_needed)

        self.auth_screen.card_login_attempt.connect(lambda *args, **kwargs: self._on_login_attempt('card', *args, **kwargs))
        self.auth_screen.email_login_attempt.connect(lambda *args, **kwargs: self._on_login_attempt('email', *args, **kwargs))
        self.auth_screen.guest_login_attempt.connect(lambda *args, **kwargs: self._on_login_attempt('guest', *args, **kwargs))
        self.auth_screen.register_attempt.connect(lambda *args, **kwargs: self._on_login_attempt('register', *args, **kwargs))

        # Connect the new tokens_set signal from ApiClient
        self.api_client.tokens_set.connect(self.on_tokens_set)

        # We will connect product widget signals when they are created

        # --- Final UI Updates ---
        self.update_totals() # Update totals after cart is populated
        
        # --- Setup and Start Serial Threads ---
        self.serial_thread = SerialReaderThread(
            port=settings.SERIAL_PORT,
            baudrate=settings.SERIAL_BAUDRATE
        )
        self.serial_thread.new_data_received.connect(self.append_serial_output)
        self.serial_thread.error_occurred.connect(self.append_serial_output) # Also display errors
        self.serial_thread.finished_signal.connect(self.on_serial_thread_finished)
        self.serial_thread.start()

        self.serial_writer = SerialWriterThread(
            port=settings.SERIAL_PORT,
            baudrate=settings.SERIAL_BAUDRATE
        )
        self.serial_writer.write_success.connect(lambda msg: self.append_serial_output(f"[WRITE SUCCESS] {msg}\n"))
        self.serial_writer.error_occurred.connect(lambda msg: self.append_serial_output(f"[WRITE ERROR] {msg}\n"))
        self.serial_writer.start()
        self.home_screen.send_serial_message.connect(self.serial_writer.send)

        # Start on login screen initially
        self.show_login_screen() # Always start at login

        # Remove the demo map_btn and container (no longer needed)
        self.showFullScreen()  # Automatically start in full screen mode

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

    def show_loading_screen(self, message="Loading..."):
        """Show a semi-transparent loading overlay with a message."""
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            return  # Already showing
        overlay = QWidget(self)
        overlay.setGeometry(self.rect())
        overlay.setStyleSheet("background: rgba(0,0,0,0.5);")
        overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        overlay.setAttribute(Qt.WA_DeleteOnClose)
        layout = QVBoxLayout(overlay)
        layout.setAlignment(Qt.AlignCenter)
        label = QLabel(message)
        label.setStyleSheet("color: white; font-size: 28px; padding: 32px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        overlay.show()
        self._loading_overlay = overlay

    def hide_loading_screen(self):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            self._loading_overlay.close()
            self._loading_overlay = None

    # --- ApiClient Signal Handlers ---
    @pyqtSlot(str, str, str)
    def on_login_success(self, identity, role, message):
        self.hide_loading_screen()
        self.append_serial_output(f"{message} Identity: {identity}, Role: {role}.\n")
        self.auth_screen.clear_inputs()
        self.fetch_products_from_api()  # Refresh products after login
        self.show_home_screen()

    @pyqtSlot(str)
    def on_login_failure(self, error_message):
        logging.warning(f"on_login_failure called with error_message: {error_message}")
        self.hide_loading_screen()
        self.append_serial_output(f"Authentication failed: {error_message}\n")
        self.show_error_dialog(
            "Login failed. Please check your credentials, card, or network connection and try again.",
            title="Login Failed",
            show_details=True,
            details=str(error_message)
        )

    @pyqtSlot()
    def on_logout_success(self):
        self.append_serial_output("Logged out successfully.\n")
        QMessageBox.information(self, "Logout", "You have been logged out.")
        self.show_login_screen()

    @pyqtSlot(str)
    def on_api_error(self, error_message):
        self.append_serial_output(f"API Error: {error_message}\n")
        self.show_error_dialog(
            "A server or network error occurred. Please try again.",
            title="API Error",
            show_details=True,
            details=str(error_message)
        )

    @pyqtSlot()
    def on_token_refresh_needed(self):
        self.append_serial_output("Access token expired. Attempting to refresh...\n")

    def on_tokens_set(self, identity, role):
        # Move to home screen when tokens are set
        self.show_home_screen()

    @contextmanager
    def api_call_feedback(self, loading_message="Loading...", error_message="An error occurred.", error_title="Error"):
        self.show_loading_screen(loading_message)
        try:
            yield
        except Exception as e:
            self.show_error_dialog(error_message, title=error_title, show_details=True, details=str(e))
            raise
        finally:
            self.hide_loading_screen()

    def fetch_products_from_api(self):
        """Fetches the initial product list from the backend API. Always allows GUI to load. Fills the cart with one of each product (quantity=1)."""
        try:
            with self.api_call_feedback(
                loading_message="Fetching products...",
                error_message="Could not connect to the backend server. Please check your network connection or try again later. Offline data will be used if available.",
                error_title="Connection Error"
            ):
                response = self.api_client.get("/api/products")
                products = response.json()
                # Fill the cart with one of each product
                self.products_in_cart = [dict(p, quantity=1) for p in products]
                print(self.products_in_cart)
                print("Successfully fetched products from API and filled cart.")
        except Exception as e:
            # Show error, but continue with empty/offline data
            print(f"Error fetching products from API: {e}. Using offline data.")
            self.products_in_cart = []
        self.cart_screen_page.set_cart_products(self.products_in_cart)

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
        subtotal_for_payload = float(subtotal_decimal)
        shipping_cost_for_payload = float(shipping_cost_decimal)
        total_cost_for_payload = float(total_cost_decimal)
        payload = {
            "items": self.products_in_cart,
            "shipping_cost": shipping_cost_for_payload,
            "subtotal": subtotal_for_payload,
            "total_cost": total_cost_for_payload,
        }
        print(f"Sending to backend: {json.dumps(payload, indent=2)}")
        self.append_serial_output("Sending checkout request to server...\n")
        with self.api_call_feedback(
            loading_message="Processing checkout...",
            error_message="Could not initiate checkout. Please try again.",
            error_title="Checkout Failed"
        ):
            response = self.api_client.post("/api/orders/checkout", json_data=payload)
            response_data = response.json()
            print(f"Backend response: {response_data}")
            self.append_serial_output(f"Checkout initiated! Order ID: {response_data.get('order_id')}.\n")
            self.show_qr_payment_dialog(response_data.get('order_id'), response_data.get('qr_svg'))

    def show_login_screen(self):
        self.auth_screen.set_default_screen() # Reset to card login
        self.stacked_widget.setCurrentWidget(self.auth_screen)
        self.setWindowTitle("Login / Register - Shopping Application")

    def show_qr_payment_dialog(self, order_id, qr_svg_string):
        """Displays the QR payment dialog, which handles its own polling."""
        from screens.qr_payment_dialog import QRPaymentDialog
        self.qr_dialog = QRPaymentDialog(order_id, qr_svg_string, self.api_client, self)
        
        self.qr_dialog.exec_() # Show as modal dialog

    def show_cart_screen(self, products):
        self.cart_screen_page.set_cart_products(products)
        self.cart_screen_page.update_cart_totals()
        self.stacked_widget.setCurrentWidget(self.cart_screen_page)
        self.setWindowTitle("Your Cart - Shopping Application")

    def show_home_screen(self):
        self.stacked_widget.setCurrentWidget(self.home_screen)
        self.setWindowTitle("Home - Shopping Application")

    def show_map_screen(self):
        self.map_screen.set_api_base_url(settings.API_BASE_URL)
        self.stacked_widget.setCurrentWidget(self.map_screen)

    def open_camera_scan_screen(self):
        self._previous_screen = self.stacked_widget.currentWidget()
        self.camera_screen = CameraScanScreen(self)
        self.camera_screen.barcode_scanned.connect(self._on_camera_barcode_scanned)
        self.camera_screen.back_requested.connect(self._on_camera_scan_back)
        self.stacked_widget.addWidget(self.camera_screen)
        self.stacked_widget.setCurrentWidget(self.camera_screen)

    def _on_camera_barcode_scanned(self, barcode):
        # Pass barcode to cart screen or wherever needed
        self.cart_screen_page.barcode_input.setText(barcode)
        self.cart_screen_page.scan_barcode_and_add_item(barcode)
        self._on_camera_scan_back()

    def _on_camera_scan_back(self):
        if hasattr(self, '_previous_screen') and self._previous_screen:
            self.stacked_widget.setCurrentWidget(self._previous_screen)
            self.stacked_widget.removeWidget(self.camera_screen)
            del self.camera_screen

    @pyqtSlot(str)
    def append_serial_output(self, text):
        """Appends text to the serial output QTextEdit on the home screen."""
        self.home_screen.append_serial_output(text)


    def on_serial_thread_finished(self):
        print("Serial reader thread has finished.")

    def closeEvent(self, event):
        """Ensure the serial thread is stopped cleanly when the application closes."""
        print("Closing application, stopping serial thread...")
        self.serial_thread.stop()
        self.serial_thread.wait() # Wait for the thread to finish
        super().closeEvent(event)

    def show_error_dialog(self, message, title="Error", show_details=False, details=None):
        """Show a touch-friendly error dialog with dynamic layout for small monitors. Optionally show details in an expandable section."""
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.setModal(True)
        dialog.setMinimumSize(320, 180)
        dialog.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout = QVBoxLayout(dialog)
        label = QLabel(message)
        label.setWordWrap(True)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("font-size: 20px; padding: 16px;")
        layout.addWidget(label)

        # Add details section if requested
        if show_details and details:
            from PyQt5.QtWidgets import QTextEdit, QToolButton, QHBoxLayout
            details_button = QToolButton()
            details_button.setText("Show Details")
            details_button.setCheckable(True)
            details_button.setStyleSheet("font-size: 16px; margin: 8px;")
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setText(details)
            details_text.setVisible(False)
            details_text.setMinimumHeight(80)
            details_text.setStyleSheet("font-size: 14px; background: #f0f0f0;")
            def toggle_details():
                if details_button.isChecked():
                    details_button.setText("Hide Details")
                    details_text.setVisible(True)
                else:
                    details_button.setText("Show Details")
                    details_text.setVisible(False)
            details_button.toggled.connect(toggle_details)
            # Center the details button
            button_layout = QHBoxLayout()
            button_layout.addStretch(1)
            button_layout.addWidget(details_button)
            button_layout.addStretch(1)
            layout.addLayout(button_layout)
            layout.addWidget(details_text)

        btn = QPushButton("OK")
        btn.setMinimumHeight(48)
        btn.setStyleSheet("font-size: 22px; padding: 12px 0;")
        btn.clicked.connect(dialog.accept)
        layout.addWidget(btn)
        dialog.setLayout(layout)
        dialog.exec_()

    def _on_login_attempt(self, login_type, *args, **kwargs):
        """Show loading screen and forward login attempt to the correct ApiClient method, with error handling."""
        logging.info(f"Login attempt started. Type: {login_type}")
        with self.api_call_feedback(
            loading_message="Logging in...",
            error_message="Login failed. Please check your credentials, card, or network connection and try again.",
            error_title="Login Failed"
        ):
            if login_type == 'card':
                logging.info("Card login attempt.")
                self.api_client.card_login(*args, **kwargs)
            elif login_type == 'email':
                logging.info("Email login attempt.")
                self.api_client.login(*args, **kwargs)
            elif login_type == 'guest':
                logging.info("Guest login attempt.")
                self.api_client.guest_login(*args, **kwargs)
            elif login_type == 'register':
                logging.info("Register attempt.")
                self.api_client.register(*args, **kwargs)
            else:
                logging.warning(f"Unknown login attempt type: {login_type}")
        logging.info(f"Login attempt exited. Type: {login_type}")

    def handle_barcode_scanned(self, barcode):
        """Handle barcode scanned from CartScreen, fetch product, and add to cart with API context manager."""
        if not barcode:
            return
        try:
            with self.api_call_feedback(
                loading_message=f"Looking up barcode {barcode}...",
                error_message="Could not fetch product for barcode. Please try again.",
                error_title="Barcode Lookup Failed"
            ):
                resp = self.api_client.get(f"/api/products/barcode/{barcode}")
                if resp.status_code != 200:
                    self.append_serial_output(f"Barcode {barcode} not found.\n")
                    return
                product = resp.json()
                # Check if already in cart
                for p in self.products_in_cart:
                    if p['id'] == product['id']:
                        p['quantity'] += 1
                        break
                else:
                    product['quantity'] = 1
                    self.products_in_cart.append(product)
                self.cart_screen_page.set_cart_products(self.products_in_cart)
                self.update_totals()
        except Exception as e:
            self.append_serial_output(f"Error fetching product: {e}\n")

    def handle_quantity_changed(self, product_id, change):
        """Handle quantity change signal from CartScreen."""
        for product in self.products_in_cart:
            if product['id'] == product_id:
                if product['quantity'] + change > 0:
                    product['quantity'] += change
                elif product['quantity'] + change == 0:
                    self.products_in_cart = [p for p in self.products_in_cart if p['id'] != product_id]
                break
        self.cart_screen_page.set_cart_products(self.products_in_cart)
        self.update_totals()

    def handle_product_removed(self, product_id):
        """Handle product removed signal from CartScreen."""
        self.products_in_cart = [p for p in self.products_in_cart if p['id'] != product_id]
        self.cart_screen_page.set_cart_products(self.products_in_cart)
        self.update_totals()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLESHEET) # Apply the global stylesheet
    
    window = ShoppingCartApp()
    window.show()
    
    sys.exit(app.exec_())
