import sys
import random
from PyQt5.Qt import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CatSpeed 仪表盘喵~")
        self.setGeometry(300, 300, 480, 320)  # 可以 later 调整为树莓派屏幕分辨率

        # 字体统一风格
        font = QFont("Arial", 40, QFont.Bold)

        # 标签 UI
        self.speed_label = QLabel("Speed: -- km/h")
        self.speed_label.setFont(font)
        self.speed_label.setAlignment(Qt.AlignCenter)

        self.rpm_label = QLabel("RPM: ----")
        self.rpm_label.setFont(font)
        self.rpm_label.setAlignment(Qt.AlignCenter)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.speed_label)
        layout.addWidget(self.rpm_label)
        self.setLayout(layout)

        # 定时器生成 mock 数据
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_data)
        self.timer.start(1000)  # 每 1 秒更新一次

    def update_data(self):
        # 模拟速度和转速
        speed = random.randint(0, 180)  # 速度 0~180 km/h
        rpm = random.randint(800, 7500)  # 转速 800~7500 rpm

        # 更新 UI
        self.speed_label.setText(f"Speed: {speed} km/h")
        self.rpm_label.setText(f"RPM: {rpm}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Dashboard()
    window.show()
    sys.exit(app.exec_())