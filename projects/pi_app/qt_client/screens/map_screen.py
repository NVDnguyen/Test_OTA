# qt_client/screens/map_screen.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QLabel, QHBoxLayout, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QHBoxLayout
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QTransform
from PyQt5.QtCore import Qt, QPointF
import requests

class MapScreen(QWidget):
    def __init__(self, api_base_url):
        super().__init__()
        self.api_base_url = api_base_url
        self.selected_product = None
        self.product_details = None
        self.product_locations = []
        self.map_image_url = None
        self.map_pixmap = None  # Store loaded map pixmap
        self.zoom_level = 1.0
        self.entrance_point = {"x": 20, "y": 20}  # Example entrance coordinates
        self.init_ui()

    def init_ui(self):
        # Main layout: map fills all, search bar floats at top
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Map area (fills all space)
        self.scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.viewport().installEventFilter(self)
        self.graphics_view.viewport().setMouseTracking(True)
        self.graphics_view.setStyleSheet("background: #fff;")
        main_layout.addWidget(self.graphics_view)

        # Floating search bar container (child widget, not top-level)
        self.floating_bar = QWidget(self.graphics_view.viewport())
        self.floating_bar.setStyleSheet("background: rgba(255,255,255,0.95); border-radius: 12px; border: 1.5px solid #b0b8c1;")
        self.floating_bar.setFixedWidth(420)
        floating_layout = QVBoxLayout(self.floating_bar)
        floating_layout.setContentsMargins(18, 12, 18, 12)
        floating_layout.setSpacing(8)

        # Title
        title = QLabel("Product Map Search")
        title.setAlignment(Qt.AlignLeft)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 2px;")
        floating_layout.addWidget(title)

        # Search bar
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search for a product...")
        self.search_bar.setStyleSheet("padding: 8px; font-size: 16px; border-radius: 8px; border: 1px solid #bbb;")
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        floating_layout.addWidget(self.search_bar)

        # Suggestions list
        self.suggestions_list = QListWidget()
        self.suggestions_list.setStyleSheet("font-size: 15px; border-radius: 6px; border: 1px solid #ddd; background: #fafbfc;")
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)
        self.suggestions_list.setMaximumHeight(120)
        floating_layout.addWidget(self.suggestions_list)

        self.floating_bar.move(30, 30)
        self.floating_bar.raise_()
        self.floating_bar.show()  # <-- Add this line

        self.load_map_image()
        self.marker_radius = 12  # For click detection
        self.last_marker_clicked = None
    def load_map_image(self):
        try:
            resp = requests.get(f"{self.api_base_url}/api/map/map_image")
            if resp.ok:
                image_bytes = resp.content
                pixmap = QPixmap()
                pixmap.loadFromData(image_bytes)
                self.scene.clear()
                self.pixmap_item = QGraphicsPixmapItem(pixmap)
                self.scene.addItem(self.pixmap_item)
                self.pixmap_item.setZValue(-1000)  # Ensure map image is at the lowest z-index
                self.map_pixmap = pixmap  # Store the pixmap for later drawing
                self.map_image_url = None  # Not a URL anymore
        except Exception as e:
            pass

    def show_empty_map(self):
        """Show the map image with no product locations."""
        if not self.map_image_url:
            self.load_map_image()
        else:
            pixmap = QPixmap(self.map_image_url)
            self.scene.clear()
            self.pixmap_item = QGraphicsPixmapItem(pixmap)
            self.scene.addItem(self.pixmap_item)

    def on_search_text_changed(self, text):
        if not text:
            self.suggestions_list.clear()
            self.product_locations = []
            self.product_details = None
            self.show_empty_map()
            return
        try:
            resp = requests.get(f"{self.api_base_url}/api/map/search", params={"q": text})
            if resp.ok:
                suggestions = resp.json()
                self.suggestions_list.clear()
                if suggestions:
                    self.suggestions_list.addItems(suggestions)
                else:
                    self.suggestions_list.addItem("No results found.")
            else:
                self.suggestions_list.clear()
                self.suggestions_list.addItem(f"Error: {resp.status_code} {resp.reason}")
        except Exception as e:
            self.suggestions_list.clear()
            self.suggestions_list.addItem(f"Error: {str(e)}")

    def on_suggestion_clicked(self, item):
        product_name = item.text()
        self.selected_product = product_name
        try:
            resp = requests.get(f"{self.api_base_url}/api/map/location", params={"name": product_name})
            if resp.ok:
                product = resp.json()
                self.product_details = product
                self.product_locations = product.get("location", [])
                self.update_map_with_locations()
                self.show_product_details_popup(product)
        except Exception as e:
            pass

    def show_product_details_popup(self, product):
        details = f"Name: {product.get('name', '')}\n"
        details += f"Subtitle: {product.get('subtitle', '')}\n"
        details += f"Price: {product.get('price', '')} {product.get('unit', '')}\n"
        details += f"Quantity: {product.get('quantity', '')}\n"
        QMessageBox.information(self, "Product Details", details)

    def update_map_with_locations(self):
        if self.map_pixmap is None or not self.product_locations:
            return
        pixmap = self.map_pixmap.copy()
        painter = QPainter(pixmap)
        pen = QPen(Qt.red)
        pen.setWidth(10)
        painter.setPen(pen)
        # Draw product locations
        for loc in self.product_locations:
            x = loc.get("x", 0)
            y = loc.get("y", 0)
            painter.drawPoint(x, y)
        # Draw path from entrance to the first product location
        if self.product_locations:
            pen_path = QPen(Qt.blue)
            pen_path.setWidth(4)
            painter.setPen(pen_path)
            entrance_x = self.entrance_point["x"]
            entrance_y = self.entrance_point["y"]
            for loc in self.product_locations:
                x = loc.get("x", 0)
                y = loc.get("y", 0)
                painter.drawLine(entrance_x, entrance_y, x, y)
        painter.end()
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

    def eventFilter(self, source, event):
        if source is self.graphics_view.viewport():
            if event.type() == event.Wheel:
                angle = event.angleDelta().y()
                factor = 1.25 if angle > 0 else 0.8
                self.graphics_view.scale(factor, factor)
                return True
            elif event.type() == event.MouseButtonPress:
                pos = event.pos()
                scene_pos = self.graphics_view.mapToScene(pos)
                clicked = self.check_marker_click(scene_pos)
                if clicked is not None:
                    self.show_marker_popup(clicked)
                    return True
        return super().eventFilter(source, event)

    def check_marker_click(self, scene_pos):
        # Returns the index of the marker clicked, or None
        if not self.product_locations:
            return None
        for idx, loc in enumerate(self.product_locations):
            x = loc.get("x", 0)
            y = loc.get("y", 0)
            dist = ((scene_pos.x() - x) ** 2 + (scene_pos.y() - y) ** 2) ** 0.5
            if dist <= self.marker_radius:
                return idx
        return None

    def show_marker_popup(self, idx):
        loc = self.product_locations[idx]
        details = f"Location: ({loc.get('x', '')}, {loc.get('y', '')})\n"
        if self.product_details:
            details += f"Name: {self.product_details.get('name', '')}\n"
            details += f"Subtitle: {self.product_details.get('subtitle', '')}\n"
            details += f"Price: {self.product_details.get('price', '')} {self.product_details.get('unit', '')}\n"
            details += f"Quantity: {self.product_details.get('quantity', '')}\n"
        QMessageBox.information(self, "Product Location Details", details)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.floating_bar.move(30, 30)

    # def showEvent(self, event):
    #     super().showEvent(event)
    #     if hasattr(self, 'floating_bar'):
    #         self.floating_bar.show()

    # def hideEvent(self, event):
    #     super().hideEvent(event)
    #     if hasattr(self, 'floating_bar'):
    #         self.floating_bar.hide()
