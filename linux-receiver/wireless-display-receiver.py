#!/usr/bin/env python3
"""
Wireless Display Receiver for Linux Mint
VNC Server + PyQt6 UI for virtual display management
"""

import sys
import socket
import threading
import struct
import zlib
import argparse
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QLabel, QPushButton, QLineEdit,
                             QTextEdit, QSystemTrayIcon, QMenu, QMessageBox,
                             QGroupBox, QComboBox, QCheckBox)
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, Qt
from PyQt6.QtGui import QIcon, QAction, QPainter, QColor, QBrush, QPen

# Constants
DEFAULT_PORT = 5900
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
DEFAULT_BPP = 32

class VNCServer:
    """Minimal RFB (VNC) Protocol Server"""

    def __init__(self, port=DEFAULT_PORT, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        self.port = port
        self.width = width
        self.height = height
        self.clients = []
        self.running = False
        self.server_socket = None
        self.lock = threading.Lock()

    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        self.server_socket.listen(5)
        self.server_socket.settimeout(1.0)
        self.running = True

    def stop(self):
        self.running = False
        with self.lock:
            for client in self.clients:
                try:
                    client.close()
                except:
                    pass
            self.clients.clear()
        if self.server_socket:
            self.server_socket.close()

    def handle_client(self, client_socket, addr):
        try:
            client_socket.send(b'RFB 003.008\n')
            version = client_socket.recv(12)
            client_socket.send(b'\x01\x00')
            shared = client_socket.recv(1)
            self.send_server_init(client_socket)
            while self.running:
                try:
                    msg_type = client_socket.recv(1)
                    if not msg_type:
                        break
                    msg_type = ord(msg_type)
                    if msg_type == 0:
                        client_socket.recv(3)
                        client_socket.recv(16)
                    elif msg_type == 2:
                        client_socket.recv(1)
                        count = struct.unpack('!H', client_socket.recv(2))[0]
                        client_socket.recv(count * 4)
                    elif msg_type == 3:
                        incremental = client_socket.recv(1)
                        x = struct.unpack('!H', client_socket.recv(2))[0]
                        y = struct.unpack('!H', client_socket.recv(2))[0]
                        w = struct.unpack('!H', client_socket.recv(2))[0]
                        h = struct.unpack('!H', client_socket.recv(2))[0]
                        self.send_framebuffer_update(client_socket, x, y, w, h)
                    elif msg_type == 4:
                        client_socket.recv(7)
                    elif msg_type == 5:
                        client_socket.recv(5)
                    elif msg_type == 6:
                        client_socket.recv(3)
                        length = struct.unpack('!I', client_socket.recv(4))[0]
                        client_socket.recv(length)
                except:
                    break
        except:
            pass
        finally:
            client_socket.close()
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)

    def send_server_init(self, client_socket):
        client_socket.send(struct.pack('!H', self.width))
        client_socket.send(struct.pack('!H', self.height))
        name = 'Wireless Display'
        client_socket.send(struct.pack('!B', 0))
        client_socket.send(struct.pack('!BBHHHBBBBBBBBB',
            DEFAULT_BPP, 0, 1, 255, 255, 255, 16, 8, 0))
        client_socket.send(struct.pack('!BBB', 0, 0, 0))
        client_socket.send(struct.pack('!I', len(name)))
        client_socket.send(name.encode())

    def send_framebuffer_update(self, client_socket, x, y, w, h):
        client_socket.send(struct.pack('!B', 0))
        client_socket.send(struct.pack('!B', 0))
        client_socket.send(struct.pack('!H', 1))
        client_socket.send(struct.pack('!H', x))
        client_socket.send(struct.pack('!H', y))
        client_socket.send(struct.pack('!H', w))
        client_socket.send(struct.pack('!H', h))
        client_socket.send(struct.pack('!i', 0))
        pixels = []
        for row in range(h):
            for col in range(w):
                r = int(30 + (col / w) * 30)
                g = int(30 + (row / h) * 30)
                b = int(80 + ((col + row) / (w + h)) * 40)
                pixels.extend([r, g, b, 255])
        client_socket.send(bytes(pixels))

    def accept_client(self):
        while self.running:
            try:
                client_socket, addr = self.server_socket.accept()
                with self.lock:
                    self.clients.append(client_socket)
                thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                thread.daemon = True
                thread.start()
            except socket.timeout:
                continue
            except:
                if self.running:
                    pass

