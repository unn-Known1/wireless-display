#!/usr/bin/env python3
"""
Wireless Display Receiver
VNC server that streams desktop to Android TV
"""

import socket
import threading
import struct
import sys
import time
import subprocess
from io import BytesIO
from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QIcon, QAction

# VNC Protocol Constants
RFB_VERSION = b'RFB 003.008\n'
CLIENT_INIT = 0
SERVER_INIT = 1
SET_PIXEL_FORMAT = 0
SET_ENCODINGS = 2
FRAMEBUFFER_UPDATE_REQUEST = 3
KEY_EVENT = 4
POINTER_EVENT = 5
CLIENT_CUT_TEXT = 6

ENCODING_RAW = 0
ENCODING_COPY_RECT = 1
ENCODING_DESKTOP_SIZE = -223

class VNCServer:
    def __init__(self, host='0.0.0.0', port=5900):
        self.host = host
        self.port = port
        self.client_socket = None
        self.running = False
        self.width = 1920
        self.height = 1080
        self.framebuffer = None
        
    def start(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(1)
        self.server_socket.settimeout(1.0)
        self.running = True
        print(f"VNC Server started on {self.host}:{self.port}")
        
        while self.running:
            try:
                client, addr = self.server_socket.accept()
                print(f"Client connected from {addr}")
                threading.Thread(target=self.handle_client, args=(client,)).start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"Error: {e}")
                break
    
    def handle_client(self, client):
        try:
            # Version handshake
            client.sendall(RFB_VERSION)
            version = client.recv(12)
            print(f"Client version: {version.decode()}")
            
            # Security handshake (no auth)
            client.sendall(b'\x01\x01')  # 1 type, no security
            client.sendall(b'\x00\x00\x00\x00')  # Accept
            
            # Client init (shared flag)
            shared = client.recv(1)
            
            # Server init
            self.send_server_init(client)
            
            # Handle client messages
            while self.running:
                msg_type = client.recv(1)
                if not msg_type:
                    break
                self.handle_message(client, msg_type[0])
                
        except Exception as e:
            print(f"Client error: {e}")
        finally:
            client.close()
            print("Client disconnected")
    
    def send_server_init(self, client):
        # Framebuffer size
        name = b"Wireless Display"
        name_len = len(name)
        
        # Security result (accepted)
        # Already sent earlier
        
        # Server init
        msg = struct.pack('>HH', self.width, self.height)
        msg += struct.pack('!BBBBHHHBBB', 
            32,  # bits per pixel
            24,  # depth
            0,   # big endian
            1,   # true color
            255, # red max
            255, # green max
            255, # blue max
            16,  # red shift
            8,   # green shift
            0    # blue shift
        )
        msg += struct.pack('!BBB', 0, 0, 0)  # padding
        msg += struct.pack('>I', name_len)
        msg += name
        client.sendall(msg)
    
    def handle_message(self, client, msg_type):
        if msg_type == SET_PIXEL_FORMAT:
            client.recv(19)  # Skip pixel format
        elif msg_type == SET_ENCODINGS:
            count = struct.unpack('!H', client.recv(2))[0]
            client.recv(count * 4)  # Skip encodings
        elif msg_type == FRAMEBUFFER_UPDATE_REQUEST:
            client.recv(1)  # Skip incremental
            x, y, w, h = struct.unpack('!HHHH', client.recv(8))
            self.send_framebuffer_update(client)
        elif msg_type == KEY_EVENT or msg_type == POINTER_EVENT or msg_type == CLIENT_CUT_TEXT:
            # Skip for now
            pass
    
    def send_framebuffer_update(self, client):
        # Header
        msg = struct.pack('!Bx', FRAMEBUFFER_UPDATE_REQUEST)  # 0
        msg += struct.pack('!H', 1)  # 1 rectangle
        
        # Rectangle header
        msg += struct.pack('!HHHH', 0, 0, self.width, self.height)
        msg += struct.pack('!i', ENCODING_RAW)
        
        # Pixel data (simple gradient for demo)
        try:
            # Try to get screenshot
            result = subprocess.run(
                ['scrot', '-o', '-'],
                capture_output=True,
                timeout=2
            )
            if result.returncode == 0:
                # Convert to raw RGB
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(result.stdout))
                img = img.resize((self.width, self.height))
                img = img.convert('RGB')
                pixels = img.tobytes()
            else:
                pixels = self.generate_fallback_frame()
        except Exception:
            pixels = self.generate_fallback_frame()
        
        msg += pixels
        client.sendall(msg)
    
    def generate_fallback_frame(self):
        """Generate a simple fallback frame"""
        pixels = bytearray()
        for y in range(self.height):
            for x in range(self.width):
                # Gradient pattern
                r = int((x / self.width) * 255)
                g = int((y / self.height) * 255)
                b = 128
                pixels.extend([r, g, b])
        return bytes(pixels)
    
    def stop(self):
        self.running = False
        if hasattr(self, 'server_socket'):
            self.server_socket.close()


class TrayApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.server = VNCServer()
        self.server_thread = None
        
        # Setup tray
        self.tray = QSystemTrayIcon()
        self.tray.setToolTip("Wireless Display Receiver")
        
        # Create menu
        menu = QMenu()
        
        self.status_action = QAction("Status: Stopped")
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        
        menu.addSeparator()
        
        start_action = QAction("Start Server")
        start_action.triggered.connect(self.start_server)
        menu.addAction(start_action)
        
        stop_action = QAction("Stop Server")
        stop_action.triggered.connect(self.stop_server)
        menu.addAction(stop_action)
        
        menu.addSeparator()
        
        quit_action = QAction("Quit")
        quit_action.triggered.connect(self.quit)
        menu.addAction(quit_action)
        
        self.tray.setContextMenu(menu)
        self.tray.show()
    
    def start_server(self):
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.daemon = True
        self.server_thread.start()
        self.status_action.setText("Status: Running")
    
    def stop_server(self):
        self.server.stop()
        self.status_action.setText("Status: Stopped")
    
    def quit(self):
        self.stop_server()
        self.app.quit()
    
    def run(self):
        return self.app.exec()


if __name__ == '__main__':
    tray = TrayApp()
    sys.exit(tray.run())