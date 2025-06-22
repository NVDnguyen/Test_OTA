# screens/cart_screen.py

from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLabel, 
                             QPushButton, QFrame, QLineEdit, QComboBox, QSpacerItem, 
                             QSizePolicy)
from PyQt5.QtCore import Qt

class CartScreen(QWidget):
    """
    A QWidget representing the entire cart screen, including product list and order summary.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
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