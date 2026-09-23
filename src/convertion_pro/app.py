import sys
import json
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QStackedWidget,
    QFrame,
    QProgressBar,
    QMessageBox,
)

from convertion_pro.hardware.simulator import SimulatedProgrammer
from convertion_pro.core.workflow import ConversionWorkflow


PROFILE_PATH = Path(
    "vehicles/jeep/wrangler_2012_2018/profile.json"
)


def load_profile():
    with PROFILE_PATH.open(encoding="utf-8") as file:
        return json.load(file)


STYLESHEET = """
QWidget {
    background-color: #080D14;
    color: #F3F7FC;
    font-family: Arial;
    font-size: 15px;
}

QMainWindow {
    background-color: #080D14;
}

QLabel#brand {
    font-size: 25px;
    font-weight: 800;
    color: #FFFFFF;
}

QLabel#eyebrow {
    color: #4D9FFF;
    font-size: 12px;
    font-weight: 700;
}

QLabel#title {
    font-size: 32px;
    font-weight: 800;
    color: #FFFFFF;
}

QLabel#subtitle {
    color: #8C9BAD;
    font-size: 15px;
}

QLabel#success {
    color: #36D98B;
    font-size: 18px;
    font-weight: 700;
}

QLabel#warning {
    color: #FFBE55;
    font-weight: 700;
}

QFrame#card {
    background-color: #101823;
    border: 1px solid #1E2B3B;
    border-radius: 14px;
}

QFrame#successCard {
    background-color: #0C1D19;
    border: 1px solid #1C684B;
    border-radius: 14px;
}

QComboBox {
    background-color: #101823;
    border: 1px solid #28384A;
    border-radius: 8px;
    padding: 12px;
    min-height: 24px;
}

QComboBox:hover {
    border: 1px solid #398DFF;
}

QPushButton {
    background-color: #151F2B;
    border: 1px solid #2A3A4D;
    border-radius: 8px;
    padding: 12px 22px;
    font-weight: 700;
}

QPushButton:hover {
    border: 1px solid #398DFF;
}

QPushButton#primary {
    background-color: #1677FF;
    border: 1px solid #3990FF;
    color: white;
}

QPushButton#primary:hover {
    background-color: #2585FF;
}

QPushButton#convert {
    background-color: #1677FF;
    border: 1px solid #3990FF;
    color: white;
    font-size: 25px;
    font-weight: 900;
    padding: 22px;
    border-radius: 12px;
}

QPushButton#advanced {
    background-color: transparent;
    border: none;
    color: #738399;
}

QProgressBar {
    background-color: #111A25;
    border: 1px solid #263648;
    border-radius: 7px;
    text-align: center;
    min-height: 18px;
}

QProgressBar::chunk {
    background-color: #1677FF;
    border-radius: 6px;
}
"""


class Page(QWidget):
    def __init__(self, app, eyebrow, title, subtitle=""):
        super().__init__()
        self.app = app

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(70, 55, 70, 55)
        self.layout.setSpacing(18)

        brand = QLabel("CONVERTION-PRO")
        brand.setObjectName("brand")

        eyebrow_label = QLabel(eyebrow.upper())
        eyebrow_label.setObjectName("eyebrow")

        title_label = QLabel(title)
        title_label.setObjectName("title")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setObjectName("subtitle")
        subtitle_label.setWordWrap(True)

        self.layout.addWidget(brand)
        self.layout.addSpacing(30)
        self.layout.addWidget(eyebrow_label)
        self.layout.addWidget(title_label)
        self.layout.addWidget(subtitle_label)


