# qt_client/screens/map_screen.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QLabel, QHBoxLayout, QMessageBox, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QHBoxLayout, QPushButton
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QTransform
from PyQt5.QtCore import Qt, QPoint, QTimer,QProcess,QProcessEnvironment

import requests
import subprocess
import os
class VirtualKeyboardLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard_process = None

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.keyboard_process is None or self.keyboard_process.state() == QProcess.NotRunning:
            try:
                self.keyboard_process = QProcess()
                # print(QProcessEnvironment.systemEnvironment().toStringList())
                self.keyboard_process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
                # Start matchbox-keyboard at the bottom of the screen
                self.keyboard_process.start("onboard", )
            except Exception as e:
                print(e)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        # Hide/close the keyboard when focus is lost
        if self.keyboard_process is not None and self.keyboard_process.state() == QProcess.Running:
            self.keyboard_process.terminate()
            self.keyboard_process.waitForFinished(1000)
            self.keyboard_process = None

class MapScreen(QWidget):
    def __init__(self, api_base_url, return_home_callback=None):
        super().__init__()
        self.api_base_url = api_base_url
        self.selected_product = None
        self.product_details = None
        self.product_locations = []
        self.map_image_url = None
        self.map_pixmap = None  # Store loaded map pixmap
        self.zoom_level = 1.0
        self.entrance_point = {"x": 20, "y": 20}  # Example entrance coordinates
        self.return_home_callback = return_home_callback  # Callback for home button
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
        self.floating_bar.setStyleSheet(
            "background: rgba(255,255,255,0.98); border-radius: 12px; border: 1.5px solid #b0b8c1;"
        )
        self.floating_bar.setMinimumWidth(0)
        self.floating_bar.setMaximumWidth(420)
        floating_layout = QVBoxLayout(self.floating_bar)
        floating_layout.setContentsMargins(8, 8, 8, 8)
        floating_layout.setSpacing(6)
        
        # Row for search bar and home button
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        # Home button
        self.home_button = QPushButton("🏠")
        self.home_button.setMinimumSize(48,48)
        self.home_button.setMaximumSize(56,56)
        self.home_button.setStyleSheet(
            "font-size: 26px; border-radius: 12px; border: 2px solid #bbb; background: #f5f6fa; padding: 0px; min-width:48px; min-height:48px; max-width:56px; max-height:56px;"
        )
        self.home_button.clicked.connect(self.on_home_clicked)
        search_row.addWidget(self.home_button)

        # Search bar
        self.search_bar = VirtualKeyboardLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search for a product...")
        self.search_bar.setMinimumHeight(48)
        self.search_bar.setStyleSheet(
            "padding: 10px; font-size: 20px; border-radius: 10px; border: 2px solid #bbb; min-height:48px;"
        )
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        search_row.addWidget(self.search_bar)

        # Add search row to floating layout
        floating_layout.addLayout(search_row)

        # Suggestions list (top-level, not stealing focus)
        self.suggestions_list = QListWidget(None)
        self.suggestions_list.setWindowFlags(Qt.ToolTip)
        self.suggestions_list.setFocusPolicy(Qt.NoFocus)
        self.suggestions_list.setStyleSheet(
            "font-size: 18px; border-radius: 8px; border: 2px solid #ddd; background: #fafbfc; min-width: 120px; min-height: 40px;"
        )
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)
        self.suggestions_list.setMaximumHeight(180)
        self.suggestions_list.hide()

        self.floating_bar.move(10, 10)
        self.floating_bar.raise_()
        self.floating_bar.show()

        self.load_map_image()
        self.marker_radius = 24  # Even larger for touch
        self.last_marker_clicked = None

        # Animation timer for marker bouncing effect
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_marker_animation)
        self.animation_phase = 0
        self.animation_timer.start(80)  # ~12.5 FPS

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
            self.suggestions_list.hide()
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
                    self.position_suggestions_list()
                    self.suggestions_list.show()
                    self.search_bar.setFocus()
                else:
                    self.suggestions_list.hide()
            else:
                self.suggestions_list.clear()
                self.suggestions_list.addItem(f"Error: {resp.status_code} {resp.reason}")
                self.position_suggestions_list()
                self.suggestions_list.show()
                self.search_bar.setFocus()
        except Exception as e:
            self.suggestions_list.clear()
            self.suggestions_list.addItem(f"Error: {str(e)}")
            self.position_suggestions_list()
            self.suggestions_list.show()
            self.search_bar.setFocus()

    def position_suggestions_list(self):
        # Position the suggestions list globally under the search bar
        search_bar_geom = self.search_bar.geometry()
        global_pos = self.search_bar.mapToGlobal(QPoint(0, search_bar_geom.height()))
        width = search_bar_geom.width()
        row_height = self.suggestions_list.sizeHintForRow(0) or 24
        visible_count = min(self.suggestions_list.count(), 6)
        height = row_height * visible_count + 4
        self.suggestions_list.setGeometry(global_pos.x(), global_pos.y(), width, height)

    def on_suggestion_clicked(self, item):
        self.suggestions_list.hide()  # Hide after selection
        product_name = item.text()
        self.selected_product = product_name
        try:
            resp = requests.get(f"{self.api_base_url}/api/map/location", params={"name": product_name})
            if resp.ok:
                product = resp.json()
                self.product_details = product
                self.product_locations = product.get("location", [])
                self.update_map_with_locations()
                # self.show_product_details_popup(product)
        except Exception as e:
            pass

    def show_product_details_popup(self, product):
        currency = product.get('currency', 'VND')
        details = f"Name: {product.get('name', '')}\n"
        details += f"Subtitle: {product.get('subtitle', '')}\n"
        details += f"Price: {product.get('price', '')} {currency} / {product.get('unit', '')}\n"
        details += f"Quantity: {product.get('quantity', '')}\n"
        QMessageBox.information(self, "Product Details", details)

    def update_marker_animation(self):
        self.animation_phase = (self.animation_phase + 1) % 24  # 24 frames per loop
        self.update_map_with_locations()

    def update_map_with_locations(self):
        if self.map_pixmap is None or not self.product_locations:
            return
        pixmap = self.map_pixmap.copy()
        painter = QPainter(pixmap)
        for idx, loc in enumerate(self.product_locations):
            x = loc.get("x", 0)
            y = loc.get("y", 0)
            marker_radius = self.marker_radius
            # Animation: bounce up and down
            bounce = int(6 * abs((self.animation_phase/12.0)-1))  # Smooth up/down
            pin_height = marker_radius * 2
            pin_width = marker_radius
            pin_center_x = int(x)
            pin_bottom_y = int(y) - bounce
            pin_top_y = pin_bottom_y - pin_height
            # Draw the pin body (ellipse/circle at top)
            pen = QPen(Qt.black)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.setBrush(Qt.red)
            painter.drawEllipse(pin_center_x - pin_width//2, pin_top_y, pin_width, pin_width)
            # Draw the pin tail (triangle)
            painter.setBrush(Qt.red)
            points = [
                QPoint(pin_center_x, pin_bottom_y),
                QPoint(pin_center_x - pin_width//2, pin_top_y + pin_width//2),
                QPoint(pin_center_x + pin_width//2, pin_top_y + pin_width//2)
            ]
            painter.drawPolygon(*points)
            # Draw white center circle
            painter.setBrush(Qt.white)
            painter.setPen(QPen(Qt.white))
            painter.drawEllipse(pin_center_x - pin_width//4, pin_top_y + pin_width//4, pin_width//2, pin_width//2)
        painter.end()
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)

    def eventFilter(self, source, event):
        if source is self.graphics_view.viewport():
            if event.type() == event.Wheel:
                angle = event.angleDelta().y()
                factor = 1.25 if angle > 0 else 0.8
                new_zoom = self.zoom_level * factor
                # Clamp zoom between 0.5x and 3x
                if 0.5 <= new_zoom <= 3.0:
                    self.graphics_view.scale(factor, factor)
                    self.zoom_level = new_zoom
                # Center map after zoom to prevent it going out of view
                if hasattr(self, 'pixmap_item') and self.pixmap_item:
                    self.graphics_view.centerOn(self.pixmap_item)
                return True
            elif event.type() == event.MouseButtonPress:
                pos = event.pos()
                scene_pos = self.graphics_view.mapToScene(pos)
                clicked = self.check_marker_click(scene_pos)
                if clicked is not None:
                    self.show_marker_popup(clicked)
                    return True
        if hasattr(self, "floating_bar"):
            self.floating_bar.move(30, 30)
            if self.suggestions_list.isVisible():
                self.position_suggestions_list()
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
            currency = self.product_details.get('currency', 'VND')
            details += f"Name: {self.product_details.get('name', '')}\n"
            details += f"Subtitle: {self.product_details.get('subtitle', '')}\n"
            details += f"Price: {self.product_details.get('price', '')} {currency} / {self.product_details.get('unit', '')}\n"
            details += f"Quantity: {self.product_details.get('quantity', '')}\n"
        QMessageBox.information(self, "Product Location Details", details)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Move floating bar to always be visible, with margin
        margin = 10
        self.floating_bar.move(margin, margin)
        # Make floating bar width responsive
        parent_width = self.graphics_view.viewport().width()
        max_width = min(420, parent_width - 2*margin)
        self.floating_bar.setFixedWidth(max_width)
        if self.suggestions_list.isVisible():
            self.position_suggestions_list()

    def on_home_clicked(self):
        if self.return_home_callback:
            self.return_home_callback()
        else:
            self.close()  # fallback: close this screen

    def set_api_base_url(self, api_base_url):
        self.api_base_url = api_base_url

    def reset_view(self):
        """Reset zoom and scroll position to default."""
        self.zoom_level = 1.0
        self.graphics_view.resetTransform()
        if hasattr(self, 'pixmap_item') and self.pixmap_item:
            self.graphics_view.centerOn(self.pixmap_item)
        else:
            self.graphics_view.centerOn(0, 0)

    # def showEvent(self, event):
    #     super().showEvent(event)
    #     if hasattr(self, 'floating_bar'):
    #         self.floating_bar.show()

    # def hideEvent(self, event):
    #     super().hideEvent(event)
    #     if hasattr(self, 'floating_bar'):
    #         self.floating_bar.hide()
