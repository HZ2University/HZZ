import paho.mqtt.client as mqtt
import random
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QPainter, QColor
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import sys
from PySide6.QtWidgets import QApplication

TOPIC_LED = "led_control"
TOPIC_BUZZER = "buzzer_control"
import os
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'd:\anaconda\envs\lihaoze\lib\site-packages'

# 将上述路径替换为你实际的Qt插件文件夹路径

class MonitoringWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.data_count = 0
        self.setup_ui()
        self.setup_charts()
        self.setup_status_message()
        self.setWindowState(Qt.WindowMaximized)  # 设置窗口为最大化（全屏）显示

    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)

        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        left_layout.setSpacing(20)

        status_group = QGroupBox("传感器状态")
        status_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d1d9e6;
                border-radius: 6px;
                margin-top: 10px;
                color: #4a4a4a;
            }
            QGroupBox::title {
                subcontrol-position: top center;
                padding: 0 10px;
                color: #666666;
            }
        """)
        status_layout = QGridLayout(status_group)
        status_layout.setContentsMargins(20, 15, 20, 20)
        status_layout.setVerticalSpacing(15)

        self.temp_label = self.create_status_label("温度: -- °C")
        self.humi_label = self.create_status_label("湿度: -- %RH")
        self.light_label = self.create_status_label("光照: -- Lux")

        status_layout.addWidget(self.temp_label, 0, 0)
        status_layout.addWidget(self.humi_label, 1, 0)
        status_layout.addWidget(self.light_label, 2, 0)

        button_container = QWidget()
        button_layout = QGridLayout(button_container)
        button_layout.setSpacing(10)

        btn1 = QPushButton("打开 LED 灯")
        btn1.setFont(QFont("Microsoft YaHei", 10))
        btn1.setStyleSheet(self.get_button_style())
        btn1.clicked.connect(lambda: self.publish_mqtt_message("LED", "ON"))
        button_layout.addWidget(btn1, 0, 0)

        btn2 = QPushButton("关闭 LED 灯")
        btn2.setFont(QFont("Microsoft YaHei", 10))
        btn2.setStyleSheet(self.get_button_style())
        btn2.clicked.connect(lambda: self.publish_mqtt_message("LED", "OFF"))
        button_layout.addWidget(btn2, 0, 1)

        btn3 = QPushButton("打开蜂鸣器")
        btn3.setFont(QFont("Microsoft YaHei", 10))
        btn3.setStyleSheet(self.get_button_style())
        btn3.clicked.connect(lambda: self.publish_mqtt_message("Buzzer", "ON"))
        button_layout.addWidget(btn3, 1, 0)

        btn4 = QPushButton("关闭蜂鸣器")
        btn4.setFont(QFont("Microsoft YaHei", 10))
        btn4.setStyleSheet(self.get_button_style())
        btn4.clicked.connect(lambda: self.publish_mqtt_message("Buzzer", "OFF"))
        button_layout.addWidget(btn4, 1, 1)

        left_layout.addWidget(status_group)
        left_layout.addWidget(button_container)
        main_layout.addWidget(left_container, stretch=3)

        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setSpacing(20)

        self.temp_chart_view = self.create_chart_view("温度变化 (°C)", 0, 50)
        self.humi_chart_view = self.create_chart_view("湿度变化 (%RH)", 0, 100)
        self.light_chart_view = self.create_chart_view("光照变化 (Lux)", 0, 2000)

        right_layout.addWidget(self.temp_chart_view)
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.humi_chart_view)
        bottom_layout.addWidget(self.light_chart_view)
        right_layout.addLayout(bottom_layout)

        main_layout.addWidget(right_container, stretch=7)

    def setup_status_message(self):
        self.status_message = QLabel(self)
        self.status_message.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.status_message.setStyleSheet("""
            background: rgba(64, 64, 64, 220);
            color: white;
            border-radius: 4px;
            padding: 6px 12px;
            font-size: 12px;
        """)
        self.status_message.hide()
        self.timer = QTimer()
        self.timer.timeout.connect(self.hide_status_message)

    def create_status_label(self, text):
        label = QLabel(text)
        label.setFont(QFont("Microsoft YaHei", 10))
        label.setStyleSheet("""
            background: #f8f9fa;
            border: 1px solid #e0e1e2;
            border-radius: 5px;
            padding: 8px 12px;
            color: #4a4a4a;
        """)
        return label

    def create_chart_view(self, title, y_min, y_max):
        chart = QChart()
        chart.setTitle(title)
        chart.setTitleFont(QFont("Microsoft YaHei", 11, QFont.Bold))
        chart.setBackgroundBrush(QColor("#ffffff"))
        chart.setTitleBrush(QColor("#4a4a4a"))
        chart.legend().hide()

        axis_x = QValueAxis()
        axis_x.setRange(0, 15)
        axis_x.setLabelFormat("%d")
        axis_x.setTitleText("数据传输次数")
        axis_x.setLabelsColor(QColor("#666666"))
        axis_x.setGridLineColor(QColor("#e0e0e0"))
        axis_x.setLabelsFont(QFont("Microsoft YaHei", 10))

        axis_y = QValueAxis()
        axis_y.setRange(y_min, y_max)
        axis_y.setTitleText(title.split()[0])
        axis_y.setLabelsColor(QColor("#666666"))
        axis_y.setGridLineColor(QColor("#e0e0e0"))
        axis_y.setLabelsFont(QFont("Microsoft YaHei", 10))

        series = QLineSeries()
        series.setColor(QColor("#808080"))
        chart.addSeries(series)

        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setMinimumHeight(200)
        return chart_view

    def setup_charts(self):
        self.temp_series = self.temp_chart_view.chart().series()[0]
        self.humi_series = self.humi_chart_view.chart().series()[0]
        self.light_series = self.light_chart_view.chart().series()[0]
        self.temp_data = []
        self.humi_data = []
        self.light_data = []
        self.data_count_list = []

    def update_mqtt_data(self, temp, humi, light):
        self.data_count += 1
        self.data_count_list.append(self.data_count)

        temp = self.apply_random_offset(temp, 0, 50, is_temp_or_humi=True)
        humi = self.apply_random_offset(humi, 0, 100, is_temp_or_humi=True)
        light = self.apply_random_offset(light, 0, 2000)

        self.update_label(self.temp_label, f"温度: {temp:.2f} °C")
        self.update_label(self.humi_label, f"湿度: {humi:.2f} %RH")
        self.update_label(self.light_label, f"光照: {light:.2f} Lux")

        self.temp_data.append(temp)
        self.humi_data.append(humi)
        self.light_data.append(light)

        if len(self.data_count_list) > 15:
            self.data_count_list.pop(0)
            self.temp_data.pop(0)
            self.humi_data.pop(0)
            self.light_data.pop(0)

        min_x = max(0, self.data_count - 15)
        max_x = self.data_count
        self.temp_chart_view.chart().axisX().setRange(min_x, max_x)
        self.humi_chart_view.chart().axisX().setRange(min_x, max_x)
        self.light_chart_view.chart().axisX().setRange(min_x, max_x)

        # 动态调整纵坐标范围
        if self.temp_data:
            temp_min = min(self.temp_data)
            temp_max = max(self.temp_data)
            temp_range = temp_max - temp_min
            if temp_range < 1:
                temp_range = 1
            self.temp_chart_view.chart().axisY().setRange(temp_min - 0.1 * temp_range, temp_max + 0.1 * temp_range)

        if self.humi_data:
            humi_min = min(self.humi_data)
            humi_max = max(self.humi_data)
            humi_range = humi_max - humi_min
            if humi_range < 1:
                humi_range = 1
            self.humi_chart_view.chart().axisY().setRange(humi_min - 0.1 * humi_range, humi_max + 0.1 * humi_range)

        if self.light_data:
            light_min = min(self.light_data)
            light_max = max(self.light_data)
            light_range = light_max - light_min
            if light_range < 1:
                light_range = 1
            self.light_chart_view.chart().axisY().setRange(light_min - 0.1 * light_range, light_max + 0.1 * light_range)

        self.update_series(self.temp_series, self.data_count_list, self.temp_data)
        self.update_series(self.humi_series, self.data_count_list, self.humi_data)
        self.update_series(self.light_series, self.data_count_list, self.light_data)

    def apply_random_offset(self, value, min_val, max_val, is_temp_or_humi=False):
        if is_temp_or_humi:
            offset = random.uniform(-2, 2)
        else:
            offset = random.randint(-10, 10)
        new_value = float(value) + offset
        new_value = max(min_val, min(new_value, max_val))
        return new_value

    def update_label(self, label, text):
        label.setText(text)

    def update_series(self, series, x_data, y_data):
        series.clear()
        for x, y in zip(x_data, y_data):
            series.append(x, y)

    def get_button_style(self):
        return """
            QPushButton {
                background: #808080;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px 18px;
                font-weight: 500;
            }
            QPushButton:hover { 
                background: #707070; 
            }
            QPushButton:pressed { 
                background: #606060; 
            }
        """

    def publish_mqtt_message(self, device, state):
        global client
        topic = f"control/{device}"
        print(f"Publishing to topic: {topic}, message: {state}")
        client.publish(topic, state)
        action = "打开" if state == "ON" else "关闭"
        self.show_status_message(f"{device}已{action}")

    def show_status_message(self, text):
        self.status_message.setText(text)
        self.status_message.adjustSize()
        self.status_message.move(self.width() - self.status_message.width() - 20, 20)
        self.status_message.show()
        self.timer.start(2000)

    def hide_status_message(self):
        self.status_message.hide()
        self.timer.stop()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.setWindowState(Qt.WindowNoState)  # 退出全屏
            event.accept()
        else:
            event.ignore()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code " + str(rc))
    if rc == 0:
        print("Successfully connected to MQTT broker")
    else:
        print(f"Failed to connect, return code {rc}")
    client.subscribe("lisitu1")
    client.subscribe(TOPIC_LED)
    client.subscribe(TOPIC_BUZZER)


def on_message(client, userdata, msg):
    print("Message received on topic: " + msg.topic)
    payload = msg.payload.decode('utf-8')
    try:
        if "Temp" in payload and "Humi" in payload:
            temp = payload.split("Temp : ")[1].split("℃")[0]
            humi = payload.split("Humi : ")[1].split("%RH")[0]
            light = 0
        elif "BH1750" in payload:
            light = payload.split("BH1750:   ")[1].split(" lux")[0]
            temp = None
            humi = None
        if temp and humi:
            userdata.update_mqtt_data(temp, humi, light)
    except Exception as e:
        print(f"数据解析出错: {str(e)}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

broker_address = "broker.emqx.io"
port = 1883

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MonitoringWindow()
    client.user_data_set(window)
    client.connect(broker_address, port, 60)
    client.loop_start()
    window.showFullScreen()
    sys.exit(app.exec())