class VehicleSelectionPage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Step 01",
            "Select Vehicle",
            "Choose the vehicle and cluster generation."
        )

        card = QFrame()
        card.setObjectName("card")
        form = QVBoxLayout(card)
        form.setContentsMargins(28, 28, 28, 28)
        form.setSpacing(14)

        form.addWidget(QLabel("MAKE"))
        self.make = QComboBox()
        self.make.addItems(["Jeep"])
        form.addWidget(self.make)

        form.addWidget(QLabel("MODEL / GENERATION"))
        self.model = QComboBox()
        self.model.addItems(["Wrangler 2012–2018"])
        form.addWidget(self.model)

        proceed = QPushButton("CONTINUE")
        proceed.setObjectName("primary")
        proceed.clicked.connect(lambda: app.go(1))
        form.addSpacing(10)
        form.addWidget(proceed)

        self.layout.addSpacing(15)
        self.layout.addWidget(card)
        self.layout.addStretch()


class ConnectionGuidePage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Step 02",
            "Connection Guide",
            "Jeep Wrangler 2012–2018"
        )

        card = QFrame()
        card.setObjectName("card")
        box = QVBoxLayout(card)
        box.setContentsMargins(28, 28, 28, 28)
        box.setSpacing(15)

        box.addWidget(QLabel("CONNECTION METHOD"))
        method = QLabel("BENCH")
        method.setObjectName("success")
        box.addWidget(method)

        box.addWidget(QLabel("REQUIRED CABLE"))
        cable = QLabel("CP-JEEP-004")
        cable.setObjectName("success")
        box.addWidget(cable)

        box.addSpacing(8)
        box.addWidget(QLabel(
            "1. Connect the required cable to the programmer.\n"
            "2. Connect the cable to the cluster.\n"
            "3. Confirm that all connections are secure.\n"
            "4. Press PROCEED to run the automatic safety check."
        ))

        proceed = QPushButton("PROCEED")
        proceed.setObjectName("primary")
        proceed.clicked.connect(app.perform_safety_check)

        back = QPushButton("BACK")
        back.clicked.connect(lambda: app.go(0))

        row = QHBoxLayout()
        row.addWidget(back)
        row.addStretch()
        row.addWidget(proceed)

        self.layout.addWidget(card)
        self.layout.addLayout(row)
        self.layout.addStretch()


class SafetyPage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Safety Gate",
            "Checking Connection",
            "Programming remains locked until every safety condition passes."
        )

        self.card = QFrame()
        self.card.setObjectName("card")
        self.box = QVBoxLayout(self.card)
        self.box.setContentsMargins(28, 28, 28, 28)
        self.box.setSpacing(14)

        self.status = QLabel("Running safety checks...")
        self.status.setObjectName("warning")
        self.box.addWidget(self.status)

        self.details = QLabel("")
        self.details.setWordWrap(True)
        self.box.addWidget(self.details)

        self.continue_button = QPushButton("CONTINUE")
        self.continue_button.setObjectName("primary")
        self.continue_button.hide()
        self.continue_button.clicked.connect(lambda: app.go(3))
        self.box.addWidget(self.continue_button)

        self.layout.addWidget(self.card)
        self.layout.addStretch()

    def show_report(self, report):
        checks = [
            ("Programmer detected", report.programmer),
            ("Correct cable", report.cable),
            ("Supply voltage", report.voltage),
            ("Cluster communication", report.communication),
            ("Profile match", report.profile),
        ]

        self.details.setText(
            "\n".join(
                f"{'✓' if passed else '✕'}  {name}"
                for name, passed in checks
            )
        )

        if report.passed:
            self.card.setObjectName("successCard")
            self.card.style().unpolish(self.card)
            self.card.style().polish(self.card)

            self.status.setText("CONNECTION VERIFIED")
            self.status.setObjectName("success")
            self.status.style().unpolish(self.status)
            self.status.style().polish(self.status)

            self.continue_button.show()
        else:
            self.status.setText("PROGRAMMING BLOCKED")


