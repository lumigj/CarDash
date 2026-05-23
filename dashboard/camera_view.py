from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


CAMERA_PREVIEW_SIZE = (1280, 720)


def scaled(value, scale):
    return max(1, round(value * scale))


class MockCameraView(QFrame):
    def __init__(self, scale):
        super().__init__()
        self.scale = scale
        self.setStyleSheet(
            "QFrame { background-color: #ffffff; border: 0; }"
            "QLabel { color: #111111; border: 0; }"
        )

        layout = QVBoxLayout()
        layout.setContentsMargins(
            scaled(24, scale),
            scaled(24, scale),
            scaled(24, scale),
            scaled(24, scale),
        )
        layout.setSpacing(scaled(12, scale))
        layout.addStretch(1)

        title = QLabel("MOCK BACKUP CAMERA")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: %dpx; font-weight: bold;" % scaled(30, scale)
        )
        layout.addWidget(title)

        subtitle = QLabel("Camera preview is mocked because --mock is active.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: %dpx;" % scaled(18, scale))
        layout.addWidget(subtitle)

        hint = QLabel("Type R then Enter for reverse, N then Enter for normal.")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("font-size: %dpx;" % scaled(16, scale))
        layout.addWidget(hint)

        self.state_label = QLabel()
        self.state_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.state_label.setStyleSheet(
            "font-size: %dpx; font-weight: bold;" % scaled(20, scale)
        )
        layout.addWidget(self.state_label)

        layout.addStretch(1)
        self.setLayout(layout)
        self.set_reverse_state(False)

    def set_reverse_state(self, is_reverse):
        if is_reverse:
            self.state_label.setText("Reverse signal: ACTIVE")
        else:
            self.state_label.setText("Reverse signal: INACTIVE")


class CameraView(QWidget):
    def __init__(self, scale, mock=False):
        super().__init__()
        self.mock = mock
        self.picam2 = None
        self.mock_view = None
        self.setStyleSheet("background-color: #000000; border: 0;")

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        if self.mock:
            self.mock_view = MockCameraView(scale)
            layout.addWidget(self.mock_view)
            return

        from picamera2 import Picamera2
        from picamera2.previews.qt import QGlPicamera2

        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": CAMERA_PREVIEW_SIZE}
        )
        self.picam2.configure(config)

        self.preview_widget = QGlPicamera2(
            self.picam2,
            width=CAMERA_PREVIEW_SIZE[0],
            height=CAMERA_PREVIEW_SIZE[1],
            keep_ar=False,
        )
        layout.addWidget(self.preview_widget)
        self.picam2.start()

    def set_reverse_state(self, is_reverse):
        if self.mock_view:
            self.mock_view.set_reverse_state(is_reverse)

    def stop(self):
        if self.picam2:
            self.picam2.stop()