class ServerThread(QThread):
    log_signal = pyqtSignal(str)
    status_signal = pyqtSignal(bool)

    def __init__(self, port, width, height):
        super().__init__()
        self.port = port
        self.width = width
        self.height = height
        self.server = None
        self.running = False

    def run(self):
        self.server = VNCServer(self.port, self.width, self.height)
        self.running = True
        try:
            self.server.start()
            self.status_signal.emit(True)
            self.log_signal.emit(f"Server started on port {self.port}")
            self.server.accept_client()
        except Exception as e:
            self.log_signal.emit(f"Server error: {e}")
            self.status_signal.emit(False)

    def stop(self):
        self.running = False
        if self.server:
            self.server.stop()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.server_thread = None
        self.settings_file = os.path.expanduser('~/.wireless-display-receiver.json')
        self.load_settings()
        self.init_ui()
        self.init_tray()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r') as f:
                    self.settings = json.load(f)
            else:
                self.settings = {
                    'port': DEFAULT_PORT,
                    'width': DEFAULT_WIDTH,
                    'height': DEFAULT_HEIGHT,
                    'auto_start': False
                }
        except:
            self.settings = {
                'port': DEFAULT_PORT,
                'width': DEFAULT_WIDTH,
                'height': DEFAULT_HEIGHT,
                'auto_start': False
            }

    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except:
            pass

    def init_ui(self):
        self.setWindowTitle('Wireless Display Receiver')
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        status_group = QGroupBox("Server Status")
        status_layout = QVBoxLayout()
        self.status_label = QLabel("Status: Stopped")
        self.status_label.setStyleSheet("font-size: 14pt; font-weight: bold;")
        status_layout.addWidget(self.status_label)
        self.ip_label = QLabel("IP: --")
        status_layout.addWidget(self.ip_label)
        self.port_label = QLabel(f"Port: {self.settings['port']}")
        status_layout.addWidget(self.port_label)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        controls_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Server")
        self.start_button.clicked.connect(self.start_server)
        controls_layout.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop Server")
        self.stop_button.clicked.connect(self.stop_server)
        self.stop_button.setEnabled(False)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        settings_group = QGroupBox("Settings")
        settings_layout = QVBoxLayout()
        resolution_layout = QHBoxLayout()
        resolution_layout.addWidget(QLabel("Resolution:"))
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['1920x1080', '1280x720', '1600x900', '1366x768'])
        self.resolution_combo.setCurrentText(f"{self.settings['width']}x{self.settings['height']}")
        resolution_layout.addWidget(self.resolution_combo)
        resolution_layout.addStretch()
        settings_layout.addLayout(resolution_layout)
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_input = QLineEdit(str(self.settings['port']))
        port_layout.addWidget(self.port_input)
        port_layout.addStretch()
        settings_layout.addLayout(port_layout)
        self.auto_start_check = QCheckBox("Start server on application launch")
        self.auto_start_check.setChecked(self.settings.get('auto_start', False))
        settings_layout.addWidget(self.auto_start_check)
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        central_widget.setLayout(layout)
        self.update_local_ip()

    def init_tray(self):
        self.tray = QSystemTrayIcon(self)
        self.tray.setToolTip("Wireless Display Receiver")
        menu = QMenu()
        menu.addAction("Show", self.show)
        menu.addAction("Hide", self.hide)
        menu.addSeparator()
        menu.addAction("Quit", self.quit_app)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self.tray_clicked)

    def tray_clicked(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show()

    def update_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            self.ip_label.setText(f"IP: {ip}")
        except:
            self.ip_label.setText("IP: Unable to detect")

    def start_server(self):
        try:
            port = int(self.port_input.text())
            resolution = self.resolution_combo.currentText().split('x')
            width, height = int(resolution[0]), int(resolution[1])
            self.settings['port'] = port
            self.settings['width'] = width
            self.settings['height'] = height
            self.settings['auto_start'] = self.auto_start_check.isChecked()
            self.save_settings()
            self.log("Starting server...")
            self.server_thread = ServerThread(port, width, height)
            self.server_thread.log_signal.connect(self.log)
            self.server_thread.status_signal.connect(self.on_server_status)
            self.server_thread.start()
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to start server: {e}")

    def stop_server(self):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
            self.server_thread = None
        self.log("Server stopped")
        self.status_label.setText("Status: Stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def on_server_status(self, running):
        if running:
            self.status_label.setText("Status: Running")
            self.status_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: green;")
        else:
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("font-size: 14pt; font-weight: bold;")

    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")

    def closeEvent(self, event):
        if self.server_thread:
            self.server_thread.stop()
            self.server_thread.wait()
        event.accept()

    def quit_app(self):
        self.close()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Wireless Display Receiver")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()
