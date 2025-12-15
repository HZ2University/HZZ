import paho.mqtt.client as mqtt
import random
import re
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QGroupBox, QPushButton
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QFont, QPainter, QColor, QLinearGradient, QBrush, QPen
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QValueAxis
import sys
from PySide6.QtWidgets import QApplication


class CyberMonitor(QWidget):
    def __init__(self):
        super().__init__()
        self.data_count = 0
        self.temp_data = []
        self.humi_data = []
        self.lux_data = []
        self.x_values = []
        self.last_temp = 25.0  # 初始默认值
        self.last_humi = 50.0

        # MQTT客户端初始化
        self.mqtt_client = mqtt.Client(client_id="CyberMonitorClient")
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.user_data_set(self)  # 设置自身为用户数据

        self.init_ui()
        self.init_charts()
        self.init_status_msg()
        self.setWindowState(Qt.WindowMaximized)
        self.setStyleSheet("background-color: #000b0f;")

        # 启动MQTT连接
        self.connect_mqtt_broker()

    def connect_mqtt_broker(self):
        """连接MQTT服务器"""
        try:
            self.mqtt_client.connect("broker.emqx.io", 1883, keepalive=60)
            self.mqtt_client.loop_start()  # 启动后台线程处理网络循环
        except Exception as e:
            self.show_message(f"MQTT连接失败: {str(e)}")

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 左侧控制面板
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(25)

        # 传感器状态组
        sensor_group = QGroupBox("传感器状态")
        sensor_group.setStyleSheet("""
            QGroupBox {
                border: 2px solid #00f9ff;
                border-radius: 12px;
                margin-top: 15px;
                background: #00161f;
            }
            QGroupBox::title {
                color: #00f9ff;
                subcontrol-position: top center;
                padding: 5px 20px;
                font: bold 18px 'Microsoft YaHei';
            }
        """)
        grid = QGridLayout(sensor_group)
        grid.setContentsMargins(15, 25, 15, 25)

        self.temp_label = self.create_cyber_label("温度: -- ℃")
        self.humi_label = self.create_cyber_label("湿度: -- %RH")
        self.lux_label = self.create_cyber_label("光照: -- lx")

        grid.addWidget(self.temp_label, 0, 0)
        grid.addWidget(self.humi_label, 1, 0)
        grid.addWidget(self.lux_label, 2, 0)

        left_layout.addWidget(sensor_group)
        main_layout.addWidget(left_panel, stretch=2)

        # 右侧图表区
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(15)

        self.temp_graph = self.create_cyber_chart("温度曲线", "#ff0055")
        self.humi_graph = self.create_cyber_chart("湿度曲线", "#00ff88")
        self.lux_graph = self.create_cyber_chart("光照曲线", "#aa00ff")

        chart_layout = QHBoxLayout()
        chart_layout.addWidget(self.humi_graph)
        chart_layout.addWidget(self.lux_graph)

        right_layout.addWidget(self.temp_graph)
        right_layout.addLayout(chart_layout)
        main_layout.addWidget(right_panel, stretch=5)

        # 返回按钮
        btn_back = QPushButton("返回主菜单")
        btn_back.clicked.connect(self.close)
        main_layout.addWidget(btn_back)

    def create_cyber_label(self, text):
        label = QLabel(text)
        label.setFont(QFont('Microsoft YaHei', 16))
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            background: #00222f;
            border: 2px solid #0077ff;
            border-radius: 8px;
            padding: 12px;
            color: #00ff9f;
            qproperty-alignment: AlignCenter;
        """)
        return label

    def create_cyber_chart(self, title, line_color):
        chart = QChart()
        chart.setTitle(title)
        chart.setTitleFont(QFont('Microsoft YaHei', 14, QFont.Bold))
        chart.setTitleBrush(QBrush(QColor(line_color)))

        grad = QLinearGradient(0, 0, 1, 1)
        grad.setColorAt(0, QColor(0, 15, 31))
        grad.setColorAt(1, QColor(0, 31, 15))
        chart.setBackgroundBrush(QBrush(grad))

        axis_x = QValueAxis()
        axis_x.setRange(0, 15)
        axis_x.setTitleText("数据序列")
        axis_x.setTitleBrush(QColor("#00ffdd"))
        axis_x.setLabelsColor(QColor("#00ffdd"))
        axis_x.setGridLineColor(QColor(0, 255, 221, 50))

        axis_y = QValueAxis()
        axis_y.setTitleText("测量值")
        axis_y.setTitleBrush(QColor(line_color))
        axis_y.setLabelsColor(QColor(line_color))
        axis_y.setGridLineColor(QColor(f"{line_color}40"))

        series = QLineSeries()
        pen = QPen(QColor(line_color))
        pen.setWidth(2)
        series.setPen(pen)

        chart.addSeries(series)
        chart.addAxis(axis_x, Qt.AlignBottom)
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)

        chart_view = QChartView(chart)
        chart_view.setRenderHint(QPainter.Antialiasing)
        chart_view.setStyleSheet("""
            border: 2px solid #005577;
            border-radius: 12px;
            background: transparent;
        """)
        return chart_view

    def init_charts(self):
        self.temp_series = self.temp_graph.chart().series()[0]
        self.humi_series = self.humi_graph.chart().series()[0]
        self.lux_series = self.lux_graph.chart().series()[0]

    def update_sensor_data(self, temp, humi, lux):
        self.data_count += 1
        self.x_values.append(self.data_count)

        # 应用随机波动（实际使用时可移除）
        temp = float(temp) + random.uniform(-1.5, 1.5)
        humi = float(humi) + random.uniform(-2, 2)
        lux = float(lux) + random.randint(-50, 50)

        self.temp_data.append(max(0, temp))
        self.humi_data.append(max(0, min(humi, 100)))  # 湿度不超过100%
        self.lux_data.append(max(0, lux))  # 光照不低于0

        # 更新标签显示
        self.temp_label.setText(f"温度: {temp:.1f} ℃")
        self.humi_label.setText(f"湿度: {humi:.1f} %RH")
        self.lux_label.setText(f"光照: {lux:.0f} lx")

        # 维护最近15个数据点
        if len(self.x_values) > 15:
            self.x_values.pop(0)
            self.temp_data.pop(0)
            self.humi_data.pop(0)
            self.lux_data.pop(0)

        # 更新图表数据
        self.update_chart(self.temp_series, self.temp_data)
        self.update_chart(self.humi_series, self.humi_data)
        self.update_chart(self.lux_series, self.lux_data)

        # 动态调整Y轴范围
        for chart, data in zip(
                [self.temp_graph, self.humi_graph, self.lux_graph],
                [self.temp_data, self.humi_data, self.lux_data]
        ):
            y_axis = chart.chart().axes(Qt.Vertical)[0]
            if data:
                min_val = max(0, min(data) - 5)
                max_val = max(data) + 5
                y_axis.setRange(min_val, max_val)

        # 调整X轴范围
        x_axis = self.temp_graph.chart().axes(Qt.Horizontal)[0]
        x_axis.setRange(max(0, self.data_count - 15), self.data_count)

    def update_chart(self, series, data):
        series.clear()
        for x, y in zip(self.x_values, data):
            series.append(x, y)

    def init_status_msg(self):
        self.status_msg = QLabel(self)
        self.status_msg.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.status_msg.setStyleSheet("""
            background: rgba(0, 50, 50, 200);
            color: #00ff9f;
            border: 1px solid #00ff9f;
            border-radius: 6px;
            padding: 8px 16px;
            font: bold 14px 'Microsoft YaHei';
        """)
        self.status_msg.hide()
        self.msg_timer = QTimer()
        self.msg_timer.timeout.connect(self.status_msg.hide)

    def show_message(self, text):
        self.status_msg.setText(text)
        self.status_msg.adjustSize()
        self.status_msg.move(self.width() - self.status_msg.width() - 30, 30)
        self.status_msg.show()
        self.msg_timer.start(2000)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def send_control(self, device, command):
        """发送控制命令"""
        topic = f"cyber/control/{device}"
        self.mqtt_client.publish(topic, command)
        self.show_message(f"[系统] {device} {command} 已发送")

    # MQTT回调函数
    def on_mqtt_connect(self, client, userdata, flags, rc):
        print(f"MQTT 连接状态: {rc}")
        if rc == 0:
            client.subscribe("lisitu1", qos=1)  # 订阅目标主题
            self.show_message("MQTT 连接成功")
        else:
            self.show_message(f"MQTT 连接失败: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode()
            print(f"接收消息: {payload}")

            # 解析温度和湿度
            temp_match = re.search(r'Temp\s*:\s*(\d+\.?\d*)', payload)
            humi_match = re.search(r'Humi\s*:\s*(\d+\.?\d*)', payload)
            lux_match = re.search(r'BH1750:\s*(\d+\.?\d*)', payload)

            # 处理缺失数据
            temp = temp_match.group(1) if temp_match else self.last_temp
            humi = humi_match.group(1) if humi_match else self.last_humi
            lux = lux_match.group(1) if lux_match else 0.0

            # 保存最新有效值
            if temp_match:
                self.last_temp = float(temp)
            if humi_match:
                self.last_humi = float(humi)

            self.update_sensor_data(temp, humi, lux)

        except Exception as e:
            print(f"数据解析错误: {str(e)}")
            self.show_message(f"数据解析错误: {str(e)}")

    def closeEvent(self, event: QEvent):
        """窗口关闭时清理MQTT资源"""
        self.mqtt_client.loop_stop()  # 停止MQTT网络循环
        self.mqtt_client.disconnect()  # 断开服务器连接
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    window = CyberMonitor()
    window.show()
    sys.exit(app.exec())