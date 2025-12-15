import sys
import cv2
import numpy as np
import socket
import threading
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap


class VideoThread(QThread):
    change_pixmap = pyqtSignal(QImage)
    connection_status = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.sock = None
        self.connection = None
        self.running = True

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_address = ('0.0.0.0', 8888)
        self.sock.bind(server_address)
        self.sock.listen(1)
        self.connection_status.emit("等待设备连接...")

        try:
            self.connection, client_address = self.sock.accept()
            self.connection_status.emit(f"已连接: {client_address}")

            expected_size = 640 * 480 * 4

            while self.running:
                try:
                    data_buffer = b""
                    while len(data_buffer) < expected_size:
                        data = self.connection.recv(expected_size - len(data_buffer))
                        if not data:
                            break
                        data_buffer += data

                    if len(data_buffer) != expected_size:
                        break

                    frame = np.frombuffer(data_buffer, dtype=np.uint8).reshape((480, 640, 4))
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                    self._process_frame(frame)

                except Exception as e:
                    print("处理帧时出错:", e)
                    continue

        finally:
            if self.connection:
                self.connection.close()
            self.sock.close()

    def _process_frame(self, frame):
        # 更新PyQt界面
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.change_pixmap.emit(qt_img)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("视频接收窗口")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        main_layout.addWidget(self.video_label)

        self.connection_label = QLabel("视频状态: 未启动")
        main_layout.addWidget(self.connection_label)

        self.video_thread = VideoThread()
        self.video_thread.connection_status.connect(self.update_connection_status)
        self.video_thread.change_pixmap.connect(self.update_image)
        self.video_thread.start()

    def update_image(self, image):
        self.video_label.setPixmap(
            QPixmap.fromImage(image).scaled(
                self.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def update_connection_status(self, status):
        self.connection_label.setText(f"连接状态: {status}")

    def closeEvent(self, event):
        self.video_thread.stop()
        event.accept()


if __name__ == "__main__":
    # 启动PyQt应用
    qt_app = QApplication(sys.argv)
    window = MainWindow()
    window.show()

    sys.exit(qt_app.exec_())