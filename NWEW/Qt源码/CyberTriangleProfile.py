import sys
import os

os.environ['QT_QPA_PLATFORM'] = 'windows'  # 或者 'direct2d'
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QFrame, QGraphicsDropShadowEffect, QGridLayout,
    QSizePolicy, QProgressBar
)
from PySide6.QtGui import (
    QFont, QPainter, QColor, QLinearGradient,
    QPainterPath, QBrush, QPen, QConicalGradient
)
from PySide6.QtCore import (
    Qt, QPoint, QRectF, QPointF, QPropertyAnimation,
    Property, QTimer, QEasingCurve
)


class TriPanel(QWidget):
    def __init__(self, color):
        super().__init__()
        self._angle = 0.0
        self.color = QColor(color)
        self.line_offset = 0

        self.animation = QPropertyAnimation(self, b"angle")
        self.animation.setDuration(3000)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setLoopCount(-1)
        self.animation.start()

        self.line_timer = QTimer(self)
        self.line_timer.timeout.connect(self.updateLineOffset)
        self.line_timer.start(50)

    def updateLineOffset(self):
        self.line_offset = (self.line_offset + 2) % 32
        self.update()

    def getAngle(self):
        return self._angle

    def setAngle(self, value):
        self._angle = value
        self.update()

    angle = Property(float, getAngle, setAngle)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        grad = QConicalGradient(self.rect().center(), self.angle)
        grad.setColorAt(0, self.color)
        grad.setColorAt(0.5, QColor(self.color.red(), self.color.green(), self.color.blue(), 100))
        grad.setColorAt(1, self.color)

        path = QPainterPath()
        path.addRoundedRect(self.rect(), 15, 15)

        # 注释掉绘制矩形边框的代码
        # line_pen = QPen(QColor(0, 255, 255), 2)
        # line_pen.setDashPattern([8, 4])
        # line_pen.setDashOffset(self.line_offset)
        # painter.setPen(line_pen)
        # painter.drawRect(10, 10, self.width() - 20, self.height() - 20)

        painter.setPen(QPen(QColor(255, 255, 255, 30), 2))
        painter.setBrush(QBrush(grad))
        painter.drawPath(path)


