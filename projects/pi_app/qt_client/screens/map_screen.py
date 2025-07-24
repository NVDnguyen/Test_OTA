# qt_client/screens/map_screen.py
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QLabel, QHBoxLayout, QMessageBox, 
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QFrame, QHBoxLayout, 
    QPushButton, QGroupBox, QRadioButton, QGraphicsEllipseItem, QGraphicsPathItem
)
from PyQt5.QtGui import QPixmap, QPainter, QPen, QTransform, QColor, QBrush, QPainterPath
from PyQt5.QtCore import Qt, QPoint, QTimer, QProcess, QProcessEnvironment, QThread, pyqtSignal
import numpy as np
import requests
import subprocess
import os
import re
import time
from config import settings

# Anchor positions (update these to match your environment)
ANCHORS = [
    (0, 630),
    (5000, 5300),
    (5100, 0),
    (0, 5392)
]

class PositioningThread(QThread):
    position_updated = pyqtSignal(float, float)  # Signal emits (x, y) position
    error_occurred = pyqtSignal(str)

    def __init__(self, port, baudrate=115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = True
        self.serial_pattern = re.compile(r'0x[\da-f]{4}:\s*=(\d+)')
        self.position_history = []
        self.max_history = 20  # Keep last 20 positions for smoothing

    def run(self):
        try:
            self.ser = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=0.1
            )
            
            while self.running:
                line = self.ser.readline().decode('utf-8', errors='replace')
                if line and '=' in line:
                    dist = list(map(int, self.serial_pattern.findall(line)))
                    if len(dist) >= 4:
                        pos = self.lse_trilateration(dist[:4])
                        if not np.isnan(pos).any():
                            # Apply median filter for smoothing
                            self.position_history.append(pos)
                            if len(self.position_history) > self.max_history:
                                self.position_history.pop(0)
                            
                            filtered = np.median(np.array(self.position_history), axis=0)
                            self.position_updated.emit(filtered[0], filtered[1])
                time.sleep(0.01)  # Prevent CPU overload
        except Exception as e:
            self.error_occurred.emit(f"Positioning error: {str(e)}")
        finally:
            if hasattr(self, 'ser') and self.ser.is_open:
                self.ser.close()

    def lse_trilateration(self, distances):
        """Least Squares Estimation for trilateration"""
        if len(distances) < 4:
            return (np.nan, np.nan)
        
        x1, y1 = ANCHORS[0]
        d1 = distances[0]
        A = []
        b = []
        
        for i in range(1, 4):
            xi, yi = ANCHORS[i]
            di = distances[i]
            # Equation: 2(x_i - x1)x + 2(y_i - y1)y = (x_i^2 + y_i^2 - d_i^2) - (x1^2 + y1^2 - d1^2)
            A.append([2*(xi - x1), 2*(yi - y1)])
            b.append(xi**2 + yi**2 - di**2 - (x1**2 + y1**2 - d1**2))
        
        A = np.array(A)
        b = np.array(b)
        
        try:
            # Solve linear system
            x = np.linalg.solve(A, b)
            return x
        except np.linalg.LinAlgError:
            return (np.nan, np.nan)

    def stop(self):
        self.running = False
        self.wait()

class VirtualKeyboardLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.keyboard_process = None

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.keyboard_process is None or self.keyboard_process.state() == QProcess.NotRunning:
            try:
                self.keyboard_process = QProcess()
                self.keyboard_process.setProcessEnvironment(QProcessEnvironment.systemEnvironment())
                self.keyboard_process.start("onboard")
            except Exception as e:
                print(e)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
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
        self.map_pixmap = None
        self.zoom_level = 1.0
        self.entrance_point = {"x": 20, "y": 20}
        self.return_home_callback = return_home_callback
        self.positioning_active = False  # Track if positioning is active
        self.current_position = None
        self.trail_history = []
        self.init_ui()
        
        # Start positioning thread if serial port is configured
        if settings.SERIAL_PORT:
            self.positioning_thread = PositioningThread(
                port=settings.SERIAL_PORT,
                baudrate=settings.SERIAL_BAUDRATE
            )
            self.positioning_thread.position_updated.connect(self.update_position)
            self.positioning_thread.error_occurred.connect(self.handle_positioning_error)
            self.positioning_thread.start()

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # Map area
        self.scene = QGraphicsScene()
        self.graphics_view = QGraphicsView(self.scene)
        self.graphics_view.setDragMode(QGraphicsView.ScrollHandDrag)
        self.graphics_view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.graphics_view.viewport().installEventFilter(self)
        self.graphics_view.viewport().setMouseTracking(True)
        self.graphics_view.setStyleSheet("background: #fff;")
        main_layout.addWidget(self.graphics_view)

        # Floating control bar
        self.floating_bar = QWidget(self.graphics_view.viewport())
        self.floating_bar.setStyleSheet(
            "background: rgba(255,255,255,0.98); border-radius: 12px; border: 1.5px solid #b0b8c1;"
        )
        self.floating_bar.setMinimumWidth(0)
        self.floating_bar.setMaximumWidth(420)
        floating_layout = QVBoxLayout(self.floating_bar)
        floating_layout.setContentsMargins(8, 8, 8, 8)
        floating_layout.setSpacing(6)
        
        # Row for home button and search bar
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        # Home button
        self.home_button = QPushButton("🏠")
        self.home_button.setMinimumSize(48, 48)
        self.home_button.setMaximumSize(56, 56)
        self.home_button.setStyleSheet(
            "font-size: 26px; border-radius: 12px; border: 2px solid #bbb; background: #f5f6fa;"
        )
        self.home_button.clicked.connect(self.on_home_clicked)
        search_row.addWidget(self.home_button)

        # Search bar
        self.search_bar = VirtualKeyboardLineEdit()
        self.search_bar.setPlaceholderText("🔍 Search for a product...")
        self.search_bar.setMinimumHeight(48)
        self.search_bar.setStyleSheet(
            "padding: 10px; font-size: 20px; border-radius: 10px; border: 2px solid #bbb;"
        )
        self.search_bar.textChanged.connect(self.on_search_text_changed)
        search_row.addWidget(self.search_bar)

        floating_layout.addLayout(search_row)
        
        # Mode selection
        mode_group = QGroupBox("Map Mode")
        mode_group.setStyleSheet(
            "QGroupBox { border: 1px solid #ccc; border-radius: 8px; margin-top: 6px; padding-top: 20px; }"
            "QGroupBox::title { subcontrol-position: top center; padding: 0 5px; }"
        )
        mode_layout = QHBoxLayout(mode_group)
        
        self.product_mode_btn = QRadioButton("Product Search")
        self.product_mode_btn.setChecked(True)
        self.product_mode_btn.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.product_mode_btn)
        
        self.position_mode_btn = QRadioButton("Position Tracking")
        self.position_mode_btn.toggled.connect(self.on_mode_changed)
        mode_layout.addWidget(self.position_mode_btn)
        
        floating_layout.addWidget(mode_group)

        # Suggestions list
        self.suggestions_list = QListWidget(None)
        self.suggestions_list.setWindowFlags(Qt.ToolTip)
        self.suggestions_list.setFocusPolicy(Qt.NoFocus)
        self.suggestions_list.setStyleSheet(
            "font-size: 18px; border-radius: 8px; border: 2px solid #ddd; background: #fafbfc;"
        )
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)
        self.suggestions_list.setMaximumHeight(180)
        self.suggestions_list.hide()

        self.floating_bar.move(10, 10)
        self.floating_bar.raise_()
        self.floating_bar.show()

        self.load_map_image()
        self.marker_radius = 24
        self.last_marker_clicked = None

        # Animation timer for marker bouncing effect
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.update_marker_animation)
        self.animation_phase = 0
        self.animation_timer.start(80)

        # Create position marker
        self.position_marker = QGraphicsEllipseItem(0, 0, 30, 30)
        self.position_marker.setBrush(QBrush(QColor(0, 0, 255, 200)))
        self.position_marker.setPen(QPen(Qt.NoPen))
        self.position_marker.setZValue(100)  # Ensure it's on top
        self.scene.addItem(self.position_marker)
        self.position_marker.hide()
        
        # Create trail path
        self.trail_path = QGraphicsPathItem()
        self.trail_path.setPen(QPen(QColor(0, 0, 255, 150), 5))
        self.trail_path.setZValue(50)
        self.scene.addItem(self.trail_path)
        self.trail_path.hide()

    def on_mode_changed(self):
        if self.product_mode_btn.isChecked():
            # Switch to product search mode
            self.position_marker.hide()
            self.trail_path.hide()
            self.positioning_active = False
            self.search_bar.setEnabled(True)
            self.search_bar.setPlaceholderText("🔍 Search for a product...")
        else:
            # Switch to position tracking mode
            self.positioning_active = True
            self.search_bar.setEnabled(False)
            self.search_bar.clear()
            self.search_bar.setPlaceholderText("Position tracking active...")
            self.position_marker.show()
            self.trail_path.show()
            self.update_map_with_position()

    def update_position(self, x, y):
        """Update position and redraw map"""
        self.current_position = (x, y)
        self.trail_history.append((x, y))
        
        # Limit trail history
        if len(self.trail_history) > 50:
            self.trail_history.pop(0)
            
        self.update_map_with_position()

    def update_map_with_position(self):
        """Update position marker and trail"""
        if not self.current_position or not self.positioning_active:
            return
            
        # Update position marker
        x, y = self.current_position
        self.position_marker.setRect(x - 15, y - 15, 30, 30)
        
        # Update trail path
        path = QPainterPath()
        if self.trail_history:
            path.moveTo(*self.trail_history[0])
            for point in self.trail_history[1:]:
                path.lineTo(*point)
        self.trail_path.setPath(path)
        
        # Auto-center view on current position
        self.graphics_view.centerOn(x, y)

    def handle_positioning_error(self, error_msg):
        QMessageBox.warning(self, "Positioning Error", 
                           f"Could not connect to positioning device:\n{error_msg}")

    # Rest of the existing methods remain mostly unchanged...
    # (load_map_image, show_empty_map, on_search_text_changed, position_suggestions_list, 
    #  on_suggestion_clicked, show_product_details_popup, update_marker_animation, 
    #  update_map_with_locations, eventFilter, check_marker_click, show_marker_popup, 
    #  resizeEvent, on_home_clicked, set_api_base_url)


    def update_marker_animation(self):
        """Update animation for product markers only in product mode"""
        if not self.positioning_active:
            self.animation_phase = (self.animation_phase + 1) % 24
            self.update_map_with_locations()

    def closeEvent(self, event):
        """Clean up positioning thread when closing"""
        if hasattr(self, 'positioning_thread') and self.positioning_thread.isRunning():
            self.positioning_thread.stop()
        super().closeEvent(event)