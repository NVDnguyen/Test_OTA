# screens/cart_screen.py

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QComboBox, QSpacerItem, 
                             QSizePolicy)
from PyQt5.QtCore import Qt
from widgets.product_widget import ProductWidget

class CartScreen(QWidget):
    """
    A QWidget representing the entire cart screen, including product list and order summary.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.products_in_cart = []  # To keep track of products added to the cart
        self.init_ui()

    def init_ui(self):
        cart_area_layout = QHBoxLayout(self)
        cart_area_layout.setContentsMargins(20, 20, 20, 20)
        cart_area_layout.setSpacing(20)

        # --- Left Panel: Shopping Cart ---
        self.cart_panel = self._create_cart_panel()
        cart_area_layout.addWidget(self.cart_panel, 7) # 70% width

        # --- Right Panel: Order Summary ---
        self.summary_panel = self._create_summary_panel()
        cart_area_layout.addWidget(self.summary_panel, 3) # 30% width

    def _create_cart_panel(self):
        """Creates the left panel for the shopping cart items."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)

        # Top header
        header_layout = QHBoxLayout()
        title = QLabel("Shopping Cart")
        title.setObjectName("title_label")
        self.item_count_label = QLabel("0 Items") # Initial count
        self.item_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        header_layout.addWidget(title)
        header_layout.addWidget(self.item_count_label)
        layout.addLayout(header_layout)
        
        layout.addSpacing(20)

        # Column titles
        columns_layout = QHBoxLayout()
        columns_layout.addWidget(QLabel("PRODUCT DETAILS"), 4)
        columns_layout.addStretch(3)
        columns_layout.addWidget(QLabel("QUANTITY"), 2, alignment=Qt.AlignCenter)
        columns_layout.addWidget(QLabel("PRICE"), 2, alignment=Qt.AlignCenter)
        columns_layout.addWidget(QLabel("TOTAL"), 2, alignment=Qt.AlignRight)
        
        for label in panel.findChildren(QLabel):
             if not label.objectName(): # Only apply to the column titles
                label.setObjectName("header_label")

        layout.addLayout(columns_layout)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # This layout will be populated with ProductWidget instances
        self.products_layout = QVBoxLayout()
        self.products_layout.setSpacing(10)
        layout.addLayout(self.products_layout)
        
        layout.addStretch()

        # Bottom "Continue Shopping" link
        self.continue_shopping_button = QPushButton("← Continue Shopping")
        self.continue_shopping_button.setObjectName("link_button")
        self.continue_shopping_button.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.continue_shopping_button, alignment=Qt.AlignLeft)

        return panel

    def _create_summary_panel(self):
        """Creates the right panel for the order summary."""
        panel = QFrame()
        panel.setObjectName("main_frame")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        title = QLabel("Order Summary")
        title.setObjectName("title_label")
        layout.addWidget(title)

        layout.addSpacing(10)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)

        # Subtotal
        subtotal_layout = QHBoxLayout()
        self.summary_items_header_label = QLabel("ITEMS 0") # Initial count
        subtotal_layout.addWidget(self.summary_items_header_label)
        self.subtotal_label = QLabel("£0.00") # This is for the monetary value
        self.subtotal_label.setAlignment(Qt.AlignRight)
        subtotal_layout.addWidget(self.subtotal_label)
        layout.addLayout(subtotal_layout)

        # Shipping
        layout.addWidget(QLabel("SHIPPING"))
        self.shipping_combo = QComboBox()
        self.shipping_combo.addItem("Standard Delivery - £5.00", 5.00)
        self.shipping_combo.addItem("Express Delivery - £15.00", 15.00)
        layout.addWidget(self.shipping_combo)

        # Promo Code
        layout.addWidget(QLabel("PROMO CODE"))
        self.promo_code_input = QLineEdit()
        self.promo_code_input.setPlaceholderText("Enter your code")
        layout.addWidget(self.promo_code_input)
        self.apply_button = QPushButton("APPLY")
        self.apply_button.setObjectName("apply_button")
        layout.addWidget(self.apply_button)
        
        layout.addSpacing(10)

        # Total Cost
        total_layout = QHBoxLayout()
        total_layout.addWidget(QLabel("TOTAL COST"))
        self.total_cost_label = QLabel("£0.00")
        self.total_cost_label.setObjectName("total_cost_label")
        self.total_cost_label.setAlignment(Qt.AlignRight)
        total_layout.addWidget(self.total_cost_label)
        layout.addLayout(total_layout)
        
        layout.addStretch()
        
        # Checkout Button
        self.checkout_button = QPushButton("CHECKOUT")
        self.checkout_button.setObjectName("checkout_button")
        layout.addWidget(self.checkout_button)
        
        return panel

    def clear_products_layout(self):
        """Removes all product widgets from the layout."""
        while self.products_layout.count():
            child = self.products_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def scan_barcode_and_add_item(self, barcode):
        """Look up a product by barcode from the backend and add it to the cart."""
        import requests
        from qt_client.config.settings import settings
        api_url = settings.API_BASE_URL.rstrip('/') + "/api/products/barcode/"
        try:
            resp = requests.get(api_url + barcode)
            if resp.status_code != 200:
                print(f"Barcode {barcode} not found.")
                return
            product = resp.json()
        except Exception as e:
            print(f"Error fetching product: {e}")
            return
        # Check if already in cart (by product id)
        for i in range(self.products_layout.count()):
            widget = self.products_layout.itemAt(i).widget()
            if widget and widget.property('product_id') == product['id']:
                qty_label = widget.findChild(QLabel, 'qty_label')
                if qty_label:
                    qty = int(qty_label.text()) + 1
                    qty_label.setText(str(qty))
                self.update_cart_totals()
                return
        # Add new product widget
        item_widget = QWidget()
        layout = QHBoxLayout(item_widget)
        name_label = QLabel(product['name'])
        name_label.setProperty('product_name', product['name'])
        layout.addWidget(name_label, 4)
        qty_label = QLabel('1')
        qty_label.setObjectName('qty_label')
        qty_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(qty_label, 2)
        price_label = QLabel(f"£{product['price']:.2f}")
        price_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(price_label, 2)
        total_label = QLabel(f"£{product['price']:.2f}")
        total_label.setAlignment(Qt.AlignRight)
        layout.addWidget(total_label, 2)
        item_widget.setProperty('product_id', product['id'])
        self.products_layout.addWidget(item_widget)
        self.update_cart_totals()

    def update_cart_totals(self):
        """Update item count and totals in the cart and summary."""
        count = 0
        subtotal = 0.0
        for i in range(self.products_layout.count()):
            widget = self.products_layout.itemAt(i).widget()
            if widget:
                qty_label = widget.findChild(QLabel, 'qty_label')
                if qty_label is None:
                    continue  # Skip if qty_label is missing
                price_label = widget.findChildren(QLabel)[2] if len(widget.findChildren(QLabel)) > 2 else None
                total_label = widget.findChildren(QLabel)[3] if len(widget.findChildren(QLabel)) > 3 else None
                qty = int(qty_label.text())
                price = float(price_label.text().replace('£', '')) if price_label else 0.0
                total = qty * price
                if total_label:
                    total_label.setText(f"£{total:.2f}")
                count += qty
                subtotal += total
        self.item_count_label.setText(f"{count} Items")
        self.summary_items_header_label.setText(f"ITEMS {count}")
        self.subtotal_label.setText(f"£{subtotal:.2f}")
        shipping = self.shipping_combo.currentData() or 0.0
        total_cost = subtotal + float(shipping)
        self.total_cost_label.setText(f"£{total_cost:.2f}")

    def _add_barcode_input(self):
        """Add a barcode input field and button for demo/testing."""
        barcode_layout = QHBoxLayout()
        self.barcode_input = QLineEdit()
        self.barcode_input.setPlaceholderText("Scan or enter barcode")
        barcode_layout.addWidget(self.barcode_input)
        scan_btn = QPushButton("Add by Barcode")
        scan_btn.clicked.connect(lambda: self.scan_barcode_and_add_item(self.barcode_input.text()))
        barcode_layout.addWidget(scan_btn)
        camera_btn = QPushButton()
        camera_btn.setText("Scan with Camera")
        camera_btn.setObjectName("camera_scan_button")
        camera_btn.setStyleSheet("font-size: 16px; padding: 6px 18px; border-radius: 8px; background: #eaf6ff; border: 1.5px solid #7bb1e0;")
        camera_btn.clicked.connect(self.window().open_camera_scan_screen)
        barcode_layout.addWidget(camera_btn)
        self.camera_btn = camera_btn
        # Insert at the top of the cart panel
        cart_panel_layout = self.cart_panel.layout()
        cart_panel_layout.insertLayout(1, barcode_layout)

    def open_camera_scan_screen(self):
        from screens.camera_scan_screen import CameraScanScreen
        self._previous_screen = self.parentWidget()
        self.camera_screen = CameraScanScreen(self.window())
        self.camera_screen.barcode_scanned.connect(self._on_camera_barcode_scanned)
        self.camera_screen.back_requested.connect(self._on_camera_scan_back)
        self.window().setCentralWidget(self.camera_screen)

    def _on_camera_barcode_scanned(self, barcode):
        self.barcode_input.setText(barcode)
        self.scan_barcode_and_add_item(barcode)

    def _on_camera_scan_back(self):
        if hasattr(self, '_previous_screen') and self._previous_screen:
            self.window().setCentralWidget(self._previous_screen)

    def scan_barcode_with_camera(self):
        """Open the camera, scan for a barcode, and fill the barcode input."""
        try:
            from qt_client.utils.camera_barcode import scan_barcode_from_camera
        except ImportError:
            print("Please install opencv-python and pyzbar to use camera scanning.")
            return
        found_code = scan_barcode_from_camera()
        if found_code:
            self.barcode_input.setText(found_code)
            self.scan_barcode_and_add_item(found_code)

    def showEvent(self, event):
        super().showEvent(event)
        # Ensure barcode input is added only once
        if not hasattr(self, '_barcode_input_added'):
            self._add_barcode_input()
            self._barcode_input_added = True

    def set_cart_products(self, products):
        """Set the products in the cart and update the UI."""
        self.products_in_cart = products.copy()
        self.clear_products_layout()
        self.product_widgets = {}
        for product_data in self.products_in_cart:
            product_widget = ProductWidget(product_data)
            product_widget.plus_button.clicked.connect(lambda _, p=product_data: self.change_quantity(p['id'], 1))
            product_widget.minus_button.clicked.connect(lambda _, p=product_data: self.change_quantity(p['id'], -1))
            product_widget.remove_button.clicked.connect(lambda _, p=product_data: self.remove_product(p['id']))
            self.products_layout.addWidget(product_widget)
            self.product_widgets[product_data['id']] = product_widget
        self.update_cart_totals()

    def change_quantity(self, product_id, change):
        """Change the quantity of a product in the cart."""
        for product in self.products_in_cart:
            if product['id'] == product_id:
                if product['quantity'] + change >= 0:
                    product['quantity'] += change
                    if product['quantity'] == 0:
                        self.remove_product(product_id)
                        return
                    if product_id in self.product_widgets:
                        self.product_widgets[product_id].update_product_info(product)
                break
        self.update_cart_totals()

    def remove_product(self, product_id):
        """Remove a product from the cart."""
        self.products_in_cart = [p for p in self.products_in_cart if p['id'] != product_id]
        if product_id in self.product_widgets:
            widget = self.product_widgets.pop(product_id)
            widget.setParent(None)
            widget.deleteLater()
        self.update_cart_totals()

    def get_cart_products(self):
        """Return the current list of products in the cart."""
        return self.products_in_cart.copy()

    def set_checkout_callback(self, callback):
        """Set a callback function for the checkout button."""
        self.checkout_callback = callback
        self.checkout_button.clicked.connect(callback)

    def set_continue_shopping_callback(self, callback):
        """Set a callback function for the continue shopping button."""
        self.continue_shopping_button.clicked.connect(callback)