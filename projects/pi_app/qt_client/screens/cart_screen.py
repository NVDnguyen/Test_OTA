# screens/cart_screen.py

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QComboBox, QSpacerItem, QBoxLayout,
                             QSizePolicy, QScrollArea)
from PyQt5.QtCore import Qt, pyqtSignal
from widgets.product_widget import ProductWidget
class CartScreen(QWidget):
    """
    A QWidget representing the entire cart screen, including product list and order summary.
    """
    quantity_changed = pyqtSignal(int, int)  # product_id, change
    product_removed = pyqtSignal(int)        # product_id
    def __init__(self, parent=None, currency="VND"):
        super().__init__(parent)
        self.currency = currency
        # Remove products_in_cart from CartScreen state
        self.init_ui()

    def init_ui(self):
        # Use a generic QBoxLayout to allow for orientation changes
        self.main_layout = QBoxLayout(QBoxLayout.LeftToRight, self)
        self.main_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins for small screens
        self.main_layout.setSpacing(10)

        # --- Left Panel: Shopping Cart ---
        self.cart_panel = self._create_cart_panel()
        self.cart_scroll = QScrollArea()
        self.cart_scroll.setWidgetResizable(True)
        self.cart_scroll.setWidget(self.cart_panel)
        self.main_layout.addWidget(self.cart_scroll, 7)
        # self.main_layout.addStretch(1)

        # --- Right Panel: Order Summary (Scrollable) ---
        self.summary_panel = self._create_summary_panel()
        self.summary_scroll = QScrollArea()
        self.summary_scroll.setWidgetResizable(True)
        self.summary_scroll.setWidget(self.summary_panel)
        self.main_layout.addWidget(self.summary_scroll, 3)
        self._add_barcode_input()
    def _create_cart_panel(self):
        """Creates the left panel for the shopping cart items."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        layout.setSpacing(8)

        # Top row: Continue Shopping button (left), Shopping Cart title (center), item count (right)
        top_row = QHBoxLayout()
        self.continue_shopping_button = QPushButton("← Back to Home")
        self.continue_shopping_button.setObjectName("link_button")
        self.continue_shopping_button.setCursor(Qt.PointingHandCursor)
        self.continue_shopping_button.setMinimumHeight(40)
        self.continue_shopping_button.setStyleSheet("font-size: 14px;")
        top_row.addWidget(self.continue_shopping_button, alignment=Qt.AlignLeft)

        # Centered title
        top_row.addStretch(1)
        title = QLabel("Shopping Cart")
        title.setObjectName("title_label")
        title.setStyleSheet("font-size: 17px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        top_row.addWidget(title, alignment=Qt.AlignVCenter)
        top_row.addStretch(1)

        self.item_count_label = QLabel("0 Items")
        self.item_count_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.item_count_label.setStyleSheet("font-size: 13px;")
        top_row.addWidget(self.item_count_label, alignment=Qt.AlignRight)
        layout.addLayout(top_row)
        
        layout.addSpacing(6)

        # Column titles in a container widget so we can hide/show them
        self.column_headers_widget = QWidget()
        columns_layout = QHBoxLayout(self.column_headers_widget)
        columns_layout.setContentsMargins(0, 0, 0, 0)
        columns_layout.setSpacing(2)
        columns_layout.addWidget(QLabel("PRODUCT DETAILS"), 4)
        columns_layout.addStretch(3)
        columns_layout.addWidget(QLabel("QUANTITY"), 2, alignment=Qt.AlignCenter)
        columns_layout.addWidget(QLabel("PRICE"), 2, alignment=Qt.AlignCenter)
        columns_layout.addWidget(QLabel("TOTAL"), 2, alignment=Qt.AlignRight)
        for label in self.column_headers_widget.findChildren(QLabel):
            if not label.objectName():
                label.setObjectName("header_label")
                label.setStyleSheet("font-size: 12px; font-weight: bold;")
        layout.addWidget(self.column_headers_widget)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)
        
        # This layout will be populated with ProductWidget instances
        self.products_layout = QVBoxLayout()
        self.products_layout.setSpacing(8)
        layout.addLayout(self.products_layout)
        
        layout.addStretch()

        return panel

    def _create_summary_panel(self):
        """Creates the right panel for the order summary."""
        panel = QFrame()
        panel.setObjectName("main_frame")
        panel.setMinimumWidth(180)  # Lowered for small screens
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        title = QLabel("Order Summary")
        title.setObjectName("title_label")
        title.setStyleSheet("font-size: 17px; font-weight: bold;")
        layout.addWidget(title)

        layout.addSpacing(6)
        
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setObjectName("separator")
        layout.addWidget(separator)

        # Subtotal
        subtotal_layout = QHBoxLayout()
        self.summary_items_header_label = QLabel("ITEMS 0")
        self.summary_items_header_label.setStyleSheet("font-size: 13px;")
        subtotal_layout.addWidget(self.summary_items_header_label)
        self.subtotal_label = QLabel(f"{self.currency} 0.00")
        self.subtotal_label.setAlignment(Qt.AlignRight)
        self.subtotal_label.setStyleSheet("font-size: 13px;")
        subtotal_layout.addWidget(self.subtotal_label)
        layout.addLayout(subtotal_layout)

        # Promo Code
        promo_label = QLabel("PROMO CODE")
        promo_label.setStyleSheet("font-size: 12px;")
        layout.addWidget(promo_label)
        self.promo_code_input = QLineEdit()
        self.promo_code_input.setPlaceholderText("Enter your code")
        self.promo_code_input.setMinimumHeight(36)
        self.promo_code_input.setStyleSheet("font-size: 13px;")
        layout.addWidget(self.promo_code_input)
        self.apply_button = QPushButton("APPLY")
        self.apply_button.setObjectName("apply_button")
        self.apply_button.setMinimumHeight(40)
        self.apply_button.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.apply_button)
        
        layout.addSpacing(6)

        # Total Cost
        total_layout = QHBoxLayout()
        total_label = QLabel("TOTAL COST")
        total_label.setStyleSheet("font-size: 13px;")
        total_layout.addWidget(total_label)
        self.total_cost_label = QLabel(f"{self.currency} 0.00")
        self.total_cost_label.setObjectName("total_cost_label")
        self.total_cost_label.setAlignment(Qt.AlignRight)
        self.total_cost_label.setStyleSheet("font-size: 15px; font-weight: bold;")
        total_layout.addWidget(self.total_cost_label)
        layout.addLayout(total_layout)
        
        layout.addStretch()
        
        # Checkout Button
        self.checkout_button = QPushButton("CHECKOUT")
        self.checkout_button.setObjectName("checkout_button")
        self.checkout_button.setMinimumHeight(48)
        self.checkout_button.setStyleSheet("font-size: 16px; min-width: 120px;")
        layout.addWidget(self.checkout_button)
        
        return panel

    def clear_products_layout(self):
        """Removes all product widgets from the layout."""
        while self.products_layout.count():
            child = self.products_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def set_camera_scan_callback(self, callback):
        """Expose the clicked event for the camera scan button."""
        self.camera_btn.clicked.connect(callback)

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
        barcode_layout.addWidget(camera_btn)
        self.camera_btn = camera_btn
        # Insert at the top of the cart panel
        cart_panel_layout = self.cart_panel.layout()
        cart_panel_layout.insertLayout(1, barcode_layout)

    def _on_camera_scan_back(self):
        if hasattr(self, '_previous_screen') and self._previous_screen:
            self.window().setCentralWidget(self._previous_screen)

    def showEvent(self, event):
        super().showEvent(event)

    def set_cart_products(self, products):
        """Set the products in the cart and update the UI."""
        self.clear_products_layout()
        self.product_widgets = {}
        # Set currency from first product, or default to VND
        # ANND: temporary for now
        if products and 'currency' in products[0]:
            self.currency = products[0]['currency']
        else:
            self.currency = "VND"
        if self.products_layout.parentWidget() is None:
            self.products_layout.setParent(self.cart_panel)
        count = 0
        subtotal = 0.0
        for product_data in products:
            product_widget = ProductWidget(product_data)
            from functools import partial
            product_widget.plus_button.clicked.connect(partial(self.change_quantity, product_data['id'], 1))
            product_widget.minus_button.clicked.connect(partial(self.change_quantity, product_data['id'], -1))
            product_widget.remove_button.clicked.connect(partial(self.remove_product, product_data['id']))
            self.products_layout.addWidget(product_widget)
            self.product_widgets[product_data['id']] = product_widget
        # Calculate totals using products list/dict
        for product_data in products:
            qty = int(product_data.get('quantity', 0))
            price = float(str(product_data.get('price', 0)))
            total = qty * price
            # Update the widget's total label if available
            product_widget = self.product_widgets.get(product_data['id'])
            count += qty
            subtotal += total
        self.item_count_label.setText(f"{count} Items")
        self.summary_items_header_label.setText(f"ITEMS {count}")
        self.subtotal_label.setText(f"{self.currency} {subtotal:.2f}")
        self.total_cost_label.setText(f"{self.currency} {subtotal:.2f}")
        self.cart_panel.update()
        self.cart_panel.repaint()
        self.update()
        self.repaint()

    def change_quantity(self, product_id, change):
        """Emit a signal to main to change the quantity of a product in the cart."""
        self.quantity_changed.emit(product_id, change)

    def remove_product(self, product_id):
        """Emit a signal to main to remove a product from the cart."""
        self.product_removed.emit(product_id)
        
    def set_checkout_callback(self, callback):
        """Set a callback function for the checkout button."""
        self.checkout_callback = callback
        self.checkout_button.clicked.connect(callback)

    def set_continue_shopping_callback(self, callback):
        """Set a callback function for the continue shopping button."""
        self.continue_shopping_button.clicked.connect(callback)

    def resizeEvent(self, event):
        """Responds to window resize events to adjust the layout."""
        super().resizeEvent(event)
        breakpoint = 750
        is_narrow = self.width() < breakpoint
        current_direction = self.main_layout.direction()

        if is_narrow and current_direction != QBoxLayout.TopToBottom:
            self.main_layout.setDirection(QBoxLayout.TopToBottom)
            self.main_layout.setStretch(0, 0)
            self.main_layout.setStretch(1, 1)
            self.column_headers_widget.hide()
            self.summary_panel.setMinimumWidth(0)
            self.cart_scroll.setMaximumHeight(320)  # Limit cart height in vertical mode
            self.summary_panel.layout().setSpacing(12)
        elif not is_narrow and current_direction != QBoxLayout.LeftToRight:
            self.main_layout.setDirection(QBoxLayout.LeftToRight)
            self.main_layout.setStretch(0, 7)
            self.main_layout.setStretch(1, 3)
            self.column_headers_widget.show()
            self.summary_panel.setMinimumWidth(180)
            self.cart_scroll.setMaximumHeight(16777215)
            self.summary_panel.layout().setSpacing(8)