from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                             QPushButton, QFrame)
from PyQt5.QtGui import QPixmap, QColor
from PyQt5.QtCore import Qt

class ProductWidget(QFrame):
    """A custom widget to display a single product in the cart."""
    def __init__(self, product_info, parent=None):
        super().__init__(parent)
        self.product_info = product_info
        self.setObjectName("product_frame")
        self.init_ui()

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 10)
        
        # Product Image Placeholder
        self.image_label = QLabel()
        pixmap = QPixmap(80, 80)
        pixmap.fill(QColor('#e0e0e0')) # Grey placeholder
        self.image_label.setPixmap(pixmap)
        
        # Product Details
        details_layout = QVBoxLayout()
        details_layout.setSpacing(2)
        self.name_label = QLabel(self.product_info['name'])
        self.name_label.setObjectName("product_name_label")
        self.subtitle_label = QLabel(self.product_info['subtitle'])
        self.subtitle_label.setObjectName("product_subtitle_label")
        self.remove_button = QPushButton("Remove")
        self.remove_button.setObjectName("link_button")
        self.remove_button.setCursor(Qt.PointingHandCursor)
        
        details_layout.addWidget(self.name_label)
        details_layout.addWidget(self.subtitle_label)
        details_layout.addStretch()
        details_layout.addWidget(self.remove_button)

        # Quantity Control
        quantity_layout = QHBoxLayout()
        self.minus_button = QPushButton("-")
        self.minus_button.setObjectName("quantity_button")
        self.quantity_label = QLabel(str(self.product_info['quantity']))
        self.quantity_label.setAlignment(Qt.AlignCenter)
        self.plus_button = QPushButton("+")
        self.plus_button.setObjectName("quantity_button")
        quantity_layout.addWidget(self.minus_button)
        quantity_layout.addWidget(self.quantity_label)
        quantity_layout.addWidget(self.plus_button)
        
        # Price and Total
        currency = self.product_info.get('currency', 'VND')
        self.price_label = QLabel(f"{self.product_info['price']:.2f} {currency}")
        self.price_label.setAlignment(Qt.AlignCenter)
        self.total_label = QLabel(f"{self.product_info['price'] * self.product_info['quantity']:.2f} {currency}")
        self.total_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # Add all widgets to the main layout
        layout.addWidget(self.image_label, 1)
        layout.addLayout(details_layout, 4)
        layout.addStretch(1)
        layout.addLayout(quantity_layout, 2)
        layout.addWidget(self.price_label, 2, alignment=Qt.AlignCenter)
        layout.addWidget(self.total_label, 2, alignment=Qt.AlignRight)

    def update_product_info(self, product_info):
        """Update the widget's display to reflect new product info."""
        self.product_info = product_info
        self.name_label.setText(product_info['name'])
        self.subtitle_label.setText(product_info['subtitle'])
        self.quantity_label.setText(str(product_info['quantity']))
        currency = product_info.get('currency', 'VND')
        self.price_label.setText(f"{product_info['price']:.2f} {currency}")
        self.total_label.setText(f"{product_info['price'] * product_info['quantity']:.2f} {currency}")