class ReadyPage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Step 03",
            "Cluster Ready",
            "Connection verified. The cluster is ready for analysis."
        )

        card = QFrame()
        card.setObjectName("successCard")
        box = QVBoxLayout(card)
        box.setContentsMargins(30, 30, 30, 30)

        status = QLabel("✓ PROGRAMMER ONLINE")
        status.setObjectName("success")
        box.addWidget(status)

        box.addWidget(QLabel(
            "Jeep Wrangler 2012–2018\n"
            "Cable: CP-JEEP-004\n"
            "Voltage: 12.4 V\n"
            "Communication: VERIFIED"
        ))

        convert = QPushButton("CONVERT")
        convert.setObjectName("convert")
        convert.clicked.connect(app.analyze_cluster)

        advanced = QPushButton("Advanced Tools")
        advanced.setObjectName("advanced")
        advanced.clicked.connect(
            lambda: QMessageBox.information(
                app,
                "Advanced Tools",
                "Advanced tools will be enabled progressively during development."
            )
        )

        self.layout.addWidget(card)
        self.layout.addSpacing(20)
        self.layout.addWidget(convert)
        self.layout.addWidget(advanced)
        self.layout.addStretch()


class ConfirmationPage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Conversion",
            "Confirm Conversion",
            "The current unit was detected automatically."
        )

        card = QFrame()
        card.setObjectName("card")
        box = QVBoxLayout(card)
        box.setContentsMargins(32, 32, 32, 32)

        self.direction = QLabel("KM / KMH   →   MILES / MPH")
        self.direction.setAlignment(Qt.AlignCenter)
        self.direction.setObjectName("title")
        box.addWidget(self.direction)

        self.info = QLabel("")
        self.info.setAlignment(Qt.AlignCenter)
        self.info.setObjectName("subtitle")
        box.addWidget(self.info)

        confirm = QPushButton("CONFIRM CONVERSION")
        confirm.setObjectName("primary")
        confirm.clicked.connect(app.start_programming)

        cancel = QPushButton("CANCEL")
        cancel.clicked.connect(lambda: app.go(3))

        self.layout.addWidget(card)
        self.layout.addWidget(confirm)
        self.layout.addWidget(cancel)
        self.layout.addStretch()


class ProgrammingPage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Programming",
            "Programming Cluster",
            "DO NOT DISCONNECT • DO NOT TURN POWER OFF"
        )

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)

        self.step = QLabel("Preparing...")
        self.step.setObjectName("success")

        self.details = QLabel(
            "Reading original data\n"
            "Creating backup\n"
            "Preparing conversion\n"
            "Programming cluster\n"
            "Verifying programming"
        )

        self.layout.addWidget(self.progress)
        self.layout.addWidget(self.step)
        self.layout.addWidget(self.details)
        self.layout.addStretch()


