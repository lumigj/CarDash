from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


CAMERA_PREVIEW_SIZE = (1280, 720)


def scaled(value, scale):
    return max(1, round(value * scale))


class MockCameraView(QFrame):
    def __init__(
        self,
        scale,
        title_text="MOCK BACKUP CAMERA",
        subtitle_text="Camera preview is mocked because --mock is active.",
        hint_text="Type R then Enter for reverse, N then Enter for normal.",
    ):
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

        title = QLabel(title_text)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(
            "font-size: %dpx; font-weight: bold;" % scaled(30, scale)
        )
        layout.addWidget(title)

        subtitle = QLabel(subtitle_text)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("font-size: %dpx;" % scaled(18, scale))
        layout.addWidget(subtitle)

        hint = QLabel(hint_text)
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

        try:
            from picamera2 import Picamera2
            from picamera2.previews.qt import QGlPicamera2

            picam2 = Picamera2()
            config = picam2.create_preview_configuration(
                main={"size": CAMERA_PREVIEW_SIZE}
            )
            picam2.configure(config)

            preview_widget = QGlPicamera2(
                picam2,
                width=CAMERA_PREVIEW_SIZE[0],
                height=CAMERA_PREVIEW_SIZE[1],
                keep_ar=False,
            )
            layout.addWidget(preview_widget)
            picam2.start()
            self.picam2 = picam2
            self.preview_widget = preview_widget
        except Exception as error:
            print("Camera unavailable: %s" % error)
            self.mock_view = MockCameraView(
                scale,
                title_text="CAMERA UNAVAILABLE",
                subtitle_text="Dashboard is running without a camera preview.",
                hint_text="Check Raspberry Pi camera connection and libcamera detection.",
            )
            layout.addWidget(self.mock_view)

    def set_reverse_state(self, is_reverse):
        if self.mock_view:
            self.mock_view.set_reverse_state(is_reverse)

    def stop(self):
        if self.picam2:
            self.picam2.stop()
