# qt_client/screens/map_screen.py
import sys
import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QListWidget, QLabel, QHBoxLayout, 
    QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt, QPoint, QTimer, QProcess, QProcessEnvironment
from PyQt5.QtGui import QColor
from PIL import Image
import requests
from utils.serial_reader import UWBSerialReader
import time
import io 

Image.MAX_IMAGE_PIXELS = None

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
        self.return_home_callback = return_home_callback
        
        # tracking atribute
        self.uwb_reader = None
        self.position_history = []
        self.trail_history = []
        self.target = None
        self.fps_time = time.time()
        self.tracking_mode = False  #mode
        
        self.init_ui()
        
        # Timer 
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(10)  # ~100 FPS

    def init_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        # PlotWidget
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('w')
        main_layout.addWidget(self.plot_widget)

        # Load image
        self.load_map_image()

        # Floating search bar
        self.floating_bar = QWidget(self)
        self.floating_bar.setStyleSheet(
            "background: rgba(255,255,255,0.98); border-radius: 12px; border: 1.5px solid #b0b8c1;"
        )
        self.floating_bar.setMinimumWidth(0)
        self.floating_bar.setMaximumWidth(420)
        
        floating_layout = QVBoxLayout(self.floating_bar)
        floating_layout.setContentsMargins(8, 8, 8, 8)
        floating_layout.setSpacing(6)
        
        # Search row
        search_row = QHBoxLayout()
        search_row.setSpacing(6)

        # Home button
        self.home_button = QPushButton("🏠")
        self.home_button.setMinimumSize(48, 48)
        self.home_button.setMaximumSize(56, 56)
        self.home_button.setStyleSheet(
            "font-size: 26px; border-radius: 12px; border: 2px solid #bbb; "
            "background: #f5f6fa; padding: 0px;"
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

        # Tracking Mode button
        self.tracking_button = QPushButton("Tracking Mode")
        self.tracking_button.setMinimumSize(150, 48)
        self.tracking_button.setStyleSheet(
            "font-size: 20px; border-radius: 12px; border: 2px solid #bbb; "
            "background: #f5f6fa; padding: 0px;"
        )
        self.tracking_button.clicked.connect(self.toggle_tracking_mode)
        search_row.addWidget(self.tracking_button)

        floating_layout.addLayout(search_row)

        # Suggestions list
        self.suggestions_list = QListWidget(None)
        self.suggestions_list.setWindowFlags(Qt.ToolTip)
        self.suggestions_list.setFocusPolicy(Qt.NoFocus)
        self.suggestions_list.setStyleSheet(
            "font-size: 18px; border-radius: 8px; border: 2px solid #ddd; "
            "background: #fafbfc; min-width: 120px; min-height: 40px;"
        )
        self.suggestions_list.itemClicked.connect(self.on_suggestion_clicked)
        self.suggestions_list.setMaximumHeight(180)
        self.suggestions_list.hide()

        # floating
        self.floating_bar.move(10, 10)
        self.floating_bar.raise_()
        self.floating_bar.show()

    def load_map_image(self):
        try:
            #v backend img
            resp = requests.get(f"{self.api_base_url}/api/map/map_image")
            if resp.ok:
                image_bytes = resp.content
                
                # img process
                img = Image.open(io.BytesIO(image_bytes))
                arr = np.array(img)
                arr = np.rot90(arr, k=3) 

                # ImageItem
                self.bg = pg.ImageItem(arr)
                self.bg.setZValue(-200)  # back filter 
                self.bg.setRect(0, 0, 1600, 1300)
                self.plot_widget.addItem(self.bg)

                # limit 
                self.plot_widget.setXRange(0, 1600)
                self.plot_widget.setYRange(0, 1300)
                self.plot_widget.setLimits(
                    xMin=0, xMax=1600,
                    yMin=0, yMax=1300
                )
                
                # UI
                self.target_scatter = self.plot_widget.plot(
                    [], [], pen=None, symbol='x', symbolSize=20,
                    symbolBrush='g'
                )
                self.path_curve = self.plot_widget.plot(
                    [], [], pen=pg.mkPen('r', width=4)
                )
                self.fpt_scatter = self.plot_widget.plot(
                    [], [], pen=None,
                    symbol='o', symbolSize=40,
                    symbolBrush=pg.mkBrush(QColor(0, 255, 255, 200))
                )
                self.trail_curve = self.plot_widget.plot(
                    [], [], pen=pg.mkPen(QColor(0, 255, 255, 150), width=1)
                )
                self.fpt_text = pg.TextItem(
                    text="SCI", color='r',
                    anchor=(0.5, -1.0)
                )
                self.plot_widget.addItem(self.fpt_text)
                
                # hide 
                self.fpt_scatter.hide()
                self.trail_curve.hide()
                self.fpt_text.hide()
                
                # Click
                self.plot_widget.scene().sigMouseClicked.connect(self.on_click)
        except Exception as e:
            print(f"Error loading map image: {e}")

    def on_click(self, ev):
        """Click to show shortest path"""
        pos = ev.scenePos()
        vb = self.plot_widget.getViewBox()
        mp = vb.mapSceneToView(pos)
        x, y = mp.x(), mp.y()
        if 0 <= x <= 1300 and 0 <= y <= 1600:
            self.target = np.array([x, y])
            self.target_scatter.setData([x], [y])
            self.path_curve.setData([], [])

    def toggle_tracking_mode(self):
        if self.tracking_button.text() == "Tracking Mode":
            self.start_tracking()
            self.tracking_button.setText("Stop Tracking")
        else:
            self.stop_tracking()
            self.tracking_button.setText("Tracking Mode")
    
    def start_tracking(self):
        """tracking mode"""
        if self.uwb_reader is None:
            self.uwb_reader = UWBSerialReader(port='/dev/ttyACM0', baudrate=115200)
        
        if not self.uwb_reader.start_reading():
            QMessageBox.warning(self, "Connection Error", "Could not connect to UWB device.")
            self.tracking_button.setText("Tracking Mode")
            return
        
        # Show
        self.fpt_scatter.show()
        self.trail_curve.show()
        self.fpt_text.show()
        
        # reset history cor
        self.position_history = []
        self.trail_history = []
        
        self.tracking_mode = True

    def stop_tracking(self):
        """Dừng chế độ tracking"""
        if self.uwb_reader:
            self.uwb_reader.stop_reading()
        
        # hide
        self.fpt_scatter.hide()
        self.trail_curve.hide()
        self.fpt_text.hide()
        
        self.tracking_mode = False

    def update_plot(self):
        """Cập nhật vị trí tag"""
        if not self.tracking_mode or not self.uwb_reader or not self.uwb_reader.is_reading:
            return
        
        raw_data = self.uwb_reader.get_latest_data()
        if not raw_data:
            return
        
        # process raw
        pos = self.uwb_reader.process_data(raw_data)
        if pos is None:
            return
        
        # Median filter
        self.position_history.append(pos)
        if len(self.position_history) > 100:
            self.position_history.pop(0)
        filtered = np.median(np.array(self.position_history), axis=0)
        x, y = filtered[0], filtered[1]
        
        # draw TAG
        self.fpt_scatter.setData([x], [y])
        self.fpt_text.setPos(x, y)
        
        # draw trail
        self.trail_history.append(filtered)
        if len(self.trail_history) > 200:
            self.trail_history.pop(0)
        trail = np.array(self.trail_history)
        self.trail_curve.setData(trail[:,0], trail[:,1])
        
        # Vdraw shortest path
        if self.target is not None:
            lx = [x, self.target[0]]
            ly = [y, self.target[1]]
            self.path_curve.setData(lx, ly)
        
        # FPS
        now = time.time()
        fps = 1.0 / (now - self.fps_time)
        self.fps_time = now
        self.setWindowTitle(f"UWB Tracking (FPS: {fps:.1f})")

    def on_search_text_changed(self, text):
        if not text:
            self.suggestions_list.clear()
            self.suggestions_list.hide()
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
        except Exception as e:
            pass

    def show_product_details_popup(self, product):
        details = f"Name: {product.get('name', '')}\n"
        details += f"Subtitle: {product.get('subtitle', '')}\n"
        details += f"Price: {product.get('price', '')} {product.get('unit', '')}\n"
        details += f"Quantity: {product.get('quantity', '')}\n"
        QMessageBox.information(self, "Product Details", details)

    def update_map_with_locations(self):
        # tick point
        if not self.product_locations:
            return
        
        # delete old point
        if hasattr(self, 'product_markers'):
            for marker in self.product_markers:
                self.plot_widget.removeItem(marker)
        
        self.product_markers = []
        
        # new tick point
        for loc in self.product_locations:
            x = loc.get("x", 0)
            y = loc.get("y", 0)
            
            # marker
            marker = pg.ScatterPlotItem([x], [y], size=20, symbol='s', 
                                        brush=pg.mkBrush(QColor(255, 0, 0, 200)),
                                        pen=pg.mkPen(QColor(0, 0, 0)))
            self.plot_widget.addItem(marker)
            self.product_markers.append(marker)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # floating bar
        margin = 10
        self.floating_bar.move(margin, margin)
        # resize width
        parent_width = self.width()
        max_width = min(420, parent_width - 2 * margin)
        self.floating_bar.setFixedWidth(max_width)
        if self.suggestions_list.isVisible():
            self.position_suggestions_list()

    def on_home_clicked(self):
        if self.return_home_callback:
            self.return_home_callback()
        else:
            self.close()

    def set_api_base_url(self, api_base_url):
        self.api_base_url = api_base_url

    def closeEvent(self, event):
        self.stop_tracking()
        super().closeEvent(event)