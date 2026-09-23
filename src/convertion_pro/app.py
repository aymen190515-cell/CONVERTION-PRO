import sys
from pathlib import Path

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QComboBox, QStackedWidget, QFrame,
    QGridLayout, QProgressBar
)


# ============================================================
# THEME
# ============================================================

BG = "#071018"
PANEL = "#0C1823"
PANEL_2 = "#0A141E"
BORDER = "#1D3447"
TEXT = "#F4F7FB"
MUTED = "#8999AB"
BLUE = "#1687FF"
BLUE_2 = "#086BE3"
GREEN = "#39D98A"
AMBER = "#FFB648"


STYLE = f"""
QMainWindow {{
    background: {BG};
}}

QWidget {{
    background: {BG};
    color: {TEXT};
    font-family: Arial;
}}

QFrame#topbar {{
    background: #08131D;
    border-bottom: 1px solid {BORDER};
}}

QFrame#panel {{
    background: {PANEL};
    border: 1px solid {BORDER};
    border-radius: 12px;
}}

QFrame#subpanel {{
    background: {PANEL_2};
    border: 1px solid {BORDER};
    border-radius: 8px;
}}

QPushButton {{
    background: #101F2C;
    color: {TEXT};
    border: 1px solid #294157;
    border-radius: 7px;
    padding: 11px 18px;
    font-weight: 700;
}}

QPushButton:hover {{
    border: 1px solid {BLUE};
}}

QPushButton#primary {{
    background: {BLUE};
    border: 1px solid #43A1FF;
    color: white;
}}

QPushButton#primary:hover {{
    background: {BLUE_2};
}}

QPushButton#convert {{
    background: {BLUE};
    border: 1px solid #55A9FF;
    color: white;
    font-size: 21px;
    font-weight: 800;
    min-height: 58px;
}}

QPushButton#nav {{
    background: transparent;
    border: none;
    color: {MUTED};
    padding: 8px 14px;
}}

QPushButton#nav:hover {{
    color: white;
}}

QComboBox {{
    background: #0A1621;
    border: 1px solid #294157;
    border-radius: 7px;
    padding: 12px;
    min-height: 20px;
    color: white;
}}

QProgressBar {{
    background: #142332;
    border: none;
    border-radius: 5px;
    height: 10px;
}}

QProgressBar::chunk {{
    background: {BLUE};
    border-radius: 5px;
}}
"""


# ============================================================
# COMPONENTS
# ============================================================

def title(text):
    x = QLabel(text)
    x.setStyleSheet(
        "font-size:30px;font-weight:800;color:#F4F7FB;"
    )
    return x


def subtitle(text):
    x = QLabel(text)
    x.setStyleSheet(
        f"font-size:14px;color:{MUTED};"
    )
    return x


def section_label(text):
    x = QLabel(text.upper())
    x.setStyleSheet(
        f"font-size:11px;font-weight:800;color:{BLUE};"
        "letter-spacing:2px;"
    )
    return x


def panel():
    x = QFrame()
    x.setObjectName("panel")
    return x


def subpanel():
    x = QFrame()
    x.setObjectName("subpanel")
    return x


def primary(text):
    x = QPushButton(text)
    x.setObjectName("primary")
    return x


def stat_card(label, value, value_color=TEXT):
    card = subpanel()
    lay = QVBoxLayout(card)
    lay.setContentsMargins(16, 13, 16, 13)

    a = QLabel(label.upper())
    a.setStyleSheet(
        f"font-size:10px;font-weight:700;color:{MUTED};"
    )

    b = QLabel(value)
    b.setStyleSheet(
        f"font-size:15px;font-weight:800;color:{value_color};"
    )

    lay.addWidget(a)
    lay.addSpacing(4)
    lay.addWidget(b)

    return card


