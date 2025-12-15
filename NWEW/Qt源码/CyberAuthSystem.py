import sys
import cv2
import face_recognition
import numpy as np
import os
import mysql.connector
from mysql.connector import Error
from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout,
    QComboBox, QSpacerItem, QGraphicsOpacityEffect
)
from PyQt6.QtGui import QFont, QImage, QPixmap
from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve, pyqtSignal
from PyQt6.QtCore import pyqtSignal

class CyberAuthSystem(QWidget):
    # 定义身份验证成功信号
    authentication_success = pyqtSignal()

    def __init__(self):
        super().__init__()
        # 数据库配置
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '123456',
            'database': 'cyber_auth'
        }
        self.db_connection = None
        self.connect_to_db()

        # 初始化UI组件
        self.animation = None
        self.overlay_effect = None
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.bg_color = "#FAFAFA"
        self.neon_blue = "#00B4FF"
        self.dark_text = "#2D2D2D"
        self.scan_speed = 3
        self.scan_alpha = 0.0
        self.effect_level = 0.1

        # 初始化界面
        self.init_ui()
        self.init_video_capture()

        # 用户数据
        self.user_encodings = {}
        self.user_info = {}
        self.load_database()

        # 视频处理参数
        self.process_frame = True
        self.face_detection_interval = 5
        self.frame_count = 0

        # 连接信号
        self.authentication_success.connect(self.launch_main_interfaces)

    def update_status(self, message, status_type="normal"):
        """更新状态显示"""
        status_colors = {
            "success": "#00FF88",
            "warning": "#FFAA00",
            "error": "#FF0066",
            "normal": self.neon_blue
        }
        self.status_label.setText(f"⏺ {message}")
        self.status_label.setStyleSheet(f"""
            background: rgba(26, 26, 46, 0.9);
            color: {status_colors[status_type]};
            font-size: 16px;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid {status_colors[status_type]};
            font-weight: bold;
        """)

    def connect_to_db(self):
        """建立数据库连接并初始化表结构"""
        try:
            # 先创建数据库（如果不存在）
            connection = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password']
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.db_config['database']}")
            cursor.close()
            connection.close()

            # 连接到目标数据库
            self.db_connection = mysql.connector.connect(
                host=self.db_config['host'],
                user=self.db_config['user'],
                password=self.db_config['password'],
                database=self.db_config['database']
            )
            self.create_tables()
        except Error as e:
            self.update_status(f"数据库连接失败: {str(e)}", "error")

    def create_tables(self):
        """创建用户表"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            job_number VARCHAR(20) PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            phone VARCHAR(20),
            position VARCHAR(50),
            status VARCHAR(20),
            face_encoding BLOB
        )
        """
        try:
            cursor = self.db_connection.cursor()
            cursor.execute(create_table_query)
            self.db_connection.commit()
            cursor.close()
        except Error as e:
            self.update_status(f"创建表失败: {str(e)}", "error")

    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle("NeonVision 光电认证系统")
        self.setMinimumSize(1280, 720)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(30)

        # 控制面板
        control_panel = QGroupBox("用户注册终端")
        control_panel.setMaximumWidth(400)
        control_panel.setStyleSheet(f"""
            QGroupBox {{
                border: 2px solid {self.neon_blue};
                border-radius: 10px;
                margin-top: 20px;
                padding-top: 30px;
                background: white;
            }}
            QGroupBox::title {{
                color: {self.neon_blue};
                font-size: 18px;
                subcontrol-origin: margin;
                left: 15px;
            }}
        """)

        # 表单字段
        self.name_input = QLineEdit()
        self.job_number_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.position_combo = QComboBox()
        self.status_combo = QComboBox()

        # 下拉选项
        self.position_combo.addItems(["员工", "工程师", "项目经理", "部门主管", "其他"])
        self.status_combo.addItems(["在职", "离职", "休假", "实习"])

        # 表单布局
        form = QFormLayout()
        form.setVerticalSpacing(15)
        form.addRow("姓　　名:", self.name_input)
        form.addRow("工　　号:", self.job_number_input)
        form.addRow("联系电话:", self.phone_input)
        form.addRow("职　　务:", self.position_combo)
        form.addRow("状　　态:", self.status_combo)

        # 功能按钮
        self.btn_register = QPushButton("📸 生物特征注册")
        self.btn_login = QPushButton("🔓 实时身份验证")

        # 样式设置
        input_style = f"""
            QLineEdit, QComboBox {{
                border: 2px solid {self.neon_blue};
                border-radius: 6px;
                padding: 12px;
                font-size: 14px;
                min-width: 250px;
            }}
            QComboBox::drop-down {{ border: none; }}
        """
        button_style = f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {self.neon_blue}, stop:1 #0066FF);
                color: white;
                border: none;
                padding: 16px 32px;
                border-radius: 8px;
                font-size: 14px;
                margin-top: 20px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #00C8FF, stop:1 #0055CC);
                border: 1px solid #00FFFF;
            }}
            QPushButton:pressed {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0099FF, stop:1 #003399);
            }}
        """

        # 应用样式
        for widget in [self.name_input, self.job_number_input, self.phone_input,
                       self.position_combo, self.status_combo]:
            widget.setStyleSheet(input_style)
        for btn in [self.btn_register, self.btn_login]:
            btn.setStyleSheet(button_style)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)

        # 布局组合
        panel_layout = QVBoxLayout()
        panel_layout.addLayout(form)
        panel_layout.addSpacerItem(QSpacerItem(20, 30))
        panel_layout.addWidget(self.btn_register)
        panel_layout.addWidget(self.btn_login)
        control_panel.setLayout(panel_layout)

        # 视频面板
        video_panel = QGroupBox()
        video_panel.setStyleSheet(f"""
            border: 3px solid {self.neon_blue};
            border-radius: 15px;
            background: #1A1A2E;
            position: relative;
        """)
        self.video_container = QLabel()
        self.video_container.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_container.setStyleSheet("""
            background: rgba(0,0,0,0.8);
            border-radius: 12px;
            border: 1px solid #00F3FF;
            box-shadow: 0 0 20px rgba(0, 179, 255, 0.5);
        """)
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            background: rgba(26, 26, 46, 0.9);
            color: {self.neon_blue};
            font-size: 16px;
            padding: 15px;
            border-radius: 8px;
            border-left: 5px solid {self.neon_blue};
        """)
        video_layout = QVBoxLayout()
        video_layout.addWidget(self.video_container)
        video_layout.addWidget(self.status_label, alignment=Qt.AlignmentFlag.AlignBottom)
        video_panel.setLayout(video_layout)

        # 主界面布局
        main_layout.addWidget(control_panel)
        main_layout.addWidget(video_panel)
        self.setLayout(main_layout)
        self.setStyleSheet(
            f"background-color: {self.bg_color}; color: {self.dark_text}; font-family: 'Microsoft YaHei';")

        # 绑定事件
        self.btn_register.clicked.connect(self.register_user)
        self.btn_login.clicked.connect(self.authenticate_user)

    def init_video_capture(self):
        """初始化视频采集设备"""
        try:
            self.cap = cv2.VideoCapture(0)
            if not self.cap.isOpened():
                raise Exception("无法打开摄像头")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.update_frame)
            self.timer.start(30)
        except Exception as e:
            self.update_status(f"摄像头初始化错误: {str(e)}", "error")
            sys.exit(1)

    def register_user(self):
        """用户注册逻辑"""
        name = self.name_input.text().strip()
        job_number = self.job_number_input.text().strip()
        phone = self.phone_input.text().strip()
        position = self.position_combo.currentText()
        status = self.status_combo.currentText()

        if not all([name, job_number, phone]):
            self.update_status("⚠ 请填写所有必填信息", "warning")
            return

        def registration_task():
            try:
                # 采集面部特征
                encodings = []
                for _ in range(5):
                    ret, frame = self.cap.read()
                    if ret:
                        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        face_locs = face_recognition.face_locations(rgb_frame)
                        if face_locs:
                            encoding = face_recognition.face_encodings(rgb_frame, face_locs)[0]
                            encodings.append(encoding)

                if encodings:
                    # 序列化面部编码
                    avg_encoding = np.mean(encodings, axis=0)
                    encoding_bytes = avg_encoding.tobytes()

                    # 插入数据库
                    insert_query = """
                    INSERT INTO users 
                    (job_number, name, phone, position, status, face_encoding)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor = self.db_connection.cursor()
                    cursor.execute(insert_query, (
                        job_number,
                        name,
                        phone,
                        position,
                        status,
                        encoding_bytes
                    ))
                    self.db_connection.commit()
                    cursor.close()

                    # 更新内存数据
                    self.user_encodings[job_number] = avg_encoding
                    self.user_info[job_number] = {
                        "name": name,
                        "job_number": job_number,
                        "phone": phone,
                        "position": position,
                        "status": status
                    }

                    self.update_status(f"✅ {name} 注册成功", "success")
            except mysql.connector.IntegrityError:
                self.update_status("⚠ 工号已存在", "error")
            except Error as e:
                self.update_status(f"❌ 数据库错误: {str(e)}", "error")
            except Exception as e:
                self.update_status(f"❌ 注册失败: {str(e)}", "error")

        self.executor.submit(registration_task)

    def authenticate_user(self):
        """用户认证逻辑"""
        def recognition_task():
            try:
                ret, frame = self.cap.read()
                if ret:
                    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    face_locs = face_recognition.face_locations(rgb_frame)

                    if face_locs:
                        encoding = face_recognition.face_encodings(rgb_frame, face_locs)[0]
                        matches = face_recognition.compare_faces(
                            list(self.user_encodings.values()),
                            encoding,
                            tolerance=0.4
                        )

                        if True in matches:
                            job_number = list(self.user_encodings.keys())[matches.index(True)]
                            user_info = self.user_info[job_number]
                            status_msg = (
                                f"👤 欢迎 {user_info['name']}（{user_info['position']}）\n"
                                f"📧 工号: {user_info['job_number']}\n"
                                f"📞 电话: {user_info['phone']}"
                            )
                            self.update_status(status_msg, "success")
                            # 发出身份验证成功信号
                            self.authentication_success.emit()
                        else:
                            self.update_status("❌ 未识别的用户", "error")
                    else:
                        self.update_status("⚠ 未检测到人脸", "warning")
            except Exception as e:
                self.update_status(f"❌ 认证错误: {str(e)}", "error")

        self.executor.submit(recognition_task)

    def load_database(self):
        """从数据库加载用户数据"""
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT job_number, name, phone, position, status, face_encoding FROM users")

            for (job_number, name, phone, position, status, face_encoding) in cursor:
                # 反序列化面部编码
                encoding = np.frombuffer(face_encoding, dtype=np.float64)
                self.user_encodings[job_number] = encoding
                self.user_info[job_number] = {
                    "name": name,
                    "job_number": job_number,
                    "phone": phone,
                    "position": position,
                    "status": status
                }
            cursor.close()
            self.update_status(f"✅ 已加载 {len(self.user_info)} 位用户数据", "success")
        except Error as e:
            self.update_status(f"数据库加载错误: {str(e)}", "error")

    def update_frame(self):
        """更新视频帧"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                try:
                    # 应用特效并显示
                    frame = self.apply_cyber_effects(frame)
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w = frame.shape[:2]
                    q_img = QImage(frame.data, w, h, w * 3, QImage.Format.Format_RGB888)
                    self.video_container.setPixmap(
                        QPixmap.fromImage(q_img).scaled(
                            self.video_container.width(),
                            self.video_container.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                    )
                except Exception as e:
                    self.update_status(f"视频处理错误: {str(e)}", "error")

    def apply_cyber_effects(self, frame):
        """应用赛博朋克风格特效"""
        try:
            # 动态模糊效果
            kernel_size = int(5 * abs(np.sin(np.radians(self.scan_alpha))))
            kernel_size = kernel_size + 1 if kernel_size % 2 == 0 else kernel_size
            blurred = cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
            frame = cv2.addWeighted(frame, 0.7, blurred, 0.3, 0)

            # 网格效果
            h, w = frame.shape[:2]
            grid_color = (0, 255, 255)
            for i in range(1, 3):
                cv2.line(frame, (w // 3 * i, 0), (w // 3 * i, h), grid_color, 1)
                cv2.line(frame, (0, h // 3 * i), (w, h // 3 * i), grid_color, 1)

            # 扫描线动画
            self.scan_alpha = (self.scan_alpha + self.scan_speed) % 360
            scan_pos = int((np.sin(np.radians(self.scan_alpha)) + 1) * h / 2)
            cv2.line(frame, (0, scan_pos), (w, scan_pos), (100, 255, 255), 2)

            # 边缘检测
            edges = cv2.Canny(frame, 100, 200)
            edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            return cv2.addWeighted(frame, 0.9, edges, 0.1, 0)
        except Exception as e:
            return frame

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.cap:
            self.cap.release()
        if self.db_connection and self.db_connection.is_connected():
            self.db_connection.close()
        event.accept()

    def launch_main_interfaces(self):
        # 这里可以添加启动主界面的逻辑
        print("启动主界面")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CyberAuthSystem()
    window.show()
    sys.exit(app.exec())