class CompletePage(Page):
    def __init__(self, app):
        super().__init__(
            app,
            "Complete",
            "Conversion Complete",
            "Programming and read-back verification completed successfully."
        )

        card = QFrame()
        card.setObjectName("successCard")
        box = QVBoxLayout(card)
        box.setContentsMargins(32, 32, 32, 32)

        success = QLabel("✓ VERIFIED")
        success.setObjectName("success")
        success.setAlignment(Qt.AlignCenter)

        self.direction = QLabel("KM → MILES")
        self.direction.setObjectName("title")
        self.direction.setAlignment(Qt.AlignCenter)

        safe = QLabel(
            "Original backup saved.\n"
            "Programming verified.\n\n"
            "It is now safe to disconnect the cluster."
        )
        safe.setAlignment(Qt.AlignCenter)

        box.addWidget(success)
        box.addWidget(self.direction)
        box.addWidget(safe)

        done = QPushButton("DONE")
        done.setObjectName("primary")
        done.clicked.connect(app.reset_workflow)

        self.layout.addWidget(card)
        self.layout.addWidget(done)
        self.layout.addStretch()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CONVERTION-PRO")
        self.resize(1100, 760)
        self.setMinimumSize(850, 620)

        self.profile = load_profile()
        self.hardware = SimulatedProgrammer()
        self.workflow = ConversionWorkflow(
            self.hardware,
            self.profile
        )

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.vehicle_page = VehicleSelectionPage(self)
        self.connection_page = ConnectionGuidePage(self)
        self.safety_page = SafetyPage(self)
        self.ready_page = ReadyPage(self)
        self.confirm_page = ConfirmationPage(self)
        self.programming_page = ProgrammingPage(self)
        self.complete_page = CompletePage(self)

        for page in [
            self.vehicle_page,
            self.connection_page,
            self.safety_page,
            self.ready_page,
            self.confirm_page,
            self.programming_page,
            self.complete_page,
        ]:
            self.stack.addWidget(page)

        self.current_unit = None
        self.target_unit = None
        self.converted_data = None
        self.program_step = 0

    def go(self, index):
        self.stack.setCurrentIndex(index)

    def perform_safety_check(self):
        self.go(2)

        try:
            report = self.workflow.run_safety_check()
            self.safety_page.show_report(report)
        except Exception as error:
            QMessageBox.critical(
                self,
                "Safety Check Failed",
                str(error)
            )

    def analyze_cluster(self):
        try:
            self.workflow.create_backup()
            self.current_unit = self.workflow.detect_unit()

            if self.current_unit == "KM":
                self.target_unit = "MI"
                direction = "KM / KMH   →   MILES / MPH"
            else:
                self.target_unit = "KM"
                direction = "MILES / MPH   →   KM / KMH"

            self.confirm_page.direction.setText(direction)
            self.confirm_page.info.setText(
                f"Current unit: {self.current_unit}\n"
                f"Target unit: {self.target_unit}\n\n"
                "An original backup has been created automatically."
            )

            self.go(4)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Analysis Failed",
                str(error)
            )

    def start_programming(self):
        try:
            self.converted_data = (
                self.workflow.prepare_synthetic_conversion(
                    self.target_unit
                )
            )
        except Exception as error:
            QMessageBox.critical(
                self,
                "Conversion Preparation Failed",
                str(error)
            )
            return

        self.program_step = 0
        self.programming_page.progress.setValue(0)
        self.go(5)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.advance_programming)
        self.timer.start(500)

    def advance_programming(self):
        stages = [
            (15, "Reading original data ✓"),
            (30, "Creating backup ✓"),
            (50, "Preparing conversion ✓"),
            (75, "Programming cluster..."),
            (90, "Verifying programming..."),
        ]

        if self.program_step < len(stages):
            value, text = stages[self.program_step]
            self.programming_page.progress.setValue(value)
            self.programming_page.step.setText(text)

            if self.program_step == 3:
                try:
                    self.hardware.write_memory(
                        self.converted_data
                    )
                except Exception as error:
                    self.timer.stop()
                    QMessageBox.critical(
                        self,
                        "Programming Failed",
                        str(error)
                    )
                    return

            self.program_step += 1
            return

        self.timer.stop()

        try:
            if not self.hardware.verify_memory(
                self.converted_data
            ):
                raise RuntimeError(
                    "Read-back verification failed."
                )

            self.programming_page.progress.setValue(100)
            self.programming_page.step.setText(
                "Programming verified ✓"
            )

            if self.target_unit == "MI":
                self.complete_page.direction.setText(
                    "KM → MILES"
                )
            else:
                self.complete_page.direction.setText(
                    "MILES → KM"
                )

            QTimer.singleShot(
                700,
                lambda: self.go(6)
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Verification Failed",
                str(error)
            )

    def reset_workflow(self):
        self.hardware = SimulatedProgrammer()
        self.workflow = ConversionWorkflow(
            self.hardware,
            self.profile
        )

        self.current_unit = None
        self.target_unit = None
        self.converted_data = None

        self.go(0)


def main():
    qt_app = QApplication(sys.argv)
    qt_app.setStyleSheet(STYLESHEET)

    window = MainWindow()
    window.show()

    sys.exit(qt_app.exec())


if __name__ == "__main__":
    main()