def status_row(name, value, success=True):
    row = subpanel()
    lay = QHBoxLayout(row)
    lay.setContentsMargins(14, 10, 14, 10)

    icon = QLabel("●")
    icon.setStyleSheet(
        f"color:{GREEN if success else AMBER};font-size:13px;"
    )

    left = QLabel(name)
    left.setStyleSheet("font-size:13px;")

    right = QLabel(value)
    right.setAlignment(Qt.AlignRight)
    right.setStyleSheet(
        f"font-size:12px;font-weight:700;"
        f"color:{GREEN if success else TEXT};"
    )

    lay.addWidget(icon)
    lay.addWidget(left)
    lay.addStretch()
    lay.addWidget(right)

    return row


def cluster_visual(text="JEEP\nINSTRUMENT CLUSTER"):
    frame = subpanel()
    frame.setMinimumHeight(210)

    lay = QVBoxLayout(frame)
    lay.setAlignment(Qt.AlignCenter)

    gauge_row = QHBoxLayout()

    for symbol in ("240", "140"):
        gauge = QLabel(
            f"""
            ◜────────◝
            │   {symbol}   │
            │    ●    │
            ◟────────◞
            """
        )
        gauge.setAlignment(Qt.AlignCenter)
        gauge.setStyleSheet(
            "font-family:monospace;"
            "font-size:17px;"
            "font-weight:700;"
            "color:#DDE7F0;"
        )
        gauge_row.addWidget(gauge)

    lay.addStretch()
    lay.addLayout(gauge_row)

    label = QLabel(text)
    label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet(
        f"font-size:11px;font-weight:800;color:{MUTED};"
    )
    lay.addWidget(label)
    lay.addStretch()

    return frame


# ============================================================
# MAIN WINDOW
# ============================================================