class CyberTriangleProfile(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("赛博代码界面")
        self.resize(1280, 720)
        self.initUI()
        self.setupCyberStyles()
        self.addCyberEffects()

    def initUI(self):
        self.setStyleSheet("background: #000;")

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(50, 40, 50, 40)
        main_layout.setSpacing(30)

        left_panel = self.create_cyber_panel("部门信息", [
            ("所属部门", "技术研发中心"),
            ("直属上级", "方昕（技术总监）"),
            ("入职日期", "2021-08-15"),
            ("员工状态", "在职")
        ], color="#00ffcc")

        center_panel = self.create_cyber_center()

        right_panel = self.create_cyber_panel("技能评估", [
            ("Python", 85),
            ("系统架构", 78),
            ("项目管理", 92),
            ("团队协作", 95)
        ], progress_bars=True, color="#ff00ff")

        main_layout.addWidget(left_panel, stretch=2)
        main_layout.addWidget(center_panel, stretch=5)
        main_layout.addWidget(right_panel, stretch=2)
        self.setLayout(main_layout)

    def create_cyber_center(self):
        panel = TriPanel("#001f3f")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(30, 30, 30, 30)

        header = QWidget()
        header_layout = QVBoxLayout(header)
        header_layout.addWidget(CodeTriangleWidget())

        self.name_label = QLabel("黄 正")
        self.name_label.setFont(QFont("Orbitron", 34, QFont.Bold))
        self.name_label.setStyleSheet("""
            color: #00ffcc;
            text-shadow: 0 0 15px #00ffcc88;
        """)
        header_layout.addWidget(self.name_label, 0, Qt.AlignCenter)

        separator = QFrame()
        separator.setFixedHeight(4)
        separator.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #00ffcc, stop:0.5 #ff00ff, stop:1 #00ffcc);
            margin: 20px 100px;
        """)

        info_frame = self.create_cyber_infobox([
            ("工号：", "202305100108"),
            ("职位：", "技术工程师"),
            ("联系电话：", "17558085667"),
            ("电子邮箱: ", "2049682157@qq.com")
        ])

        layout.addWidget(header)
        layout.addWidget(separator)
        layout.addWidget(info_frame)
        return panel

    def create_cyber_panel(self, title, items, progress_bars=False, color="#00ffcc"):
        panel = TriPanel(color)
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)

        title_label = QLabel(title)
        title_label.setFont(QFont("Orbitron", 18, QFont.Bold))
        title_label.setStyleSheet(f"""
            color: {color};
            text-shadow: 0 0 10px {color}88;
            margin-bottom: 20px;
            border-bottom: 2px solid {color}44;
            padding-bottom: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)

        content_layout = QVBoxLayout()
        for item in items:
            if progress_bars:
                self.add_cyber_progress(content_layout, item[0], item[1], color)
            else:
                self.add_cyber_text(content_layout, item[0], item[1], color)

        layout.addWidget(title_label)
        layout.addLayout(content_layout)
        return panel

    def add_cyber_text(self, layout, key, value, color):
        item = QWidget()
        hbox = QHBoxLayout(item)
        hbox.setContentsMargins(10, 8, 10, 8)

        key_label = QLabel(f"▷ {key}：")
        key_label.setFont(QFont("Orbitron", 12))
        key_label.setStyleSheet(f"color: {color};")

        value_label = QLabel(value)
        value_label.setFont(QFont("Consolas", 13))
        value_label.setStyleSheet(f"""
            color: white;
            background: #00000044;
            padding: 6px 12px;
            border-left: 2px solid {color}88;
        """)

        hbox.addWidget(key_label)
        hbox.addWidget(value_label)
        layout.addWidget(item)
        print(f"Key: {key}, Value: {value}")
        print(f"Key label visible: {key_label.isVisible()}, Value label visible: {value_label.isVisible()}")

    def add_cyber_progress(self, layout, skill, value, color):
        item = QWidget()
        item.setMinimumHeight(80)
        vbox = QVBoxLayout(item)
        vbox.setSpacing(8)

        skill_label = QLabel(f"◼ {skill}")
        skill_label.setFont(QFont("Orbitron", 12, QFont.Bold))
        skill_label.setStyleSheet(f"""
            color: {color};
            margin-left: 5px;
        """)

        # 取消进度条相关代码
        percent = QLabel(f"{value}%")
        percent.setAlignment(Qt.AlignCenter)
        percent.setFont(QFont("Arial", 14, QFont.Bold))
        percent.setStyleSheet(f"""
            color: {color};
            background: #{hex(value * 255 // 100)[2:].zfill(2)}000022;
            border: 1px solid {color}44;
            border-radius: 3px;
            padding: 2px 8px;
        """)

        vbox.addWidget(skill_label)
        vbox.addWidget(percent)
        layout.addWidget(item)

    def create_cyber_infobox(self, items):
        frame = TriPanel("#001f3f")
        grid = QGridLayout(frame)
        grid.setHorizontalSpacing(40)
        grid.setVerticalSpacing(20)

        font_label = QFont("Orbitron", 14, QFont.Bold)
        font_value = QFont("Consolas", 15)

        for row, (label, value) in enumerate(items):
            lbl = QLabel(f"▶ {label}")
            lbl.setFont(font_label)
            lbl.setStyleSheet("color: #00ffcc;")

            val = QLabel(value)
            val.setFont(font_value)
            val.setStyleSheet("""
                color: #ff00ffdd;
                padding: 10px 18px;
                background: #00000044;
                border-left: 2px solid #00ffcc88;
            """)

            grid.addWidget(lbl, row, 0)
            grid.addWidget(val, row, 1)

        return frame

    def setupCyberStyles(self):
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("""
            * { 
                font-smooth: always;
                -webkit-font-smoothing: antialiased;
            }
        """)

    def addCyberEffects(self):
        for panel in self.findChildren(TriPanel):
            effect = QGraphicsDropShadowEffect()
            effect.setColor(QColor(0, 255, 204, 80))
            effect.setBlurRadius(30)
            effect.setOffset(5, 5)
            panel.setGraphicsEffect(effect)

        name_glow = QGraphicsDropShadowEffect()
        name_glow.setColor(QColor(0, 255, 204, 150))
        name_glow.setBlurRadius(30)
        name_glow.setOffset(0, 0)
        self.name_label.setGraphicsEffect(name_glow)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        super().keyPressEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setPen(QPen(QColor(0, 31, 63, 60), 1))

        for y in range(0, self.height(), 20):
            painter.drawLine(0, y, self.width(), y)
        for x in range(0, self.width(), 20):
            painter.drawLine(x, 0, x, self.height())


class CodeTriangleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedSize(220, 220)
        self.pulse_radius = 30
        self.pulse_alpha = 255

        self.anim = QPropertyAnimation(self, b"pulse")
        self.anim.setDuration(2000)
        self.anim.setStartValue(0)
        self.anim.setEndValue(1)
        self.anim.setLoopCount(-1)
        self.anim.start()

    def getPulse(self):
        return self.pulse_radius

    def setPulse(self, value):
        self.pulse_radius = 30 + 20 * value
        self.pulse_alpha = 255 - int(225 * value)
        self.update()

    pulse = Property(float, getPulse, setPulse)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        path = QPainterPath()
        path.moveTo(110, 20)
        path.lineTo(200, 110)
        path.lineTo(110, 200)
        path.lineTo(20, 110)
        path.closeSubpath()

        painter.setPen(QPen(QColor(0, 255, 204), 4))
        painter.drawPath(path)

        painter.setPen(QPen(QColor(0, 255, 204, self.pulse_alpha), 2))
        painter.drawEllipse(QPoint(110, 110), self.pulse_radius, self.pulse_radius)

        line_pen = QPen(QColor(255, 0, 255, 100), 2)
        line_pen.setDashPattern([8, 4])
        painter.setPen(line_pen)
        painter.drawLine(20, 20, 200, 200)
        painter.drawLine(200, 20, 20, 200)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CyberTriangleProfile()
    window.show()
    sys.exit(app.exec())
