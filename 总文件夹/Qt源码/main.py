import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtGui import QFont, QPalette, QColor
from PyQt6.QtCore import (
    Qt, QTimer, QDateTime
)

# 假设这些类在相应文件中定义
from CyberAuthSystem import CyberAuthSystem
from CyberMonitor import CyberMonitor
from DateWindow import MainWindow
from CyberTriangleProfile import CyberTriangleProfile

os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = r'D:\anaconda\envs\M\Library\bin'


class SelectionWindow(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.init_ui()
        self.start_time_updater()

    def init_ui(self):
        # 设置窗口背景
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#050709"))
        self.setPalette(palette)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(25)

        # 标题部分
        self.create_title(main_layout)
        self.create_divider(main_layout)
        self.create_status_bar(main_layout)
        self.create_main_buttons(main_layout)
        self.create_footer(main_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("智井风暴系统")
        self.showFullScreen()

    def create_title(self, layout):
        """创建标题组件"""
        title = QLabel("智 井 风 暴 控 制 中 枢")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #00ffcc;
                font-size: 48px;
                font-weight: bold;
                font-family: 'Orbitron', 'Microsoft YaHei';
                text-shadow: 0 0 15px rgba(0, 255, 204, 0.8);
                padding: 20px;
                border: 3px solid #00ffcc;
                border-radius: 15px;
                background-color: rgba(0, 255, 204, 0.05);
                margin-bottom: 20px;
            }
        """)
        layout.addWidget(title)

    def create_divider(self, layout):
        """创建装饰性分割线"""
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("""
            QFrame {
                border: 2px solid rgba(0, 255, 204, 0.3);
                margin: 20px 50px;
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(0,255,204,0),
                    stop:0.5 rgba(0,255,204,0.6),
                    stop:1 rgba(0,255,204,0)
                );
            }
        """)
        layout.addWidget(divider)

    def create_status_bar(self, layout):
        """创建状态指示栏"""
        status_box = QWidget()
        status_layout = QHBoxLayout()

        # 系统状态
        status_label = QLabel("■ 系统状态：")
        status_label.setStyleSheet("""
            QLabel {
                color: #00ffcc;
                font-size: 20px;
                font-family: 'Microsoft YaHei';
                padding-right: 10px;
            }
        """)

        status_text = QLabel("运 行 中")
        status_text.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 24px;
                font-family: 'Orbitron';
                text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
            }
        """)

        # 网络状态
        network_label = QLabel("▲ 网络连接：")
        network_label.setStyleSheet("""
            QLabel {
                color: #00ffcc;
                font-size: 20px;
                font-family: 'Microsoft YaHei';
                padding-left: 40px;
            }
        """)

        network_status = QLabel("已 连 接")
        network_status.setStyleSheet("""
            QLabel {
                color: #00ff00;
                font-size: 24px;
                font-family: 'Orbitron';
                text-shadow: 0 0 10px rgba(0, 255, 0, 0.5);
            }
        """)

        status_layout.addStretch()
        status_layout.addWidget(status_label)
        status_layout.addWidget(status_text)
        status_layout.addWidget(network_label)
        status_layout.addWidget(network_status)
        status_layout.addStretch()

        status_box.setLayout(status_layout)
        layout.addWidget(status_box)

    def create_main_buttons(self, layout):
        """创建主要功能按钮"""
        button_style = """
        QPushButton {
            background-color: rgba(0, 255, 204, 0.08);
            color: #00ffcc;
            border: 2px solid #00ffcc;
            padding: 30px 60px;
            font-size: 32px;
            font-weight: bold;
            font-family: 'Microsoft YaHei';
            border-radius: 15px;
            margin: 15px;
            text-shadow: 0 0 10px rgba(0, 255, 204, 0.5);
            transition: all 0.3s ease;
        }
        QPushButton:hover {
            background-color: rgba(0, 255, 204, 0.15);
            border-color: #ffffff;
            color: #ffffff;
            box-shadow: 0 0 30px rgba(0, 255, 204, 0.8);
            transform: translateY(-2px);
        }
        QPushButton:pressed {
            background-color: rgba(0, 255, 204, 0.25);
            transform: translateY(0);
        }
        """

        buttons = [
            ("实时数据监控中心", self.open_monitor_window),
            ("智能设备控制中心", self.open_main_window),
            ("用户信息管理中心", self.open_triangle_window)
        ]

        button_layout = QVBoxLayout()
        for text, callback in buttons:
            btn = QPushButton(text)
            btn.setStyleSheet(button_style)
            btn.clicked.connect(callback)
            button_layout.addWidget(btn)

        layout.addLayout(button_layout)

    def create_footer(self, layout):
        """创建底部状态栏"""
        footer = QWidget()
        footer_layout = QHBoxLayout()

        # 时间显示
        self.time_label = QLabel()
        self.time_label.setStyleSheet("""
            QLabel {
                color: #00ffcc;
                font-family: 'Microsoft YaHei';
                font-size: 18px;
                padding: 8px 15px;
                border: 1px solid rgba(0, 255, 204, 0.2);
                border-radius: 5px;
            }
        """)

        # 系统版本
        version = QLabel("智井风暴系统 v2.3.1 | © 2025 西石大")
        version.setStyleSheet("""
            QLabel {
                color: rgba(0, 255, 204, 0.6);
                font-family: 'Microsoft YaHei';
                font-size: 14px;
            }
        """)

        footer_layout.addWidget(self.time_label)
        footer_layout.addStretch()
        footer_layout.addWidget(version)
        footer.setLayout(footer_layout)
        layout.addWidget(footer)

    def start_time_updater(self):
        """启动时间更新定时器"""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        self.update_time()

    def update_time(self):
        """更新时间显示"""
        current_time = QDateTime.currentDateTime().toString("yyyy年MM月dd日 HH:mm:ss")
        self.time_label.setText(f"■ 系统时间：{current_time}")

    def open_monitor_window(self):
        self.controller.monitor_window = CyberMonitor()
        self.controller.monitor_window.showFullScreen()

    def open_main_window(self):
        self.controller.main_window = MainWindow()
        self.controller.main_window.showFullScreen()

    def open_triangle_window(self):
        self.controller.triangle_window = CyberTriangleProfile()
        self.controller.triangle_window.showFullScreen()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Escape:
            self.close()


class SystemController:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.auth_window = CyberAuthSystem()
        self.monitor_window = None
        self.main_window = None
        self.triangle_window = None
        self.selection_window = None

    def show_auth_window(self):
        self.auth_window.show()
        self.auth_window.authentication_success.connect(self.launch_selection_window)

    def launch_selection_window(self):
        self.selection_window = SelectionWindow(self)
        self.selection_window.showFullScreen()
        self.auth_window.hide()

    def run(self):
        self.show_auth_window()
        sys.exit(self.app.exec())


if __name__ == "__main__":
    controller = SystemController()
    controller.run()