class ConversionPro(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("CONVERTION-PRO")
        self.resize(1180, 760)

        self.stack = QStackedWidget()

        root = QWidget()
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self.build_topbar())
        root_layout.addWidget(self.stack)

        self.setCentralWidget(root)

        self.build_pages()
        self.show_page(0)

    # --------------------------------------------------------
    # TOP BAR
    # --------------------------------------------------------

    def build_topbar(self):
        bar = QFrame()
        bar.setObjectName("topbar")
        bar.setFixedHeight(72)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(28, 0, 28, 0)

        logo_mark = QLabel("◉")
        logo_mark.setStyleSheet(
            f"font-size:26px;color:{BLUE};font-weight:900;"
        )

        brand_box = QVBoxLayout()

        brand = QLabel("CONVERTION PRO")
        brand.setStyleSheet(
            "font-size:15px;font-weight:900;"
            "letter-spacing:1px;"
        )

        tagline = QLabel("DRIVE FURTHER")
        tagline.setStyleSheet(
            f"font-size:8px;color:{MUTED};letter-spacing:2px;"
        )

        brand_box.addWidget(brand)
        brand_box.addWidget(tagline)

        lay.addWidget(logo_mark)
        lay.addLayout(brand_box)

        lay.addStretch()

        home = QPushButton("⌂\nHome")
        home.setObjectName("nav")
        home.clicked.connect(lambda: self.show_page(0))

        settings = QPushButton("⚙\nSettings")
        settings.setObjectName("nav")

        help_btn = QPushButton("?\nHelp")
        help_btn.setObjectName("nav")

        lay.addWidget(home)
        lay.addWidget(settings)
        lay.addWidget(help_btn)

        return bar

    # --------------------------------------------------------
    # PAGE WRAPPER
    # --------------------------------------------------------

    def page(self):
        widget = QWidget()

        outer = QVBoxLayout(widget)
        outer.setContentsMargins(42, 28, 42, 32)
        outer.setSpacing(14)

        return widget, outer

    def show_page(self, index):
        self.stack.setCurrentIndex(index)

    # --------------------------------------------------------
    # BUILD ALL
    # --------------------------------------------------------

    def build_pages(self):
        self.stack.addWidget(self.vehicle_page())
        self.stack.addWidget(self.connection_page())
        self.stack.addWidget(self.verify_page())
        self.stack.addWidget(self.ready_page())
        self.stack.addWidget(self.analyze_page())
        self.stack.addWidget(self.confirm_page())
        self.stack.addWidget(self.program_page())
        self.stack.addWidget(self.complete_page())
        self.stack.addWidget(self.advanced_page())

    # ========================================================
    # 1 SELECT VEHICLE
    # ========================================================

    def vehicle_page(self):
        w, lay = self.page()

        lay.addWidget(title("SELECT VEHICLE"))
        lay.addWidget(
            subtitle("Choose the make and model of the vehicle you want to work on.")
        )
        lay.addSpacing(8)

        form = panel()
        f = QGridLayout(form)
        f.setContentsMargins(22, 20, 22, 20)
        f.setHorizontalSpacing(18)

        make_label = QLabel("MAKE")
        make_label.setStyleSheet(
            f"font-size:10px;font-weight:800;color:{MUTED};"
        )

        model_label = QLabel("MODEL / GENERATION")
        model_label.setStyleSheet(
            f"font-size:10px;font-weight:800;color:{MUTED};"
        )

        make = QComboBox()
        make.addItems(["Jeep"])

        model = QComboBox()
        model.addItems(["Wrangler 2012 - 2018"])

        f.addWidget(make_label, 0, 0)
        f.addWidget(model_label, 0, 1)
        f.addWidget(make, 1, 0)
        f.addWidget(model, 1, 1)

        cont = primary("Continue  →")
        cont.clicked.connect(lambda: self.show_page(1))

        f.addWidget(cont, 2, 0, 1, 2, Qt.AlignCenter)

        lay.addWidget(form)

        lay.addWidget(section_label("Recent Vehicles"))

        recent = QHBoxLayout()

        vehicles = [
            ("Jeep", "Wrangler", "2012 - 2018"),
            ("Toyota", "RAV4", "2019 - 2024"),
            ("Ford", "F-150", "2015 - 2020"),
            ("Chevrolet", "Silverado", "2014 - 2018"),
        ]

        for make_name, model_name, years in vehicles:
            card = subpanel()
            c = QVBoxLayout(card)

            a = QLabel(make_name)
            a.setStyleSheet("font-weight:800;")

            b = QLabel(model_name)
            b.setStyleSheet("font-size:12px;")

            d = QLabel(years)
            d.setStyleSheet(f"font-size:11px;color:{MUTED};")

            c.addWidget(a)
            c.addWidget(b)
            c.addWidget(d)

            recent.addWidget(card)

        lay.addLayout(recent)
        lay.addStretch()

        bottom = QHBoxLayout()

        connected = QLabel("●  Programmer Connected")
        connected.setStyleSheet(
            f"font-size:10px;color:{GREEN};font-weight:700;"
        )

        version = QLabel("Software v0.2.0")
        version.setStyleSheet(
            f"font-size:10px;color:{MUTED};"
        )

        bottom.addWidget(connected)
        bottom.addStretch()
        bottom.addWidget(version)

        lay.addLayout(bottom)

        return w

    # ========================================================
    # 2 CONNECTION GUIDE
    # ========================================================

    def connection_page(self):
        w, lay = self.page()

        top = QHBoxLayout()

        back = QPushButton("←  Back")
        back.clicked.connect(lambda: self.show_page(0))

        heading = QVBoxLayout()
        t = title("Jeep Wrangler 2012 - 2018")
        t.setStyleSheet("font-size:19px;font-weight:800;")

        heading.addWidget(t)
        heading.addWidget(subtitle("Connection Guide"))

        top.addWidget(back)
        top.addStretch()
        top.addLayout(heading)
        top.addStretch()

        lay.addLayout(top)

        tabs = QHBoxLayout()

        for i, name in enumerate([
            "1. Interactive View",
            "2. Rear View",
            "3. Connector",
            "4. Cable",
            "5. Notes",
        ]):
            b = QPushButton(name)
            if i == 0:
                b.setObjectName("primary")
            tabs.addWidget(b)

        lay.addLayout(tabs)

        content = QHBoxLayout()

        visual = cluster_visual("JEEP WRANGLER CLUSTER")
        visual.setMinimumWidth(580)
        content.addWidget(visual, 3)

        info = panel()
        i = QVBoxLayout(info)

        i.addWidget(stat_card("Method", "BENCH", BLUE))
        i.addWidget(stat_card("Required Cable", "CP-JEEP-004"))
        i.addWidget(stat_card("Power State", "OFF"))

        steps = QLabel(
            "①  Connect CP-JEEP-004 to the cluster.\n\n"
            "②  Connect the other end to the programmer.\n\n"
            "③  Make sure the connector is fully seated."
        )
        steps.setWordWrap(True)
        steps.setStyleSheet(
            f"font-size:12px;color:{MUTED};"
        )

        i.addWidget(steps)
        i.addStretch()

        proceed = primary("Proceed  →")
        proceed.clicked.connect(lambda: self.show_page(2))
        i.addWidget(proceed)

        content.addWidget(info, 2)

        lay.addLayout(content)
        lay.addStretch()

        return w

    # ========================================================
    # 3 VERIFY
    # ========================================================

    def verify_page(self):
        w, lay = self.page()

        lay.addWidget(title("Verifying Connection"))
        lay.addWidget(
            subtitle("Jeep Wrangler 2012 - 2018")
        )

        body = QHBoxLayout()

        checks = panel()
        c = QVBoxLayout(checks)

        c.addWidget(status_row("Programmer detected", "OK"))
        c.addWidget(status_row("Cable detected", "CP-JEEP-004"))
        c.addWidget(status_row("Supply voltage", "12.3 V"))
        c.addWidget(status_row("Current draw", "Normal"))
        c.addWidget(status_row("Communication", "CAN OK"))
        c.addWidget(status_row("Cluster response", "Detected"))
        c.addWidget(status_row("Profile match", "Confirmed"))

        body.addWidget(checks, 3)

        success = panel()
        s = QVBoxLayout(success)
        s.setAlignment(Qt.AlignCenter)

        connector = QLabel("▣\n\nCLUSTER CONNECTOR\nCP-JEEP-004")
        connector.setAlignment(Qt.AlignCenter)
        connector.setMinimumHeight(180)
        connector.setStyleSheet(
            f"background:{PANEL_2};"
            f"border:1px solid {BORDER};"
            "border-radius:8px;"
            "font-size:15px;"
            "font-weight:800;"
        )

        check = QLabel("✓")
        check.setAlignment(Qt.AlignCenter)
        check.setStyleSheet(
            f"font-size:56px;color:{GREEN};font-weight:900;"
        )

        verified = QLabel("Connection Verified")
        verified.setAlignment(Qt.AlignCenter)
        verified.setStyleSheet(
            f"font-size:18px;color:{GREEN};font-weight:800;"
        )

        msg = QLabel("The cluster is ready for programming.")
        msg.setAlignment(Qt.AlignCenter)
        msg.setStyleSheet(
            f"font-size:11px;color:{MUTED};"
        )

        cont = primary("Continue  →")
        cont.clicked.connect(lambda: self.show_page(3))

        s.addWidget(connector)
        s.addWidget(check)
        s.addWidget(verified)
        s.addWidget(msg)
        s.addWidget(cont)

        body.addWidget(success, 2)

        lay.addLayout(body)
        lay.addStretch()

        return w

    # ========================================================
    # 4 READY
    # ========================================================

    def ready_page(self):
        w, lay = self.page()

        heading = QHBoxLayout()

        h = QVBoxLayout()
        h.addWidget(title("Jeep Wrangler 2012 - 2018"))
        h.addWidget(subtitle("Connection verified successfully."))

        connected = QLabel("● Connected")
        connected.setStyleSheet(
            f"color:{GREEN};font-weight:800;"
        )

        heading.addLayout(h)
        heading.addStretch()
        heading.addWidget(connected)

        lay.addLayout(heading)

        body = QHBoxLayout()

        body.addWidget(cluster_visual(), 3)

        right = panel()
        r = QVBoxLayout(right)

        r.addWidget(title("Cluster Ready"))
        r.addWidget(
            subtitle("Connection verified successfully.")
        )
        r.addStretch()

        convert = QPushButton("⇄   Convert")
        convert.setObjectName("convert")
        convert.clicked.connect(self.start_analysis)

        r.addWidget(convert)

        body.addWidget(right, 2)

        lay.addLayout(body)

        lay.addWidget(section_label("Advanced Tools"))

        tools = QHBoxLayout()

        for name in [
            "▣\nRead Memory",
            "▤\nWrite Memory",
            "□\nOpen File",
            "⇩\nSave File",
            "•••\nMore Tools",
        ]:
            b = QPushButton(name)
            if "More" in name:
                b.clicked.connect(lambda: self.show_page(8))
            tools.addWidget(b)

        lay.addLayout(tools)
        lay.addStretch()

        return w

    # ========================================================
    # 5 ANALYZE
    # ========================================================

    def analyze_page(self):
        w, lay = self.page()

        center = QVBoxLayout()
        center.setAlignment(Qt.AlignCenter)

        center.addWidget(title("Analyzing Cluster"), alignment=Qt.AlignCenter)
        center.addWidget(
            subtitle("Reading current configuration..."),
            alignment=Qt.AlignCenter
        )

        body = panel()
        b = QHBoxLayout(body)
        b.setContentsMargins(30, 25, 30, 25)

        left = QVBoxLayout()

        self.analysis_progress = QProgressBar()
        self.analysis_progress.setRange(0, 100)
        self.analysis_progress.setValue(0)

        left.addWidget(self.analysis_progress)
        left.addSpacing(18)

        self.analysis_rows = []

        names = [
            "Identifying cluster",
            "Reading data",
            "Detecting units",
            "Analyzing configuration",
        ]

        for n in names:
            lbl = QLabel("○  " + n)
            lbl.setStyleSheet(
                f"font-size:13px;color:{MUTED};"
            )
            self.analysis_rows.append(lbl)
            left.addWidget(lbl)

        left.addStretch()

        b.addLayout(left, 2)
        b.addWidget(cluster_visual(), 3)

        center.addWidget(body)

        lay.addLayout(center)
        lay.addStretch()

        return w

    def start_analysis(self):
        self.show_page(4)

        self.analysis_progress.setValue(0)

        for lbl in self.analysis_rows:
            lbl.setText(
                "○  " + lbl.text().replace("✓  ", "").replace("○  ", "")
            )
            lbl.setStyleSheet(
                f"font-size:13px;color:{MUTED};"
            )

        self.analysis_step = 0
        self.analysis_timer = QTimer(self)
        self.analysis_timer.timeout.connect(self.analysis_tick)
        self.analysis_timer.start(500)

    def analysis_tick(self):
        if self.analysis_step < len(self.analysis_rows):
            lbl = self.analysis_rows[self.analysis_step]
            text = lbl.text().replace("○  ", "")

            lbl.setText("✓  " + text)
            lbl.setStyleSheet(
                f"font-size:13px;color:{GREEN};font-weight:700;"
            )

            self.analysis_step += 1
            self.analysis_progress.setValue(
                int(self.analysis_step / len(self.analysis_rows) * 100)
            )

        else:
            self.analysis_timer.stop()
            QTimer.singleShot(350, lambda: self.show_page(5))

    # ========================================================
    # 6 CONFIRM
    # ========================================================

    def confirm_page(self):
        w, lay = self.page()

        lay.addWidget(title("Convert Cluster"))

        body = panel()
        b = QVBoxLayout(body)
        b.setContentsMargins(28, 25, 28, 25)

        comparison = QHBoxLayout()

        current = stat_card(
            "Current Configuration",
            "◴   KM\n      KM/H\n\nMetric",
            BLUE
        )

        arrow = QLabel("→")
        arrow.setAlignment(Qt.AlignCenter)
        arrow.setStyleSheet(
            f"font-size:34px;color:{BLUE};font-weight:800;"
        )

        target = stat_card(
            "Target Configuration",
            "◴   MILES\n      MPH\n\nImperial"
        )

        comparison.addWidget(current)
        comparison.addWidget(arrow)
        comparison.addWidget(target)

        b.addLayout(comparison)
        b.addSpacing(18)

        question = QLabel(
            "Do you want to convert this cluster to Miles / MPH?"
        )
        question.setAlignment(Qt.AlignCenter)
        question.setStyleSheet("font-size:14px;")

        b.addWidget(question)
        b.addSpacing(16)

        buttons = QHBoxLayout()

        cancel = QPushButton("Cancel")
        cancel.clicked.connect(lambda: self.show_page(3))

        confirm = primary("Confirm")
        confirm.clicked.connect(self.start_programming)

        buttons.addWidget(cancel)
        buttons.addWidget(confirm)

        b.addLayout(buttons)

        lay.addWidget(body)
        lay.addStretch()

        return w

    # ========================================================
    # 7 PROGRAMMING
    # ========================================================

    def program_page(self):
        w, lay = self.page()

        lay.addWidget(title("Converting Cluster"))

        warning = QLabel(
            "PLEASE DO NOT DISCONNECT OR TURN OFF THE POWER."
        )
        warning.setStyleSheet(
            f"font-size:12px;font-weight:800;color:{AMBER};"
        )

        lay.addWidget(warning)

        body = panel()
        b = QHBoxLayout(body)
        b.setContentsMargins(28, 25, 28, 25)

        left = QVBoxLayout()

        self.program_progress = QProgressBar()
        self.program_progress.setRange(0, 100)

        self.program_percent = QLabel("0%")
        self.program_percent.setStyleSheet(
            "font-size:15px;font-weight:800;"
        )

        progress_line = QHBoxLayout()
        progress_line.addWidget(self.program_progress)
        progress_line.addWidget(self.program_percent)

        left.addLayout(progress_line)
        left.addSpacing(20)

        self.program_rows = []

        names = [
            "Reading original data",
            "Creating backup",
            "Preparing conversion",
            "Programming cluster",
            "Verifying programming",
        ]

        for n in names:
            lbl = QLabel("○  " + n)
            lbl.setStyleSheet(
                f"font-size:13px;color:{MUTED};"
            )
            self.program_rows.append(lbl)
            left.addWidget(lbl)

        left.addStretch()

        b.addLayout(left, 2)
        b.addWidget(cluster_visual(), 2)

        lay.addWidget(body)
        lay.addStretch()

        return w

    def start_programming(self):
        self.show_page(6)

        self.program_step = 0
        self.program_progress.setValue(0)
        self.program_percent.setText("0%")

        for lbl in self.program_rows:
            clean = lbl.text().replace("✓  ", "").replace("○  ", "")
            lbl.setText("○  " + clean)
            lbl.setStyleSheet(
                f"font-size:13px;color:{MUTED};"
            )

        self.program_timer = QTimer(self)
        self.program_timer.timeout.connect(self.program_tick)
        self.program_timer.start(650)

    def program_tick(self):
        if self.program_step < len(self.program_rows):
            lbl = self.program_rows[self.program_step]

            text = lbl.text().replace("○  ", "")
            lbl.setText("✓  " + text)
            lbl.setStyleSheet(
                f"font-size:13px;color:{GREEN};font-weight:700;"
            )

            self.program_step += 1

            value = int(
                self.program_step / len(self.program_rows) * 100
            )

            self.program_progress.setValue(value)
            self.program_percent.setText(f"{value}%")

        else:
            self.program_timer.stop()
            QTimer.singleShot(450, lambda: self.show_page(7))

    # ========================================================
    # 8 COMPLETE
    # ========================================================

    def complete_page(self):
        w, lay = self.page()

        lay.addStretch()

        check = QLabel("✓")
        check.setAlignment(Qt.AlignCenter)
        check.setStyleSheet(
            f"font-size:62px;color:{GREEN};font-weight:900;"
        )

        done = title("Conversion Complete")
        done.setAlignment(Qt.AlignCenter)

        direction = QLabel("KM  →  MILES")
        direction.setAlignment(Qt.AlignCenter)
        direction.setStyleSheet(
            "font-size:24px;font-weight:900;"
        )

        details = panel()
        d = QVBoxLayout(details)
        d.setContentsMargins(30, 20, 30, 20)

        verified = QLabel("Programming verified successfully.")
        verified.setAlignment(Qt.AlignCenter)

        backup = QLabel("Original backup saved.")
        backup.setAlignment(Qt.AlignCenter)
        backup.setStyleSheet(
            f"color:{MUTED};"
        )

        original = QLabel(
            "▣  Original File\n"
            "    Jeep_Wrangler_2012-2018_original.bin"
        )

        converted = QLabel(
            "▣  Converted File\n"
            "    Jeep_Wrangler_2012-2018_MI.bin"
        )

        original.setStyleSheet(
            f"background:{PANEL_2};padding:10px;"
            f"border:1px solid {BORDER};border-radius:6px;"
        )

        converted.setStyleSheet(
            f"background:{PANEL_2};padding:10px;"
            f"border:1px solid {BORDER};border-radius:6px;"
        )

        d.addWidget(verified)
        d.addWidget(backup)
        d.addSpacing(12)
        d.addWidget(original)
        d.addWidget(converted)

        safe = QLabel("It is now safe to disconnect the cluster.")
        safe.setAlignment(Qt.AlignCenter)
        safe.setStyleSheet(
            f"font-size:13px;color:{GREEN};font-weight:800;"
        )

        finish = primary("Done")
        finish.clicked.connect(lambda: self.show_page(0))

        lay.addWidget(check)
        lay.addWidget(done)
        lay.addWidget(direction)
        lay.addWidget(details)
        lay.addWidget(safe)
        lay.addWidget(finish, alignment=Qt.AlignCenter)
        lay.addStretch()

        return w

    # ========================================================
    # 9 ADVANCED
    # ========================================================

    def advanced_page(self):
        w, lay = self.page()

        body = QHBoxLayout()

        sidebar = panel()
        sidebar.setFixedWidth(180)

        s = QVBoxLayout(sidebar)

        cluster = primary("◉  Cluster")
        files = QPushButton("□  Files")
        diagnostics = QPushButton("⌁  Diagnostics")
        developer = QPushButton("⌘  Developer")
        settings = QPushButton("⚙  Settings")

        s.addWidget(cluster)
        s.addWidget(files)
        s.addWidget(diagnostics)
        s.addWidget(developer)
        s.addStretch()
        s.addWidget(settings)

        body.addWidget(sidebar)

        content = QVBoxLayout()

        head = QHBoxLayout()

        head.addWidget(title("Advanced Tools"))
        head.addStretch()

        back = QPushButton("← Cluster")
        back.clicked.connect(lambda: self.show_page(3))

        head.addWidget(back)

        content.addLayout(head)

        grid = QGridLayout()
        grid.setSpacing(12)

        tools = [
            ("▣", "Read Memory", "Read full cluster memory"),
            ("▤", "Write Memory", "Write memory to cluster"),
            ("✓", "Verify Memory", "Verify written data"),
            ("◎", "Identify Cluster", "Show detailed information"),
            ("□", "Open File", "Load a binary file"),
            ("⇩", "Save File", "Save current data"),
            ("⇄", "Compare Files", "Compare two files"),
            ("↶", "Restore Backup", "Write original backup"),
        ]

        for index, (icon, name, desc) in enumerate(tools):
            card = subpanel()
            c = QVBoxLayout(card)

            ico = QLabel(icon)
            ico.setAlignment(Qt.AlignCenter)
            ico.setStyleSheet(
                f"font-size:25px;color:{BLUE};font-weight:800;"
            )

            n = QLabel(name)
            n.setAlignment(Qt.AlignCenter)
            n.setStyleSheet(
                "font-size:13px;font-weight:800;"
            )

            d = QLabel(desc)
            d.setAlignment(Qt.AlignCenter)
            d.setWordWrap(True)
            d.setStyleSheet(
                f"font-size:10px;color:{MUTED};"
            )

            c.addStretch()
            c.addWidget(ico)
            c.addWidget(n)
            c.addWidget(d)
            c.addStretch()

            row = index // 4
            col = index % 4

            grid.addWidget(card, row, col)

        content.addLayout(grid)
        content.addStretch()

        body.addLayout(content, 1)

        lay.addLayout(body)

        return w


# ============================================================
# START
# ============================================================

def run():
    app = QApplication(sys.argv)

    app.setStyleSheet(STYLE)

    font = QFont("Arial")
    font.setPointSize(11)
    app.setFont(font)

    window = ConversionPro()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    run()
