import sys
import cv2
import numpy as np
import socket
import threading
from PySide6.QtCore import Qt, QThread, Signal, QTimer
from PySide6.QtGui import (QImage, QPixmap, QFont, QColor, QLinearGradient,
                           QPainter, QPalette, QBrush, QKeyEvent)
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget,
                               QVBoxLayout, QHBoxLayout, QGridLayout,
                               QLabel, QFrame, QPushButton,
                               QGraphicsDropShadowEffect)
import paho.mqtt.client as mqtt


class VideoThread(QThread):
    change_pixmap = Signal(QImage)
    connection_status = Signal(str)

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
            expected_size = 640 * 480 * 4  # RGBA格式数据大小

            while self.running:
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
                self.process_frame(frame)

        except Exception as e:
            print("视频接收错误:", e)
        finally:
            if self.connection:
                self.connection.close()
            self.sock.close()

    def process_frame(self, frame):
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        bytes_per_line = ch * w
        qt_img = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format_RGB888)
        self.change_pixmap.emit(qt_img)

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class SensorWidget(QFrame):
    def __init__(self, title, unit, color):
        super().__init__()
        self.setFixedSize(200, 200)
        self.setStyleSheet("background: transparent;")

        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QColor(color))
        self.shadow.setOffset(0, 0)
        self.setGraphicsEffect(self.shadow)

        self.gradient = QLinearGradient(0, 0, 1, 1)
        self.gradient.setColorAt(0, QColor(30, 40, 50))
        self.gradient.setColorAt(1, QColor(50, 60, 70))

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            color: {color};
            font: bold 14px;
            border-bottom: 1px solid {color};
            padding-bottom: 5px;
        """)

        self.value_label = QLabel("--")
        self.value_label.setStyleSheet(f"""
            color: {color};
            font: bold 36px;
            qproperty-alignment: AlignCenter;
        """)

        unit_label = QLabel(unit)
        unit_label.setStyleSheet(f"color: {color}; font: 12px;")

        layout.addWidget(title_label)
        layout.addWidget(self.value_label, 1)
        layout.addWidget(unit_label)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(self.gradient)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 10, 10)

    def update_value(self, value):
        self.value_label.setText(f"{value:.1f}")


class ControlButton(QPushButton):
    def __init__(self, text, color, topic, mqtt_client):
        super().__init__(text)
        self.setFixedSize(120, 120)
        self.setCheckable(True)
        self.color = QColor(color)
        self.topic = topic
        self.mqtt_client = mqtt_client

        self.effect = QGraphicsDropShadowEffect()
        self.effect.setColor(self.color)
        self.effect.setBlurRadius(0)
        self.effect.setOffset(0, 0)
        self.setGraphicsEffect(self.effect)

        self.update_style()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clicked.connect(self.on_click)

    def update_style(self):
        base_style = f"""
            background: rgba(30, 40, 50, 200);
            border: 2px solid {self.color.name()};
            border-radius: 60px;
            color: {self.color.name()};
            font: bold 14px;
            padding: 15px;
        """
        hover_style = f"""
            background: rgba({self.color.red()}, {self.color.green()}, {self.color.blue()}, 30);
            border: 2px solid {self.color.lighter(150).name()};
        """
        pressed_style = """
            background: rgba(255, 255, 255, 50);
            border: 2px solid #FFFFFF;
            color: #FFFFFF;
        """

        self.setStyleSheet(f"""
            QPushButton {{ {base_style} }}
            QPushButton:hover {{ {hover_style} }}
            QPushButton:pressed {{ {pressed_style} }}
            QPushButton:checked {{ {hover_style} }}
        """)

    def on_click(self):
        state = "ON" if self.isChecked() else "OFF"
        if self.topic:
            self.mqtt_client.publish(self.topic, state)
        print(f"{self.text().strip()} 状态: {'激活' if self.isChecked() else '关闭'}")


class VideoMonitor(QFrame):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            background: #1A1A2F;
            border: 2px solid #3498DB;
            border-radius: 10px;
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.video_label = QLabel()
        self.video_label.setStyleSheet("background: black;")
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setMinimumSize(640, 480)  # 设置视频显示区域最小尺寸

        status_bar = QFrame()
        status_bar.setStyleSheet("""
            background: #252540;
            padding: 8px;
            border-top: 1px solid #3498DB;
        """)
        status_layout = QHBoxLayout(status_bar)

        self.status_indicator = QLabel("● 在线")
        self.status_indicator.setStyleSheet("color: #2ECC71; font: bold 12px;")
        self.resolution_label = QLabel("640x480")  # 固定为代码1的分辨率
        self.fps_label = QLabel("30 FPS")

        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        status_layout.addWidget(self.resolution_label)
        status_layout.addWidget(self.fps_label)

        layout.addWidget(self.video_label, 1)
        layout.addWidget(status_bar)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("赛博监控系统 v2.5")
        self.setMinimumSize(1280, 720)

        self.init_mqtt()
        self.init_ui()
        self.init_timers()

        # 初始化视频接收线程
        self.video_thread = VideoThread()
        self.video_thread.change_pixmap.connect(self.display_video_frame)
        self.video_thread.start()

    def init_mqtt(self):
        self.mqtt_client = mqtt.Client(client_id="CyberMonitorClient")
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.user_data_set(self)
        self.mqtt_client.connect("broker.emqx.io", 1883, keepalive=60)
        self.mqtt_client.loop_start()

    def init_ui(self):
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(25, 30, 40))
        self.setPalette(palette)

        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(30, 20, 30, 20)
        main_layout.setSpacing(25)

        top_layout = QHBoxLayout()
        top_layout.setSpacing(30)

        sensor_colors = ["#1ABC9C", "#3498DB", "#F1C40F", "#9B59B6"]
        self.sensors = {
            'temp': SensorWidget("核心温度", "°C", sensor_colors[0]),
            'humi': SensorWidget("环境湿度", "%RH", sensor_colors[1]),
            'lux': SensorWidget("光照强度", "Lux", sensor_colors[2]),
            'co2': SensorWidget("CO₂浓度", "ppm", sensor_colors[3])
        }

        sensor_grid = QGridLayout()
        sensor_grid.setSpacing(20)
        sensor_grid.addWidget(self.sensors['temp'], 0, 0)
        sensor_grid.addWidget(self.sensors['humi'], 0, 1)
        sensor_grid.addWidget(self.sensors['lux'], 1, 0)
        sensor_grid.addWidget(self.sensors['co2'], 1, 1)

        self.video_monitor = VideoMonitor()
        top_layout.addLayout(sensor_grid, stretch=0)
        top_layout.addWidget(self.video_monitor, stretch=1)

        control_layout = QHBoxLayout()
        control_layout.setSpacing(40)
        control_btns = [
            ("蜂鸣器\n开关", "#E74C3C", "control/Buzzer"),
            ("LED灯\n开关", "#2ECC71", "control/LED"),
            ("视觉系统\n开关", "#2980B9", None),
            ("舵机系统\n开关", "#F39C12", None)
        ]

        self.buttons = []
        for text, color, topic in control_btns:
            btn = ControlButton(text, color, topic, self.mqtt_client)
            self.buttons.append(btn)
            control_layout.addWidget(btn)

        main_layout.addLayout(top_layout, stretch=3)
        main_layout.addLayout(control_layout, stretch=1)

        font = QFont("Microsoft YaHei", 10)
        font.setLetterSpacing(QFont.PercentageSpacing, 110)
        self.setFont(font)

    def init_timers(self):
        self.video_timer = QTimer()
        self.video_timer.timeout.connect(self.update_video_status)
        self.video_timer.start(500)

    def update_video_status(self):
        self.video_monitor.fps_label.setText(f"{random.randint(25, 35)} FPS")

    def parse_sensor_data(self, payload):
        temp = None
        humi = None
        lux = None

        temp_match = re.search(r'Temp\s*:\s*(\d+\.?\d*)', payload)
        humi_match = re.search(r'Humi\s*:\s*(\d+\.?\d*)', payload)
        lux_match = re.search(r'BH1750:\s*(\d+\.?\d*)', payload)

        if temp_match:
            temp = float(temp_match.group(1))
        if humi_match:
            humi = float(humi_match.group(1))
        if lux_match:
            lux = float(lux_match.group(1))

        return temp, humi, lux

    def update_sensor_widgets(self, temp=None, humi=None, lux=None):
        if temp is not None:
            self.sensors['temp'].update_value(temp)
        if humi is not None:
            self.sensors['humi'].update_value(humi)
        if lux is not None:
            self.sensors['lux'].update_value(lux)

    def on_mqtt_connect(self, client, userdata, flags, rc):
        if rc == 0:
            client.subscribe("lisitu1", qos=1)
            print("MQTT 连接成功")
        else:
            print(f"MQTT 连接失败: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            print(f"接收消息: {payload}")
            temp, humi, lux = self.parse_sensor_data(payload)
            self.update_sensor_widgets(temp, humi, lux)
        except Exception as e:
            print(f"数据解析错误: {str(e)}")

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def display_video_frame(self, image):
        pixmap = QPixmap.fromImage(image)
        self.video_monitor.video_label.setPixmap(
            pixmap.scaled(
                self.video_monitor.video_label.size(),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        )

    def closeEvent(self, event):
        self.video_thread.stop()
        self.mqtt_client.loop_stop()
        super().closeEvent(event)


if __name__ == "__main__":
    import random
    import re
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())