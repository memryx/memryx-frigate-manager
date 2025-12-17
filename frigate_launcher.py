#!/usr/bin/env python3
"""
MemryX + Frigate Launcher
A comprehensive GUI application for managing Frigate installation and configuration
"""

import sys
import os
import subprocess
import threading
import time
import glob
import getpass
import shutil
import tempfile
import webbrowser
import platform
from pathlib import Path

# Try to import psutil for system monitoring
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Import required Qt modules
try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QTextEdit, QPushButton, QLabel, QProgressBar,
        QGroupBox, QFormLayout, QCheckBox, QMessageBox, QSplitter,
        QFrame, QScrollArea, QGridLayout, QSpacerItem, QSizePolicy,
        QDialog, QLineEdit, QDialogButtonBox, QFileDialog, QToolButton
    )
    from PySide6.QtCore import QThread, Signal, QTimer, Qt, QEvent, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup
    from PySide6.QtGui import QFont, QPixmap, QPalette, QColor, QIcon, QPainter
except ImportError as e:
    print("❌ Required GUI libraries are not available.")
    print("   Please run './launch.sh' to set up the environment properly.")
    print(f"   Error: {e}")
    sys.exit(1)

# Import Simple Camera GUI
try:
    from camera_gui import SimpleCameraGUI
except ImportError as e:
    print(f"Warning: Could not import SimpleCameraGUI: {e}")
    SimpleCameraGUI = None

# Import Advanced Config GUI
try:
    from advanced_config_gui import ConfigGUI
except ImportError as e:
    print(f"Warning: Could not import ConfigGUI: {e}")
    ConfigGUI = None

# ============================================================================
# MODERN PROFESSIONAL DESIGN SYSTEM - Teal/Blue Theme
# ============================================================================
# Primary Brand Colors - Professional Teal Scheme
PRIMARY_COLOR = "#4a90a4"      # Professional teal for primary actions
PRIMARY_DARK = "#38758a"       # Darker teal for hover
PRIMARY_DARKER = "#2d6374"     # Even darker for pressed
PRIMARY_LIGHT = "#5ca9bf"      # Light teal for accents
PRIMARY_ULTRA_LIGHT = "#e0f2f7" # Ultra light teal for backgrounds

# Complementary Accent Colors
ACCENT_CORAL = "#f97316"       # Vibrant coral/orange accent (NEW!)
ACCENT_CORAL_DARK = "#ea580c"  # Deep coral for hover
ACCENT_BLUE = "#06b6d4"        # Bright cyan accent
ACCENT_BLUE_DARK = "#0891b2"   # Deep cyan
SUCCESS_COLOR = "#10b981"      # Modern green success
SUCCESS_DARK = "#059669"       # Deep green
WARNING_COLOR = "#f59e0b"      # Amber warning  
ERROR_COLOR = "#ef4444"        # Modern red error
INFO_COLOR = "#06b6d4"         # Cyan info

# Neutral Palette - Clean Grays
BACKGROUND = "#f9fafb"         # Light gray background
CARD_BG = "#ffffff"            # Pure white cards
SURFACE_BG = "#f3f4f6"         # Secondary surface
TEXT_PRIMARY = "#111827"       # Darker gray text (enhanced contrast)
TEXT_SECONDARY = "#4b5563"     # Medium gray text
TEXT_MUTED = "#6b7280"         # Light gray text
BORDER_COLOR = "#e5e7eb"       # Subtle border
BORDER_LIGHT = "#f3f4f6"       # Very light border

# Glass Effect Colors  
GLASS_BG = "rgba(255, 255, 255, 0.75)"
GLASS_BORDER = "rgba(74, 144, 164, 0.2)"

# Status constants
STATUS_NOT_STARTED = "not_started"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"
STATUS_WARNING = "warning"
STATUS_ERROR = "error"

# ============================================================================
# COLLAPSIBLE SECTION WIDGET
# ============================================================================
class CollapsibleSection(QWidget):
    """A collapsible section widget with smooth animations and status indicators"""
    
    toggled = Signal(bool)  # Emits True when expanded, False when collapsed
    
    def __init__(self, title="Section", subtitle="", show_status=True, parent=None):
        super().__init__(parent)
        self.is_expanded = False
        self.status = STATUS_NOT_STARTED
        self.title_text = title
        self.subtitle_text = subtitle
        self.show_status = show_status
        
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 10)
        main_layout.setSpacing(0)
        
        # Header (always visible)
        self.header = QFrame()
        self.header.setObjectName("collapsibleHeader")
        self.header.setCursor(Qt.PointingHandCursor)
        self.header.setMinimumHeight(60)
        
        header_layout = QHBoxLayout(self.header)
        header_layout.setContentsMargins(20, 10, 20, 10)
        
        # Modern toggle button with icon
        self.toggle_button = QToolButton()
        self.toggle_button.setText("▶")
        self.toggle_button.setStyleSheet(f"""
            QToolButton {{
                border: none;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_DARK});
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 10px;
            }}
            QToolButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {PRIMARY_LIGHT}, stop:1 {PRIMARY_COLOR});
            }}
            QToolButton:pressed {{
                background: {PRIMARY_DARK};
            }}
        """)
        self.toggle_button.setFixedSize(36, 36)
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.clicked.connect(self.toggle)
        header_layout.addWidget(self.toggle_button)
        
        # Spacer for visual separation
        header_layout.addSpacing(12)
        
        # Title and subtitle with modern typography
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        
        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
                letter-spacing: -0.4px;
            }}
        """)
        self.title_label.setCursor(Qt.PointingHandCursor)
        self.title_label.mousePressEvent = lambda e: self.toggle()
        title_layout.addWidget(self.title_label)
        
        if self.subtitle_text:
            self.subtitle_label = QLabel(self.subtitle_text)
            self.subtitle_label.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SECONDARY};
                    font-size: 16px;
                    font-weight: 500;
                }}
            """)
            self.subtitle_label.setCursor(Qt.PointingHandCursor)
            self.subtitle_label.mousePressEvent = lambda e: self.toggle()
            title_layout.addWidget(self.subtitle_label)
        
        header_layout.addLayout(title_layout, 1)
        
        # Modern status badge with icon
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                font-weight: 600;
                padding: 10px 18px;
                border-radius: 24px;
                background: {SURFACE_BG};
                border: 2px solid {BORDER_LIGHT};
            }}
        """)
        self.status_label.setCursor(Qt.PointingHandCursor)
        self.status_label.mousePressEvent = lambda e: self.toggle()
        self.update_status_display()
        
        # Only add status label if show_status is True
        if self.show_status:
            header_layout.addWidget(self.status_label)
        
        # Make header clickable (for any empty space)
        self.header.mousePressEvent = lambda e: self.toggle()
        
        main_layout.addWidget(self.header)
        
        # Content container (collapsible)
        self.content_container = QFrame()
        self.content_container.setObjectName("collapsibleContent")
        self.content_layout = QVBoxLayout(self.content_container)
        self.content_layout.setContentsMargins(20, 10, 20, 10)
        self.content_layout.setSpacing(10)
        
        # Initially hidden - use both max height and visibility
        self.content_container.setMaximumHeight(0)
        self.content_container.setMinimumHeight(0)
        self.content_container.hide()  # Use hide() instead of setVisible(False)
        
        main_layout.addWidget(self.content_container)
        
        # Store initial stylesheet for dynamic updates
        self.base_stylesheet = f"""
            QFrame#collapsibleHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {CARD_BG}, stop:1 #fefefe);
                border: 2px solid {BORDER_COLOR};
                border-radius: 16px;
                padding: 2px;
            }}
            QFrame#collapsibleHeader:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ffffff, stop:0.5 {PRIMARY_ULTRA_LIGHT}, stop:1 #ffffff);
                border: 2px solid {PRIMARY_LIGHT};
            }}
            QFrame#collapsibleContent {{
                background: {CARD_BG};
                border: 2px solid {BORDER_COLOR};
                border-top: 1px solid {BORDER_LIGHT};
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
                padding: 20px;
                margin-top: -2px;
            }}
        """
        
        self.expanded_stylesheet = f"""
            QFrame#collapsibleHeader {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PRIMARY_ULTRA_LIGHT}, stop:0.5 #ffffff, stop:1 {PRIMARY_ULTRA_LIGHT});
                border: 3px solid {PRIMARY_COLOR};
                border-radius: 16px;
                padding: 2px;
            }}
            QFrame#collapsibleHeader:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PRIMARY_ULTRA_LIGHT}, stop:0.5 #ffffff, stop:1 {PRIMARY_ULTRA_LIGHT});
                border: 3px solid {PRIMARY_COLOR};
            }}
            QFrame#collapsibleContent {{
                background: {CARD_BG};
                border: 3px solid {PRIMARY_COLOR};
                border-top: 1px solid {PRIMARY_LIGHT};
                border-bottom-left-radius: 16px;
                border-bottom-right-radius: 16px;
                padding: 20px;
                margin-top: -3px;
            }}
        """
        
        # Apply initial stylesheet
        self.setStyleSheet(self.base_stylesheet)
    
    def set_content(self, widget):
        """Set the content widget for this collapsible section"""
        # Clear existing content
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new content
        self.content_layout.addWidget(widget)
        
    def toggle(self):
        """Toggle the expanded/collapsed state"""
        self.is_expanded = not self.is_expanded
        
        if self.is_expanded:
            self.expand()
        else:
            self.collapse()
            
        self.toggled.emit(self.is_expanded)
        
    def expand(self):
        """Expand the section with animation and enhanced styling"""
        self.is_expanded = True
        self.toggle_button.setText("▼")
        
        # Apply expanded styling for visual prominence
        self.setStyleSheet(self.expanded_stylesheet)
        
        # Show the container first
        self.content_container.show()
        
        # Remove height constraints to allow content to display
        self.content_container.setMaximumHeight(16777215)
        self.content_container.setMinimumHeight(0)
        
        # Adjust the size policy to allow expansion
        self.content_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Expanding
        )
        
        # Force layout update
        self.content_container.adjustSize()
        self.content_container.updateGeometry()
        self.updateGeometry()
        
    def collapse(self):
        """Collapse the section with animation and restore normal styling"""
        self.is_expanded = False
        self.toggle_button.setText("▶")
        
        # Restore base styling
        self.setStyleSheet(self.base_stylesheet)
        
        # Set height to 0
        self.content_container.setMaximumHeight(0)
        self.content_container.setMinimumHeight(0)
        
        # Adjust size policy
        self.content_container.setSizePolicy(
            QSizePolicy.Expanding, QSizePolicy.Fixed
        )
        
        # Force update before hiding
        self.content_container.updateGeometry()
        
        # Hide after a brief delay to allow collapse animation
        from PySide6.QtCore import QTimer
        QTimer.singleShot(50, self.content_container.hide)
        
    def set_status(self, status):
        """Set the status of this section"""
        self.status = status
        self.update_status_display()
        
    def update_status_display(self):
        """Update the status indicator display with modern vibrant colors"""
        status_map = {
            STATUS_NOT_STARTED: ("○ Not Started", TEXT_MUTED, SURFACE_BG, BORDER_LIGHT),
            STATUS_IN_PROGRESS: ("⚡ In Progress", PRIMARY_COLOR, "#ede9fe", PRIMARY_LIGHT),
            STATUS_COMPLETED: ("✓ Completed", SUCCESS_COLOR, "#d1fae5", SUCCESS_DARK),
            STATUS_WARNING: ("⚠ Warning", WARNING_COLOR, "#fef3c7", WARNING_COLOR),
            STATUS_ERROR: ("✕ Error", ERROR_COLOR, "#fee2e2", ERROR_COLOR),
        }
        
        text, text_color, bg_color, border_color = status_map.get(
            self.status, ("○ Unknown", TEXT_MUTED, SURFACE_BG, BORDER_LIGHT)
        )
        
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {text_color};
                font-size: 14px;
                font-weight: 600;
                padding: 10px 18px;
                border-radius: 24px;
                background: {bg_color};
                border: 2px solid {border_color};
            }}
        """)

# ============================================================================
# WELCOME WIDGET
# ============================================================================
class WelcomeWidget(QWidget):
    """Welcome message widget displayed at the top of the application"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components with premium modern design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 24)
        
        # Premium welcome card with gradient border effect
        card = QFrame()
        card.setObjectName("welcomeCard")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(48, 36, 48, 36)
        card_layout.setSpacing(16)
        
        # Hero title with gradient text effect (simulated with styling)
        title = QLabel("Welcome to Frigate MemryX Manager")
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 34px;
                font-weight: 700;
                letter-spacing: -0.8px;
                margin-bottom: 8px;
            }}
        """)
        card_layout.addWidget(title)
        
        # Subtitle with accent
        subtitle = QLabel("Your intelligent NVR management system")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {PRIMARY_COLOR};
                font-size: 14px;
                font-weight: 600;
                letter-spacing: -0.2px;
                margin-bottom: 16px;
            }}
        """)
        card_layout.addWidget(subtitle)
        
        # Feature list with modern styling
        description = QLabel(
            "Complete setup wizard for your security system:\n\n"
            "⚡ Install system prerequisites (MemryX SDK, Docker)\n"
            "🎯 Download and configure Frigate NVR\n"
            "📹 Set up cameras and detection objects \n"
            "🚀 Launch and monitor your system in real-time\n\n"
            "Follow each step below to complete your setup."
        )
        description.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 16px;
                line-height: 2.0;
                font-weight: 500;
            }}
        """)
        description.setWordWrap(True)
        card_layout.addWidget(description)
        
        # Apply premium card styling with border gradient effect
        card.setStyleSheet(f"""
            QFrame#welcomeCard {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {CARD_BG}, stop:0.5 #fefefe, stop:1 {CARD_BG});
                border: 3px solid;
                border-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PRIMARY_COLOR}, stop:0.5 {ACCENT_BLUE}, stop:1 {PRIMARY_COLOR});
                border-radius: 20px;
            }}
        """)
        layout.addWidget(card)

# ============================================================================
# PREREQUISITES WIDGET (Section 1)
# ============================================================================
class PrerequisitesWidget(QWidget):
    """Widget for managing prerequisites (MemryX SDK and Docker installation)"""
    
    status_changed = Signal(str)  # Emits status when prerequisites change
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.memryx_install_worker = None
        self.docker_install_worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)  # Generous spacing between sections
        
        # ===== MemryX SDK Section =====
        memryx_section = QWidget()
        memryx_section_layout = QVBoxLayout(memryx_section)
        memryx_section_layout.setContentsMargins(0, 0, 0, 0)
        memryx_section_layout.setSpacing(15)
        
        # Section header with icon
        memryx_header = QLabel("📦 MemryX SDK Installation")
        memryx_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        memryx_section_layout.addWidget(memryx_header)
        
        # Description note
        memryx_note = QLabel("MemryX accelerator drivers and runtime libraries")
        memryx_note.setWordWrap(True)
        memryx_note.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 16px;
                padding: 12px 16px;
                background: #eff6ff;
                border-left: 3px solid #60a5fa;
                border-radius: 8px;
                line-height: 1.5;
            }}
        """)
        memryx_section_layout.addWidget(memryx_note)
        
        # Status container - compact horizontal layout
        status_container = QWidget()
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)
        
        # Status display - more compact (green background fits text width)
        self.memryx_status_label = QLabel("Status: ✅ Installed (2 device(s) | drivers:3.3.6-7.1, acc32:3.1.6-7, manager:2.3.0-7)")
        self.memryx_status_label.setWordWrap(False)
        self.memryx_status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.memryx_status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 500;
                padding: 12px 16px;
                background: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 8px;
                line-height: 1.4;
            }}
        """)
        status_layout.addWidget(self.memryx_status_label, 0)  # No stretch
        status_layout.addStretch(1)  # Add stretch to push everything left
        
        # Installed indicator - compact badge on the right
        self.memryx_installed_label = QLabel("✅ MemryX 2.1 installed")
        self.memryx_installed_label.setStyleSheet(f"""
            QLabel {{
                color: white;
                font-size: 14px;
                font-weight: 600;
                padding: 8px 16px;
                background: {SUCCESS_COLOR};
                border-radius: 6px;
            }}
        """)
        status_layout.addWidget(self.memryx_installed_label, 0)  # No stretch
        
        memryx_section_layout.addWidget(status_container)
        
        # Buttons - clean and spacious
        memryx_buttons = QHBoxLayout()
        memryx_buttons.setSpacing(12)
        
        self.check_memryx_btn = QPushButton("🔍 Check Installation")
        self.check_memryx_btn.clicked.connect(self.check_all_status)
        self.check_memryx_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.check_memryx_btn.setMinimumHeight(48)
        self.check_memryx_btn.setMinimumWidth(180)
        
        self.install_memryx_btn = QPushButton("📦 Install MemryX SDK")
        self.install_memryx_btn.clicked.connect(self.install_memryx)
        self.install_memryx_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        self.install_memryx_btn.setMinimumHeight(48)
        self.install_memryx_btn.setMinimumWidth(180)
        
        self.update_memryx_btn = QPushButton("🔄 Update SDK")
        self.update_memryx_btn.clicked.connect(self.update_memryx)
        self.update_memryx_btn.setStyleSheet(self.get_button_style(SUCCESS_COLOR))
        self.update_memryx_btn.setMinimumHeight(48)
        self.update_memryx_btn.setMinimumWidth(140)
        self.update_memryx_btn.setVisible(False)
        
        memryx_buttons.addWidget(self.check_memryx_btn)
        memryx_buttons.addWidget(self.install_memryx_btn)
        memryx_buttons.addWidget(self.update_memryx_btn)
        memryx_buttons.addStretch()
        
        memryx_section_layout.addLayout(memryx_buttons)
        layout.addWidget(memryx_section)
        
        # Elegant divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider1)
        
        # ===== Docker Section =====
        docker_section = QWidget()
        docker_section_layout = QVBoxLayout(docker_section)
        docker_section_layout.setContentsMargins(0, 0, 0, 0)
        docker_section_layout.setSpacing(15)
        
        # Section header
        docker_header = QLabel("🐳 Docker Installation")
        docker_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        docker_section_layout.addWidget(docker_header)
        
        # Description note
        docker_note = QLabel("Container runtime for Frigate")
        docker_note.setWordWrap(True)
        docker_note.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 16px;
                padding: 12px 16px;
                background: #eff6ff;
                border-left: 3px solid #60a5fa;
                border-radius: 8px;
                line-height: 1.5;
            }}
        """)
        docker_section_layout.addWidget(docker_note)
        
        # Docker status container with left alignment
        docker_status_container = QHBoxLayout()
        docker_status_container.setContentsMargins(0, 0, 0, 0)
        
        # Docker status - more compact (green background fits text width)
        self.docker_status_label = QLabel("Status: ✅ Docker version 25.1.3, build 123456a")
        self.docker_status_label.setWordWrap(False)
        self.docker_status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.docker_status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 500;
                padding: 12px 16px;
                background: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 8px;
                line-height: 1.4;
            }}
        """)
        docker_status_container.addWidget(self.docker_status_label)
        docker_status_container.addStretch()
        docker_section_layout.addLayout(docker_status_container)
        
        # Docker Compose status container with left alignment
        compose_status_container = QHBoxLayout()
        compose_status_container.setContentsMargins(0, 0, 0, 0)
        
        # Docker Compose status - compact (green background fits text width)
        self.docker_compose_status_label = QLabel("Docker Compose: ✅ Docker Compose version v5.0.0")
        self.docker_compose_status_label.setWordWrap(False)
        self.docker_compose_status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.docker_compose_status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 500;
                padding: 12px 16px;
                background: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 8px;
                line-height: 1.4;
            }}
        """)
        compose_status_container.addWidget(self.docker_compose_status_label)
        compose_status_container.addStretch()
        docker_section_layout.addLayout(compose_status_container)
        
        # Buttons - clean and spacious
        docker_buttons = QHBoxLayout()
        docker_buttons.setSpacing(12)
        
        self.check_docker_btn = QPushButton("🔍 Check Docker")
        self.check_docker_btn.clicked.connect(self.check_all_status)
        self.check_docker_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.check_docker_btn.setMinimumHeight(48)
        self.check_docker_btn.setMinimumWidth(160)
        
        self.install_docker_btn = QPushButton("🐳 Install Docker")
        self.install_docker_btn.clicked.connect(self.install_docker)
        self.install_docker_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        self.install_docker_btn.setMinimumHeight(48)
        self.install_docker_btn.setMinimumWidth(160)
        
        self.start_docker_btn = QPushButton("▶️ Start Docker")
        self.start_docker_btn.clicked.connect(self.start_docker_daemon)
        self.start_docker_btn.setStyleSheet(self.get_button_style(SUCCESS_COLOR))
        self.start_docker_btn.setMinimumHeight(48)
        self.start_docker_btn.setMinimumWidth(160)
        self.start_docker_btn.setVisible(False)
        
        docker_buttons.addWidget(self.check_docker_btn)
        docker_buttons.addWidget(self.install_docker_btn)
        docker_buttons.addWidget(self.start_docker_btn)
        docker_buttons.addStretch()
        
        docker_section_layout.addLayout(docker_buttons)
        layout.addWidget(docker_section)
        
        # Elegant divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider2)
        
        # ===== Installation Log Section (at bottom) =====
        log_section = QWidget()
        log_section_layout = QVBoxLayout(log_section)
        log_section_layout.setContentsMargins(0, 0, 0, 0)
        log_section_layout.setSpacing(12)
        
        # Logs header
        log_header = QLabel("📋 Installation Log")
        log_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        log_section_layout.addWidget(log_header)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(180)
        self.log_output.setMaximumHeight(280)
        self.log_output.setStyleSheet(f"""
            QTextEdit {{
                background: #1e293b;
                color: #e2e8f0;
                font-family: 'Courier New', 'Consolas', monospace;
                font-size: 14px;
                border: 2px solid #334155;
                border-radius: 8px;
                padding: 12px;
                line-height: 1.4;
            }}
        """)
        log_section_layout.addWidget(self.log_output)
        
        layout.addWidget(log_section)
        
        layout.addStretch()
        
        # Initial status check
        QTimer.singleShot(100, self.check_all_status)
        
    def create_subsection(self, title, description):
        """Create a modern subsection container with better styling"""
        group = QGroupBox()
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {CARD_BG};
                border: 2px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 24px;
                margin-top: 0px;
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(12)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                letter-spacing: -0.3px;
            }}
        """)
        group_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 16px;
                margin-bottom: 16px;
                font-weight: 400;
                line-height: 1.5;
            }}
        """)
        group_layout.addWidget(desc_label)
        
        return group
        
    def get_button_style(self, color):
        """Get modern button CSS with better styling"""
        # Map colors to their hover variants
        color_map = {
            INFO_COLOR: "#0891b2",
            PRIMARY_COLOR: PRIMARY_DARK,
            SUCCESS_COLOR: SUCCESS_DARK,
        }
        hover_color = color_map.get(color, color)
        
        return f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: {hover_color};
            }}
            QPushButton:pressed {{
                background: {hover_color};
                padding-top: 13px;
                padding-bottom: 11px;
            }}
            QPushButton:disabled {{
                background: {SURFACE_BG};
                color: {TEXT_MUTED};
            }}
        """
        
    def check_all_status(self):
        """Check status of all prerequisites and update overall status"""
        memryx_ok = self.check_memryx_status()
        docker_ok = self.check_docker_status()
        
        # Debug logging
        self.log_output.append(f"📊 Status Check: MemryX={memryx_ok}, Docker={docker_ok}")
        
        # Only emit completed status if BOTH MemryX and Docker are fully installed
        if memryx_ok and docker_ok:
            self.log_output.append("✅ All prerequisites completed!")
            self.status_changed.emit(STATUS_COMPLETED)
        else:
            self.log_output.append("⚡ Prerequisites in progress...")
            self.status_changed.emit(STATUS_IN_PROGRESS)
        
    def check_memryx_status(self):
        """Check MemryX installation status"""
        self.log_output.append("🔍 Checking MemryX SDK installation...")
        try:
            # Check for MemryX devices
            devices = [d for d in glob.glob("/dev/memx*") if "_feature" not in d]
            device_count = len(devices)
            
            if device_count > 0:
                # Helper function to get package version
                def get_package_version(package_name):
                    """Get the installed version of a package"""
                    try:
                        # Method 1: dpkg-query (cleaner)
                        result = subprocess.run(['dpkg-query', '-W', '-f=${Version}', package_name], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0 and result.stdout.strip():
                            return result.stdout.strip()
                    except Exception:
                        pass
                    
                    try:
                        # Method 2: dpkg -l (fallback)
                        result = subprocess.run(['dpkg', '-l', package_name], 
                                              capture_output=True, text=True, timeout=5)
                        if result.returncode == 0:
                            for line in result.stdout.split('\n'):
                                if package_name in line and line.startswith(('ii', 'hi')):
                                    parts = line.split()
                                    if len(parts) >= 3:
                                        return parts[2]
                    except Exception:
                        pass
                    
                    return None
                
                # Get versions for all three packages
                drivers_version = get_package_version('memx-drivers')
                accl_version = get_package_version('memx-accl')
                manager_version = get_package_version('mxa-manager')
                
                # Build version info string
                version_parts = []
                if drivers_version:
                    version_parts.append(f"drivers:{drivers_version}")
                if accl_version:
                    version_parts.append(f"accl:{accl_version}")
                if manager_version:
                    version_parts.append(f"manager:{manager_version}")
                
                version_info = ""
                if version_parts:
                    version_info = f" | {', '.join(version_parts)}"
                
                # Check if version is 2.1 (Frigate only supports 2.1)
                needs_update = False
                if drivers_version:
                    # Extract major.minor version (e.g., "2.1.0-7" -> "2.1")
                    version_major_minor = '.'.join(drivers_version.split('.')[:2])
                    if version_major_minor != "2.1":
                        needs_update = True
                
                status_text = f"Status: ✅ Installed ({device_count} device(s){version_info})"
                
                # Update button text, state, and visibility based on version
                if needs_update:
                    # Version is NOT 2.1 - enable button with warning style
                    self.update_memryx_btn.setText("⚠️ Update to MemryX 2.1 (Required)")
                    self.update_memryx_btn.setEnabled(True)
                    self.update_memryx_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 {WARNING_COLOR}, stop:1 #d97706);
                            color: white;
                            border: none;
                            border-radius: 8px;
                            font-size: 14px;
                            font-weight: 600;
                            padding: 10px 16px;
                        }}
                        QPushButton:hover {{
                            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                stop:0 #d97706, stop:1 #b45309);
                        }}
                    """)
                    status_text += " ⚠️ Version 2.1 required for Frigate"
                    self.memryx_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {WARNING_COLOR};
                            font-size: 16px;
                            font-weight: bold;
                            padding: 8px;
                            background: #fef3c7;
                            border-radius: 4px;
                        }}
                    """)
                else:
                    # Version IS 2.1 - disable button (correct version already installed)
                    self.update_memryx_btn.setText("✅ MemryX 2.1 Installed")
                    self.update_memryx_btn.setEnabled(False)
                    self.update_memryx_btn.setStyleSheet(f"""
                        QPushButton {{
                            background: #e2e8f0;
                            color: #64748b;
                            border: 2px solid #cbd5e0;
                            border-radius: 8px;
                            font-size: 14px;
                            font-weight: 600;
                            padding: 10px 16px;
                        }}
                        QPushButton:disabled {{
                            background: #f1f5f9;
                            color: #94a3b8;
                            border: 2px solid #e2e8f0;
                        }}
                    """)
                    self.memryx_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {SUCCESS_COLOR};
                            font-size: 16px;
                            font-weight: bold;
                            padding: 8px;
                            background: #c6f6d5;
                            border-radius: 4px;
                        }}
                    """)
                
                self.memryx_status_label.setText(status_text)
                self.install_memryx_btn.setVisible(False)
                self.update_memryx_btn.setVisible(True)
                
                log_msg = f"✅ MemryX SDK is installed - {device_count} device(s) detected"
                if version_info:
                    log_msg += version_info
                if needs_update:
                    log_msg += " ⚠️ Version 2.1 required for Frigate compatibility"
                self.log_output.append(log_msg)
                return True  # MemryX is installed
            else:
                self.memryx_status_label.setText("Status: ❌ Not Installed (no devices found)")
                self.memryx_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {ERROR_COLOR};
                        font-size: 16px;
                        font-weight: bold;
                        padding: 8px;
                        background: #fed7d7;
                        border-radius: 4px;
                    }}
                """)
                self.install_memryx_btn.setVisible(True)
                self.update_memryx_btn.setVisible(False)
                self.log_output.append("❌ MemryX SDK not detected - installation required")
                return False  # MemryX is not installed
                
        except Exception as e:
            self.memryx_status_label.setText(f"Status: ❓ Check Failed: {str(e)}")
            self.log_output.append(f"⚠ Error checking MemryX status: {str(e)}")
            return False  # Error counts as not installed
            
    def check_docker_status(self):
        """Check Docker installation status"""
        self.log_output.append("🔍 Checking Docker installation...")
        docker_installed = False
        compose_installed = False
        docker_running = False
        
        try:
            # Check Docker
            result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                docker_installed = True
                
                # Check if Docker daemon is running
                try:
                    daemon_check = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
                    if daemon_check.returncode == 0:
                        docker_running = True
                        self.docker_status_label.setText(f"Status: ✅ {version}")
                        self.docker_status_label.setStyleSheet(f"""
                            QLabel {{
                                color: {SUCCESS_COLOR};
                                font-size: 16px;
                                font-weight: bold;
                                padding: 8px;
                                background: #c6f6d5;
                                border-radius: 4px;
                            }}
                        """)
                        self.log_output.append(f"✅ {version} (daemon running)")
                        self.start_docker_btn.setVisible(False)
                    else:
                        self.docker_status_label.setText(f"Status: ⚠️ {version} (daemon not running)")
                        self.docker_status_label.setStyleSheet(f"""
                            QLabel {{
                                color: {WARNING_COLOR};
                                font-size: 16px;
                                font-weight: bold;
                                padding: 8px;
                                background: #fef3c7;
                                border-radius: 4px;
                            }}
                        """)
                        self.log_output.append(f"⚠️ {version} installed but daemon not running")
                        self.log_output.append("💡 Click 'Start Docker Daemon' or run: sudo systemctl start docker")
                        self.start_docker_btn.setVisible(True)
                except (FileNotFoundError, subprocess.TimeoutExpired):
                    self.docker_status_label.setText(f"Status: ⚠️ {version} (daemon not running)")
                    self.docker_status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {WARNING_COLOR};
                            font-size: 16px;
                            font-weight: bold;
                            padding: 8px;
                            background: #fef3c7;
                            border-radius: 4px;
                        }}
                    """)
                    self.log_output.append(f"⚠️ {version} installed but daemon not running")
                    self.log_output.append("💡 Click 'Start Docker Daemon' or run: sudo systemctl start docker")
                    self.start_docker_btn.setVisible(True)
                
                self.install_docker_btn.setVisible(False)
            else:
                raise FileNotFoundError
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.docker_status_label.setText("Status: ❌ Docker Not Installed")
            self.docker_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {ERROR_COLOR};
                    font-size: 16px;
                    font-weight: bold;
                    padding: 8px;
                    background: #fed7d7;
                    border-radius: 4px;
                }}
            """)
            self.log_output.append("❌ Docker not installed")
            self.install_docker_btn.setVisible(True)
            
        # Check Docker Compose
        try:
            result = subprocess.run(['docker', 'compose', 'version'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.docker_compose_status_label.setText(f"Docker Compose: ✅ {version}")
                self.docker_compose_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {SUCCESS_COLOR};
                        font-size: 16px;
                        font-weight: bold;
                        padding: 8px;
                        background: #c6f6d5;
                        border-radius: 4px;
                    }}
                """)
                self.log_output.append(f"✅ {version}")
                compose_installed = True
            else:
                raise FileNotFoundError
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            self.docker_compose_status_label.setText("Docker Compose: ❌ Not Installed")
            self.docker_compose_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {ERROR_COLOR};
                    font-size: 16px;
                    font-weight: bold;
                    padding: 8px;
                    background: #fed7d7;
                    border-radius: 4px;
                }}
            """)
            self.log_output.append("❌ Docker Compose not installed")
        
        # Return True only if Docker is installed, daemon is running, AND Compose is installed
        return docker_installed and docker_running and compose_installed
            
    def install_memryx(self):
        """Install MemryX SDK"""
        reply = QMessageBox.question(
            self, "Install MemryX SDK",
            "This will install MemryX drivers and runtime on your system.\n\n"
            "The installation process will:\n"
            "• Install kernel headers and DKMS\n"
            "• Add MemryX repository and GPG key\n"
            "• Install memx-drivers (requires restart after)\n"
            "• Install memx-accl and mxa-manager runtime\n\n"
            "This requires sudo privileges and may take several minutes.\n"
            "A system restart will be required after driver installation.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        sudo_password = PasswordDialog.get_sudo_password(self, "MemryX installation")
        if sudo_password is None:
            self.log_output.append("❌ Installation cancelled - password required")
            return
            
        self.install_memryx_btn.setEnabled(False)
        self.install_memryx_btn.setText("🔄 Installing...")
        
        from frigate_launcher import MemryXInstallWorker
        self.memryx_install_worker = MemryXInstallWorker(self.script_dir, sudo_password)
        self.memryx_install_worker.progress.connect(self.log_output.append)
        self.memryx_install_worker.finished.connect(self.on_memryx_install_finished)
        self.memryx_install_worker.start()
        
    def on_memryx_install_finished(self, success):
        """Handle MemryX installation completion"""
        self.install_memryx_btn.setEnabled(True)
        self.install_memryx_btn.setText("📦 Install MemryX SDK")
        
        if success:
            self.log_output.append("🎉 MemryX installation completed!")
            QMessageBox.information(
                self, "Installation Complete",
                "✅ MemryX SDK has been installed successfully!\n\n"
                "IMPORTANT: Please restart your computer for the drivers to take effect."
            )
            self.check_memryx_status()
        else:
            self.log_output.append("❌ Installation failed. Check the log for details.")
            
    def update_memryx(self):
        """Update MemryX SDK to version 2.1 (required for Frigate compatibility)"""
        reply = QMessageBox.question(
            self, "Update MemryX SDK to 2.1",
            "This will update/install MemryX SDK to version 2.1.\n\n"
            "⚠️ IMPORTANT: Frigate only supports MemryX SDK version 2.1\n\n"
            "The update process will:\n"
            "• Update package repositories\n"
            "• Install memx-drivers=2.1.*\n"
            "• Install memx-accl=2.1.*\n"
            "• Install mxa-manager=2.1.*\n"
            "• Hold packages at version 2.1 to prevent auto-updates\n"
            "• System restart may be required if drivers are updated\n\n"
            "This requires sudo privileges and may take several minutes.\n\n"
            "Continue with MemryX SDK 2.1 update?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        sudo_password = PasswordDialog.get_sudo_password(self, "MemryX SDK update to version 2.1")
        if sudo_password is None:
            self.log_output.append("❌ MemryX SDK update cancelled - password required")
            return
        
        self.update_memryx_btn.setEnabled(False)
        self.update_memryx_btn.setText("🔄 Updating to 2.1...")
        
        # Start the MemryX update worker
        self.memryx_update_worker = MemryXUpdateWorker(self.script_dir, sudo_password)
        self.memryx_update_worker.progress.connect(self.log_output.append)
        self.memryx_update_worker.finished.connect(self.on_memryx_update_finished)
        self.memryx_update_worker.start()
    
    def on_memryx_update_finished(self, success):
        """Handle MemryX SDK update completion"""
        self.update_memryx_btn.setEnabled(True)
        self.update_memryx_btn.setText("🔄 Update MemryX SDK")
        
        if success:
            self.log_output.append("🎉 MemryX SDK updated to version 2.1!")
            
            # Check if restart is needed
            devices = [d for d in glob.glob("/dev/memx*") if "_feature" not in d]
            if len(devices) == 0:
                reply = QMessageBox.question(
                    self, "Restart Required",
                    "✅ MemryX SDK 2.1 has been installed successfully!\n\n"
                    "⚠️ No MemryX devices detected yet.\n"
                    "A system restart is required for the drivers to take effect.\n\n"
                    "Would you like to restart your system now?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.restart_system()
            else:
                QMessageBox.information(
                    self, "Update Complete",
                    "✅ MemryX SDK 2.1 is now installed and ready!\n\n"
                    f"Detected {len(devices)} MemryX device(s).\n"
                    "Packages have been held at version 2.1 for Frigate compatibility."
                )
            
            # Refresh status
            self.check_memryx_status()
        else:
            self.log_output.append("❌ MemryX SDK update failed. Check the log for details.")
            QMessageBox.warning(
                self, "Update Failed",
                "❌ Failed to update MemryX SDK to version 2.1.\n\n"
                "Please check the log output for error details."
            )
        
    def install_docker(self):
        """Install Docker"""
        reply = QMessageBox.question(
            self, "Install Docker",
            "This will install Docker CE on your system.\n\n"
            "The installation process will:\n"
            "• Update package repositories\n"
            "• Install Docker CE and related components\n"
            "• Start and enable Docker service\n"
            "• Add your user to the docker group\n\n"
            "This requires sudo privileges and may take several minutes.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        sudo_password = PasswordDialog.get_sudo_password(self, "Docker installation")
        if sudo_password is None:
            self.log_output.append("❌ Installation cancelled - password required")
            return
            
        self.install_docker_btn.setEnabled(False)
        self.install_docker_btn.setText("🔄 Installing...")
        
        from frigate_launcher import DockerInstallWorker
        self.docker_install_worker = DockerInstallWorker(self.script_dir, sudo_password)
        self.docker_install_worker.progress.connect(self.log_output.append)
        self.docker_install_worker.finished.connect(self.on_docker_install_finished)
        self.docker_install_worker.start()
        
    def on_docker_install_finished(self, success):
        """Handle Docker installation completion"""
        self.install_docker_btn.setEnabled(True)
        self.install_docker_btn.setText("🐳 Install Docker")
        
        if success:
            self.log_output.append("🎉 Docker installation completed!")
            QMessageBox.information(
                self, "Installation Complete",
                "✅ Docker has been installed successfully!\n\n"
                "Please refresh to update the status."
            )
            self.check_docker_status()
        else:
            self.log_output.append("❌ Installation failed. Check the log for details.")
    
    def start_docker_daemon(self):
        """Start the Docker daemon with proper initialization"""
        sudo_password = PasswordDialog.get_sudo_password(self, "starting Docker daemon")
        if sudo_password is None:
            self.log_output.append("❌ Operation cancelled - password required")
            return
        
        self.start_docker_btn.setEnabled(False)
        self.start_docker_btn.setText("🔄 Starting...")
        self.log_output.append("🚀 Starting Docker daemon...")
        
        try:
            import time
            
            # First, stop Docker if it's running in a bad state
            self.log_output.append("🔄 Stopping Docker service...")
            process0 = subprocess.Popen(
                ['sudo', '-S', 'systemctl', 'stop', 'docker'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            process0.communicate(input=f"{sudo_password}\n", timeout=10)
            time.sleep(1)
            
            # Also stop docker.socket
            process0b = subprocess.Popen(
                ['sudo', '-S', 'systemctl', 'stop', 'docker.socket'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            process0b.communicate(input=f"{sudo_password}\n", timeout=10)
            time.sleep(1)
            
            # Clean up Docker's runtime directory if it exists with issues
            self.log_output.append("🧹 Cleaning Docker runtime data...")
            cleanup_dirs = [
                '/var/run/docker.sock',
                '/var/run/docker',
            ]
            
            for dir_path in cleanup_dirs:
                cleanup_process = subprocess.Popen(
                    ['sudo', '-S', 'rm', '-rf', dir_path],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                cleanup_process.communicate(input=f"{sudo_password}\n", timeout=5)
            
            time.sleep(1)
            
            # Start Docker service
            self.log_output.append("▶️ Starting Docker service...")
            process = subprocess.Popen(
                ['sudo', '-S', 'systemctl', 'start', 'docker'],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate(input=f"{sudo_password}\n", timeout=15)
            
            if process.returncode == 0:
                self.log_output.append("✅ Docker daemon started successfully!")
                
                # Enable Docker to start on boot
                process2 = subprocess.Popen(
                    ['sudo', '-S', 'systemctl', 'enable', 'docker'],
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                process2.communicate(input=f"{sudo_password}\n", timeout=10)
                
                if process2.returncode == 0:
                    self.log_output.append("✅ Docker enabled to start on boot")
                
                # Wait for daemon to fully initialize
                self.log_output.append("⏳ Waiting for Docker daemon to initialize...")
                time.sleep(3)
                
                # Verify Docker is actually working
                verify_result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=5)
                if verify_result.returncode == 0:
                    self.log_output.append("✅ Docker daemon is running and responding!")
                else:
                    self.log_output.append("⚠️ Docker started but may need a moment to fully initialize")
                
                # Recheck status
                self.check_all_status()
            else:
                error_msg = stderr.strip() if stderr else "Unknown error"
                self.log_output.append(f"❌ Failed to start Docker daemon: {error_msg}")
                self.log_output.append("💡 Try restarting your computer to fix Docker issues")
                
        except subprocess.TimeoutExpired:
            self.log_output.append("❌ Starting Docker daemon timed out")
            self.log_output.append("💡 Docker may be unresponsive. Try: sudo systemctl restart docker")
        except Exception as e:
            self.log_output.append(f"❌ Error starting Docker daemon: {str(e)}")
        finally:
            self.start_docker_btn.setEnabled(True)
            self.start_docker_btn.setText("▶️ Start Docker Daemon")
        

class ModalOverlay(QWidget):
    """Semi-transparent overlay widget to dim the background when dialogs are shown"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setStyleSheet("background: rgba(0, 0, 0, 0.4);")  # Semi-transparent black
        
        # Fill the entire parent widget
        if parent:
            self.setGeometry(parent.rect())
            
    def paintEvent(self, event):
        """Custom paint event to create the overlay effect"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Fill with semi-transparent black
        painter.fillRect(self.rect(), QColor(0, 0, 0, 102))  # 40% opacity (102/255)
        
    def show_overlay(self):
        """Show the overlay and bring it to front"""
        if self.parent():
            self.setGeometry(self.parent().rect())
        self.show()
        self.raise_()
        
    def hide_overlay(self):
        """Hide the overlay"""
        self.hide()

class PasswordDialog(QDialog):
    """Secure password input dialog for sudo operations"""
    
    def __init__(self, parent=None, operation_name="system operation"):
        super().__init__(parent)
        self.operation_name = operation_name
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Administrator Password Required")
        self.setModal(True)
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Info label
        info_label = QLabel(f"Administrator privileges are required for {self.operation_name}.\n"
                           "Please enter your password to continue:")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("""
            QLabel {
                color: #2d3748;
                font-size: 14px;
                margin-bottom: 10px;
                padding: 10px;
                background: #f7fafc;
                border-radius: 6px;
                border: 1px solid #e2e8f0;
            }
        """)
        layout.addWidget(info_label)
        
        # Password input
        password_layout = QHBoxLayout()
        password_label = QLabel("Password:")
        password_label.setMinimumWidth(80)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #cbd5e0;
                border-radius: 6px;
                font-size: 14px;
                background: white;
            }
            QLineEdit:focus {
                border-color: #4299e1;
                outline: none;
            }
        """)
        self.password_input.returnPressed.connect(self.accept)
        
        password_layout.addWidget(password_label)
        password_layout.addWidget(self.password_input)
        layout.addLayout(password_layout)
        
        # Show password checkbox
        self.show_password_cb = QCheckBox("Show password")
        self.show_password_cb.toggled.connect(self.toggle_password_visibility)
        self.show_password_cb.setStyleSheet("""
            QCheckBox {
                font-size: 14px;
                color: #4a5568;
                margin: 5px 0;
            }
        """)
        layout.addWidget(self.show_password_cb)
        
        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
                min-width: 80px;
            }
            QPushButton[text="OK"] {
                background: #3182ce;
                color: white;
                border: none;
            }
            QPushButton[text="OK"]:hover {
                background: #2c5aa0;
            }
            QPushButton[text="Cancel"] {
                background: #e2e8f0;
                color: #4a5568;
                border: 1px solid #cbd5e0;
            }
            QPushButton[text="Cancel"]:hover {
                background: #cbd5e0;
            }
        """)
        layout.addWidget(button_box)
        
        # Focus on password input
        self.password_input.setFocus()
        
    def toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def get_password(self):
        """Get the entered password"""
        return self.password_input.text()
    
    @staticmethod
    def get_sudo_password(parent=None, operation_name="system operation"):
        """Static method to get sudo password from user"""
        dialog = PasswordDialog(parent, operation_name)
        
        # Use overlay if parent has the capability
        if parent and hasattr(parent, 'show_dialog'):
            result = parent.show_dialog(dialog)
        else:
            result = dialog.exec()
            
        if result == QDialog.Accepted:
            return dialog.get_password()
        return None

class SystemPrereqInstallWorker(QThread):
    """Background worker for system prerequisite installations"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, script_dir, install_type, sudo_password=None):
        super().__init__()
        self.script_dir = script_dir
        self.install_type = install_type  # 'git', 'build-tools'
        self.sudo_password = sudo_password
    
    def run(self):
        try:
            # Helper function to run sudo commands with password
            def run_sudo_command(cmd, input_text=None):
                if self.sudo_password:
                    # Use sudo -S to read password from stdin
                    sudo_cmd = ['sudo', '-S'] + cmd[1:]  # Remove 'sudo' from original cmd
                    password_input = f"{self.sudo_password}\n"
                    if input_text:
                        password_input += input_text
                    return subprocess.run(sudo_cmd, input=password_input, text=True, check=True, capture_output=True)
                else:
                    # Fallback to normal sudo (will work if terminal=true)
                    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=True)
            
            if self.install_type == 'git':
                self._install_git(run_sudo_command)
            elif self.install_type == 'build-tools':
                self._install_build_tools(run_sudo_command)
            
            self.finished.emit(True)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Command failed: {e.cmd}"
            if e.stderr:
                error_msg += f"\n   Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}"
            self.progress.emit(error_msg)
            self.finished.emit(False)
            
        except Exception as e:
            self.progress.emit(f"❌ Installation error: {str(e)}")
            self.finished.emit(False)
    
    def _install_git(self, run_sudo_command):
        self.progress.emit("📦 Starting Git installation...")
        
        # Update package repositories
        self.progress.emit("🔄 Updating package repositories...")
        run_sudo_command(['sudo', 'apt', 'update'])
        
        # Install git
        self.progress.emit("📥 Installing Git...")
        run_sudo_command(['sudo', 'apt', 'install', '-y', 'git'])
        
        # Verify installation
        result = subprocess.run(['git', '--version'], capture_output=True, text=True, check=True)
        version = result.stdout.strip()
        self.progress.emit(f"✅ Git installed successfully: {version}")
    
    def _install_build_tools(self, run_sudo_command):
        self.progress.emit("🔧 Starting build tools installation...")
        
        # Update package repositories
        self.progress.emit("🔄 Updating package repositories...")
        run_sudo_command(['sudo', 'apt', 'update'])
        
        # Install essential build tools
        self.progress.emit("📥 Installing build essential packages...")
        run_sudo_command(['sudo', 'apt', 'install', '-y', 
                       'build-essential', 'cmake', 'pkg-config', 'curl', 'wget'])
        
        # Verify installation
        gcc_result = subprocess.run(['gcc', '--version'], capture_output=True, text=True, check=True)
        gcc_version = gcc_result.stdout.split('\n')[0]
        self.progress.emit(f"✅ GCC installed: {gcc_version}")
        
        make_result = subprocess.run(['make', '--version'], capture_output=True, text=True, check=True)
        make_version = make_result.stdout.split('\n')[0]
        self.progress.emit(f"✅ Make installed: {make_version}")
        
        cmake_result = subprocess.run(['cmake', '--version'], capture_output=True, text=True, check=True)
        cmake_version = cmake_result.stdout.split('\n')[0]
        self.progress.emit(f"✅ CMake installed: {cmake_version}")

class InstallWorker(QThread):
    """Background worker for installation tasks"""
    progress = Signal(str)  # Progress message
    finished = Signal(bool)  # Success/failure
    
    def __init__(self, script_dir, action_type='skip_frigate'):
        super().__init__()
        self.script_dir = script_dir
        self.action_type = action_type  # 'clone_only', 'update_only', 'skip_frigate'
        
    def run(self):
        try:
            # Check dependencies
            self.progress.emit("🔍 Checking system dependencies...")
            self._check_dependencies()
            
            # Setup Python environment
            self.progress.emit("🐍 Setting up Python virtual environment...")
            self._setup_python_env()
            
            # Handle Frigate repository based on action type
            if self.action_type == 'clone_only':
                self.progress.emit("📥 Cloning fresh Frigate repository...")
                self._clone_frigate()
            elif self.action_type == 'update_only':
                self.progress.emit("🔄 Updating existing Frigate repository...")
                self._update_frigate()
            elif self.action_type == 'skip_frigate':
                self.progress.emit("⏭️ Skipping Frigate repository setup...")
            
            self.progress.emit("✅ Setup completed successfully!")
            self.finished.emit(True)
            
        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.progress.emit(error_msg)
            self.progress.emit("💡 Tip: Check the troubleshooting section in README.md")
            self.finished.emit(False)
    
    def _check_dependencies(self):
        # Check for required tools
        required = ['git', 'python3']
        for tool in required:
            result = subprocess.run(['which', tool], capture_output=True)
            if result.returncode != 0:
                raise Exception(f"{tool} is not installed. Please install it first.")
        
        # Special check for Docker with better verification
        docker_check = subprocess.run(['which', 'docker'], capture_output=True)
        if docker_check.returncode != 0:
            raise Exception("docker is not installed. Please install it first.")
        
        # Verify Docker is actually working
        try:
            version_check = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
            if version_check.returncode != 0:
                raise Exception("Docker binary found but not working properly.")
        except subprocess.TimeoutExpired:
            raise Exception("Docker command timed out - Docker may not be properly installed.")
        except FileNotFoundError:
            raise Exception("Docker binary not found in PATH.")
        
        # Check if Docker service is running
        try:
            service_check = subprocess.run(['systemctl', 'is-active', 'docker'], 
                                         capture_output=True, text=True, timeout=5)
            if service_check.stdout.strip() != 'active':
                raise Exception("Docker service is not running. Please start it with: sudo systemctl start docker")
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            # If we can't check systemctl, try a simple docker command
            try:
                subprocess.run(['docker', 'info'], capture_output=True, timeout=5, check=True)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                raise Exception("Docker is installed but not accessible. You may need to add your user to the docker group or start the Docker service.")
        
        time.sleep(1)  # Simulate work
    
    def _setup_python_env(self):
        """Set up Python environment - skip if already properly configured"""
        venv_path = os.path.join(self.script_dir, '.venv')
        pip_path = os.path.join(venv_path, 'bin', 'pip')
        
        # Check if environment already exists and is functional
        if os.path.exists(venv_path) and os.path.exists(pip_path):
            try:
                # Test if pip works
                result = subprocess.run([pip_path, '--version'], capture_output=True, timeout=10)
                if result.returncode == 0:
                    # Check if required packages are already installed
                    try:
                        result = subprocess.run([pip_path, 'show', 'PySide6', 'pyyaml'], 
                                              capture_output=True, timeout=10)
                        if result.returncode == 0:
                            self.progress.emit("✅ Python environment already configured and ready!")
                            return
                    except:
                        pass
            except:
                pass
        
        # Environment needs setup
        self.progress.emit("🏗️ Creating/updating Python virtual environment...")
        
        # Remove corrupted venv if exists
        if os.path.exists(venv_path):
            self.progress.emit("🗑️ Removing existing virtual environment...")
            import shutil
            shutil.rmtree(venv_path)
        
        # Create new venv
        self.progress.emit("🐍 Creating virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv', venv_path], check=True)
        
        # Install/upgrade requirements
        self.progress.emit("📦 Installing Python packages...")
        subprocess.run([pip_path, 'install', '--upgrade', 'pip'], check=True)
        subprocess.run([pip_path, 'install', 'PySide6', 'pyyaml'], check=True)
        
        self.progress.emit("✅ Python environment setup completed!")
    
    def _setup_frigate(self):
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if os.path.exists(frigate_path):
            # Check if it's a valid git repository
            try:
                # Check if .git directory exists
                git_dir = os.path.join(frigate_path, '.git')
                if not os.path.exists(git_dir):
                    self.progress.emit("⚠️ Frigate directory exists but is not a git repo, removing...")
                    import shutil
                    shutil.rmtree(frigate_path)
                    raise FileNotFoundError("Not a git repository")
                
                # Try to update existing repo
                self.progress.emit("🔄 Updating existing Frigate repository...")
                result = subprocess.run(['git', 'status'], cwd=frigate_path, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Repository is valid, try to fetch and pull
                    try:
                        # First fetch all remote changes
                        subprocess.run(['git', 'fetch', 'origin'], cwd=frigate_path, check=True)
                        
                        # Check current branch
                        branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                                     cwd=frigate_path, capture_output=True, text=True, check=True)
                        current_branch = branch_result.stdout.strip()
                        
                        if current_branch:
                            # Try to pull from the current branch
                            try:
                                subprocess.run(['git', 'pull', 'origin', current_branch], cwd=frigate_path, check=True)
                                self.progress.emit(f"✅ Frigate repository updated successfully! (branch: {current_branch})")
                            except subprocess.CalledProcessError:
                                # If pull fails, just use what we have
                                self.progress.emit(f"⚠️ Could not update branch {current_branch}, using existing version")
                        else:
                            self.progress.emit("⚠️ Repository in detached HEAD state, using existing version")
                    except subprocess.CalledProcessError as e:
                        self.progress.emit(f"⚠️ Could not update repository: {str(e)}, using existing version")
                else:
                    # Repository is corrupted, remove and re-clone
                    raise Exception("Repository is corrupted")
                    
            except (subprocess.CalledProcessError, Exception) as e:
                self.progress.emit(f"⚠️ Repository update failed: {str(e)}")
                self.progress.emit("🗑️ Removing corrupted repository...")
                import shutil
                shutil.rmtree(frigate_path)
                # Fall through to clone new repo
        
        # Clone new repo if directory doesn't exist or was removed
        if not os.path.exists(frigate_path):
            self.progress.emit("📥 Cloning Frigate repository...")
            try:
                subprocess.run([
                    'git', 'clone', 
                    'https://github.com/blakeblackshear/frigate.git',
                    frigate_path
                ], cwd=self.script_dir, check=True)
                self.progress.emit("✅ Frigate repository cloned successfully!")
            except subprocess.CalledProcessError as e:
                raise Exception(f"Failed to clone Frigate repository: {str(e)}")
        
    def _clone_frigate(self):
        """Clone a fresh Frigate repository, removing existing if present"""
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        # Remove existing directory if present
        if os.path.exists(frigate_path):
            self.progress.emit("🗑️ Removing existing Frigate directory...")
            import shutil
            shutil.rmtree(frigate_path)
        
        # Clone fresh repository
        self.progress.emit("📥 Cloning Frigate repository...")
        try:
            subprocess.run([
                'git', 'clone', 
                'https://github.com/blakeblackshear/frigate.git',
                frigate_path
            ], cwd=self.script_dir, check=True)
            self.progress.emit("✅ Frigate repository cloned successfully!")
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to clone Frigate repository: {str(e)}")
        
        self._setup_config_directory(frigate_path)
        self._create_default_config(frigate_path)
    
    def _update_frigate(self):
        """Update existing Frigate repository"""
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if not os.path.exists(frigate_path):
            raise Exception("Frigate repository not found. Please use 'Clone Fresh' option instead.")
        
        # Check if it's a valid git repository
        git_dir = os.path.join(frigate_path, '.git')
        if not os.path.exists(git_dir):
            raise Exception("Frigate directory exists but is not a git repository. Please use 'Clone Fresh' option.")
        
        try:
            # Check repository status
            result = subprocess.run(['git', 'status'], cwd=frigate_path, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception("Git repository is corrupted. Please use 'Clone Fresh' option.")
            
            # Check for local changes
            status_output = result.stdout
            if "Changes not staged" in status_output or "Changes to be committed" in status_output:
                self.progress.emit("⚠️ Local changes detected in repository")
                # Stash changes
                self.progress.emit("💾 Stashing local changes...")
                subprocess.run(['git', 'stash'], cwd=frigate_path, check=True)
            
            # Fetch latest changes
            self.progress.emit("📡 Fetching latest changes...")
            subprocess.run(['git', 'fetch', 'origin'], cwd=frigate_path, check=True)
            
            # Get current branch
            branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                         cwd=frigate_path, capture_output=True, text=True, check=True)
            current_branch = branch_result.stdout.strip()
            
            if current_branch:
                # Pull latest changes
                self.progress.emit(f"⬇️ Pulling latest changes for branch: {current_branch}")
                subprocess.run(['git', 'pull', 'origin', current_branch], cwd=frigate_path, check=True)
                self.progress.emit(f"✅ Repository updated successfully! (branch: {current_branch})")
            else:
                self.progress.emit("⚠️ Repository in detached HEAD state, fetched latest changes")
                
        except subprocess.CalledProcessError as e:
            raise Exception(f"Failed to update repository: {str(e)}")
        
        self._setup_config_directory(frigate_path)
    
    def _setup_config_directory(self, frigate_path):
        """Ensure config directory exists and create version.py"""
        config_dir = os.path.join(frigate_path, 'config')
        if not os.path.exists(config_dir):
            os.makedirs(config_dir, exist_ok=True)
            self.progress.emit("📁 Created config directory")
        
        # Create version.py file in frigate/frigate/version.py
        version_dir = os.path.join(frigate_path, 'frigate')
        version_file_path = os.path.join(version_dir, 'version.py')
        
        # Ensure frigate subdirectory exists
        if not os.path.exists(version_dir):
            os.makedirs(version_dir, exist_ok=True)
            self.progress.emit("📁 Created frigate subdirectory")
        
        try:
            # Create version.py with the specific version
            version_content = 'VERSION = "0.16.0-2458f667"\n'
            
            with open(version_file_path, 'w') as f:
                f.write(version_content)
            
            self.progress.emit("📝 Created version.py with version: 0.16.0-2458f667")
            
        except Exception as e:
            self.progress.emit(f"⚠️ Could not create version.py: {str(e)}")

    def _create_default_config(self, frigate_path):
        """Create default config.yaml file with template content"""
        config_dir = os.path.join(frigate_path, 'config')
        config_file_path = os.path.join(config_dir, 'config.yaml')
        
        # Check if config.yaml already exists
        if os.path.exists(config_file_path):
            self.progress.emit("ℹ️ Config file already exists, skipping creation")
            return
        
        # Default configuration content (same as in load_config_preview)
        default_config = """# Frigate Configuration
# This is a basic template. Customize it for your cameras and setup.

mqtt:
enabled: False

detectors:
  memx0:
    type: memryx
    device: PCIe:0

model:
model_type: yolo-generic
width: 320
height: 320
input_tensor: nchw
input_dtype: float
labelmap_path: /labelmap/coco-80.txt

# cameras:
# Add your cameras here
# example_camera:
#   ffmpeg:
#     inputs:
#       - path: rtsp://username:password@camera_ip:554/stream
#         roles:
#           - detect
#   detect:
#     width: 2560
#     height: 1440

cameras:
cam1:
    ffmpeg:
    inputs:
        - path: 
            rtsp://username:password@camera_ip:554/stream
        roles:
            - detect
    detect:
    width: 2560
    height: 1440
    fps: 5
    enabled: true

    objects:
    track:
        - person
        - car
        - bottle
        - cup

    snapshots:
    enabled: false
    bounding_box: true
    retain:
        default: 0  # Keep snapshots for 'n' days
    record:
    enabled: false
    alerts:
        retain:
        days: 0
    detections:
        retain:
        days: 0

version: 0.17-0

# For more configuration options, visit:
# https://docs.frigate.video/configuration/
"""
        
        try:
            # Create the config file
            with open(config_file_path, 'w', encoding='utf-8') as f:
                f.write(default_config)
            
            self.progress.emit("📝 Created default config.yaml file")
            self.progress.emit(f"   📁 Location: {config_file_path}")
            
            # Signal to main thread to update config_file_mtime to prevent popup
            self.progress.emit("UPDATE_CONFIG_MTIME")
            
        except Exception as e:
            self.progress.emit(f"⚠️ Could not create default config.yaml: {str(e)}")

class DockerWorker(QThread):
    """Background worker for Docker operations"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, script_dir, action='start'):
        super().__init__()
        self.script_dir = script_dir
        self.action = action
        self._terminated = False  # Track termination state
        self._process = None  # Track current subprocess
    
    def stop(self):
        """Stop the current operation gracefully"""
        self._terminated = True
        if self._process and self._process.poll() is None:  # Process is still running
            try:
                self._process.terminate()  # Send SIGTERM
                self._process.wait(timeout=5)  # Wait up to 5 seconds
            except subprocess.TimeoutExpired:
                self._process.kill()  # Force kill if it doesn't stop
                self._process.wait()
            except Exception:
                pass
    
    def terminate(self):
        """Override terminate to set our flag"""
        self.stop()  # Use our stop method
        super().terminate()
    
    def run(self):
        try:
            if self._terminated:
                return
                
            if self.action == 'build':
                self._build_image()
            elif self.action == 'start':
                self._start_frigate()
            elif self.action == 'stop':
                self._stop_frigate()
            elif self.action == 'restart':
                self._restart_frigate()
            elif self.action == 'remove':
                self._remove_frigate()
                
            if not self._terminated:
                self.finished.emit(True)
        except Exception as e:
            if not self._terminated:
                self.progress.emit(f"❌ Error: {str(e)}")
                self.finished.emit(False)
    
    def _run_docker_command(self, cmd, description, cwd=None, capture_output=True):
        """Run a docker command and emit its output line by line"""
        if self._terminated:
            return
            
        self.progress.emit(f"{description}")
        
        try:
            if capture_output:
                # For commands that produce lots of output (like build)
                self._process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=cwd,
                    bufsize=1,
                    universal_newlines=True
                )
                
                # Read output line by line and emit it
                for line in self._process.stdout:
                    if self._terminated:
                        self._process.terminate()
                        break
                    line = line.strip()
                    if line:  # Only emit non-empty lines
                        self.progress.emit(line)
                
                # Wait for process to complete
                self._process.wait()
                
                if not self._terminated and self._process.returncode != 0:
                    raise subprocess.CalledProcessError(self._process.returncode, cmd)
                    
            else:
                # For simple commands that don't produce much output
                self._process = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True)
                result = self._process
                if result.stdout.strip():
                    for line in result.stdout.strip().split('\n'):
                        if line.strip():
                            self.progress.emit(line.strip())
                if result.stderr.strip():
                    for line in result.stderr.strip().split('\n'):
                        if line.strip():
                            self.progress.emit(f"⚠️ {line.strip()}")
                            
        except subprocess.CalledProcessError as e:
            self.progress.emit(f"❌ Command failed: {' '.join(cmd)}")
            if e.stdout:
                self.progress.emit(f"Output: {e.stdout}")
            if e.stderr:
                self.progress.emit(f"Error: {e.stderr}")
            raise
    
    def _check_container_exists(self):
        """Check if Frigate container exists"""
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=frigate', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True)
            return 'frigate' in result.stdout
        except:
            return False
    
    def _check_container_running(self):
        """Check if Frigate container is running"""
        try:
            result = subprocess.run(['docker', 'ps', '--filter', 'name=frigate', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True)
            return 'frigate' in result.stdout
        except:
            return False
    
    def _build_image(self):
        """Build the Frigate Docker image only (doesn't start container)"""
        self.progress.emit("🔨 Building Frigate Docker image...")
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if not os.path.exists(frigate_path):
            raise Exception("Frigate repository not found. Please clone it first in Section 2.")
        
        self._run_docker_command([
            'docker', 'build', '-t', 'frigate', 
            '-f', 'docker/main/Dockerfile', '.'
        ], "Building Docker image:", cwd=frigate_path, capture_output=True)
        
        self.progress.emit("")  # Empty line for separation
        self.progress.emit("✅ Frigate Docker image built successfully!")
        self.progress.emit("💡 You can now start the container using the Start button")
    
    def _start_frigate(self):
        """Start Frigate container (create if doesn't exist, just start if stopped)"""
        if self._check_container_exists():
            if self._check_container_running():
                self.progress.emit("ℹ️ Frigate container is already running")
                return
            else:
                self.progress.emit("▶️ Starting existing Frigate container...")
                self._run_docker_command(['docker', 'start', 'frigate'], "Starting container:", capture_output=False)
                self.progress.emit("✅ Frigate started successfully!")
                return
        
        # Container doesn't exist, need to create it
        self.progress.emit("🚀 Creating and starting new Frigate container...")
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if not os.path.exists(frigate_path):
            raise Exception("Frigate repository not found. Please clone it first in Section 2.")
        
        # Create and start new container
        self._run_docker_command([
            'docker', 'run', '-d',
            '--name', 'frigate',
            '--restart=unless-stopped',
            '--mount', 'type=tmpfs,target=/tmp/cache,tmpfs-size=1000000000',
            '--shm-size=256m',
            '-v', f"{frigate_path}/config:/config",
            '-v', '/run/mxa_manager:/run/mxa_manager',
            '-e', 'FRIGATE_RTSP_PASSWORD=password',
            '--privileged=true',
            '-p', '8971:8971',
            '-p', '8554:8554', 
            '-p', '5000:5000',
            '-p', '8555:8555/tcp',
            '-p', '8555:8555/udp',
            '--device', '/dev/memx0',
            'frigate'
        ], "Creating container:", capture_output=False)
        
        self.progress.emit("")  # Empty line for separation
        self.progress.emit("✅ Frigate started successfully!")
        self.progress.emit("🌐 Access Frigate UI at: http://localhost:5000")
    
    def _stop_frigate(self):
        """Stop Frigate container (but keep it for later restart)"""
        if not self._check_container_exists():
            self.progress.emit("ℹ️ Frigate container doesn't exist - nothing to stop")
            return
            
        if not self._check_container_running():
            self.progress.emit("ℹ️ Frigate container is already stopped")
            return
            
        self.progress.emit("⏹️ Stopping Frigate container...")
        self._run_docker_command(['docker', 'stop', 'frigate'], "Stopping container:", capture_output=False)
        self.progress.emit("✅ Frigate stopped successfully!")
    
    def _restart_frigate(self):
        """Restart Frigate container (stop then start)"""
        if not self._check_container_exists():
            self.progress.emit("❌ Cannot restart: Frigate container doesn't exist")
            self.progress.emit("💡 Use 'Start' to create and start a new container")
            raise Exception("Container doesn't exist - cannot restart")
            
        self.progress.emit("🔄 Restarting Frigate container...")
        
        # Stop if running
        if self._check_container_running():
            self._run_docker_command(['docker', 'stop', 'frigate'], "Stopping container:", capture_output=False)
        
        # Start the container
        self._run_docker_command(['docker', 'start', 'frigate'], "Starting container:", capture_output=False)
            
        self.progress.emit("✅ Frigate restarted successfully!")
    
    def _remove_frigate(self):
        """Stop and remove Frigate container completely"""
        if not self._check_container_exists():
            self.progress.emit("ℹ️ Frigate container doesn't exist")
            return
            
        self.progress.emit("🗑️ Stopping and removing Frigate container...")
        
        # Stop if running
        if self._check_container_running():
            self._run_docker_command(['docker', 'stop', 'frigate'], "Stopping container:", capture_output=False)
        
        # Remove container
        self._run_docker_command(['docker', 'rm', 'frigate'], "Removing container:", capture_output=False)
        self.progress.emit("✅ Frigate container removed successfully!")

class DockerInstallWorker(QThread):
    """Background worker for Docker installation"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, script_dir, sudo_password=None):
        super().__init__()
        self.script_dir = script_dir
        self.sudo_password = sudo_password
    
    def run(self):
        try:
            self.progress.emit("🐳 Starting Docker installation process...")
            
            # Helper function to run sudo commands with password
            def run_sudo_command(cmd, input_text=None):
                if self.sudo_password:
                    # Use sudo -S to read password from stdin
                    sudo_cmd = ['sudo', '-S'] + cmd[1:]  # Remove 'sudo' from original cmd
                    if input_text:
                        # For commands that need input, we can't mix password and content
                        # This should only be used for commands that don't need input
                        raise ValueError("Use write_sudo_file for commands that need file input")
                    return subprocess.run(sudo_cmd, input=f"{self.sudo_password}\n", text=True, check=True, capture_output=True)
                else:
                    # Fallback to normal sudo (will work if terminal=true)
                    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=True)
            
            # Helper function to write files with sudo
            def write_sudo_file(file_path, content):
                if self.sudo_password:
                    # Write to temp file first, then move with sudo
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Move temp file to target location with sudo
                        sudo_cmd = ['sudo', '-S', 'mv', temp_file_path, file_path]
                        subprocess.run(sudo_cmd, input=f"{self.sudo_password}\n", text=True, check=True, capture_output=True)
                    finally:
                        # Clean up temp file if it still exists
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                else:
                    # Fallback to normal write (won't work for protected paths)
                    with open(file_path, 'w') as f:
                        f.write(content)
            
            # Step 0: Clean up any existing Docker repository files (in case of previous failed attempts)
            self.progress.emit("🧹 Cleaning up any existing Docker repository files...")
            try:
                run_sudo_command(['sudo', 'rm', '-f', '/etc/apt/sources.list.d/docker.list'])
                run_sudo_command(['sudo', 'rm', '-f', '/etc/apt/keyrings/docker.asc'])
            except subprocess.CalledProcessError:
                pass  # Files may not exist, continue
            
            # Step 1: Update package repositories
            self.progress.emit("📦 Updating package repositories...")
            run_sudo_command(['sudo', 'apt-get', 'update'])
            
            # Step 2: Install prerequisites
            self.progress.emit("🔧 Installing prerequisites...")
            run_sudo_command([
                'sudo', 'apt-get', 'install', '-y',
                'ca-certificates', 'curl'
            ])
            
            # Step 3: Create keyrings directory
            self.progress.emit("🔑 Setting up Docker GPG keyring...")
            run_sudo_command([
                'sudo', 'install', '-m', '0755', '-d', '/etc/apt/keyrings'
            ])
            
            # Step 4: Download Docker GPG key
            run_sudo_command([
                'sudo', 'curl', '-fsSL', 
                'https://download.docker.com/linux/ubuntu/gpg',
                '-o', '/etc/apt/keyrings/docker.asc'
            ])
            
            # Step 5: Set permissions on GPG key
            run_sudo_command([
                'sudo', 'chmod', 'a+r', '/etc/apt/keyrings/docker.asc'
            ])
            
            # Step 6: Add Docker repository
            self.progress.emit("📋 Adding Docker repository...")
            
            # Get architecture and version codename
            arch_result = subprocess.run(['dpkg', '--print-architecture'], 
                                       capture_output=True, text=True, check=True)
            architecture = arch_result.stdout.strip()
            
            # Get Ubuntu version codename
            with open('/etc/os-release', 'r') as f:
                os_release = f.read()
            
            version_codename = None
            for line in os_release.split('\n'):
                if line.startswith('VERSION_CODENAME='):
                    version_codename = line.split('=')[1].strip('"')
                    break
            
            if not version_codename:
                raise Exception("Could not determine Ubuntu version codename")
            
            # Create repository entry
            repo_entry = (
                f"deb [arch={architecture} signed-by=/etc/apt/keyrings/docker.asc] "
                f"https://download.docker.com/linux/ubuntu {version_codename} stable\n"
            )
            
            # Add repository to sources list
            self.progress.emit("📋 Adding Docker repository...")
            write_sudo_file('/etc/apt/sources.list.d/docker.list', repo_entry)
            
            # Verify the repository was written correctly
            try:
                verify_result = subprocess.run(['cat', '/etc/apt/sources.list.d/docker.list'], 
                                             capture_output=True, text=True, check=True)
                self.progress.emit(f"✅ Repository added: {verify_result.stdout.strip()}")
            except subprocess.CalledProcessError:
                self.progress.emit("⚠️  Could not verify repository file, continuing...")
            
            # Step 7: Update package repositories again
            self.progress.emit("🔄 Updating package repositories with Docker repo...")
            run_sudo_command(['sudo', 'apt-get', 'update'])
            
            # Step 8: Install Docker (with specific versions to ensure compatibility)
            self.progress.emit("🐳 Installing Docker CE and components...")
            
            # First, check available versions
            self.progress.emit("🔍 Checking available Docker versions...")
            
            # Install Docker packages
            run_sudo_command([
                'sudo', 'apt-get', 'install', '-y',
                'docker-ce', 'docker-ce-cli', 'containerd.io',
                'docker-buildx-plugin', 'docker-compose-plugin'
            ])
            
            # Verify buildx is properly installed
            self.progress.emit("🔍 Verifying Docker Buildx installation...")
            try:
                buildx_result = subprocess.run(['docker', 'buildx', 'version'], 
                                             capture_output=True, text=True, timeout=5)
                if buildx_result.returncode == 0:
                    self.progress.emit(f"✅ Docker Buildx installed: {buildx_result.stdout.strip()}")
                else:
                    self.progress.emit("⚠️  Docker Buildx not responding properly")
            except Exception as e:
                self.progress.emit(f"⚠️  Could not verify Buildx: {str(e)}")
            
            # Step 9: Configure containerd (required for building images)
            self.progress.emit("⚙️  Configuring containerd for image building...")
            try:
                # Ensure containerd is running
                run_sudo_command(['sudo', 'systemctl', 'restart', 'containerd'])
                run_sudo_command(['sudo', 'systemctl', 'enable', 'containerd'])
                self.progress.emit("✅ Containerd configured and running")
            except subprocess.CalledProcessError as e:
                self.progress.emit(f"⚠️  Containerd configuration issue: {str(e)}")
            
            # Step 10: Start and enable Docker service
            self.progress.emit("🚀 Starting Docker service...")
            run_sudo_command(['sudo', 'systemctl', 'start', 'docker'])
            run_sudo_command(['sudo', 'systemctl', 'enable', 'docker'])
            
            # Wait for Docker daemon to be fully ready
            self.progress.emit("⏳ Waiting for Docker daemon to initialize...")
            import time
            time.sleep(3)
            
            # Step 11: Initialize Docker Buildx (required for modern builds)
            self.progress.emit("🔧 Initializing Docker Buildx builder...")
            try:
                # Create and use a new builder instance with all platforms
                run_sudo_command(['sudo', 'docker', 'buildx', 'create', '--name', 'mybuilder', '--use', '--bootstrap'])
                self.progress.emit("✅ Docker Buildx builder initialized")
            except subprocess.CalledProcessError as e:
                # Builder might already exist
                self.progress.emit("ℹ️  Buildx builder already exists or initialization skipped")
                try:
                    # Try to use existing default builder
                    run_sudo_command(['sudo', 'docker', 'buildx', 'use', 'default'])
                except:
                    pass
            
            # Step 12: Create docker group and add user
            self.progress.emit("👥 Configuring user permissions...")
            
            # Create docker group (may already exist)
            try:
                run_sudo_command(['sudo', 'groupadd', 'docker'])
            except subprocess.CalledProcessError:
                # Group may already exist, continue
                pass
            
            # Add current user to docker group
            import getpass
            current_user = getpass.getuser()
            run_sudo_command(['sudo', 'usermod', '-aG', 'docker', current_user])
            
            # Step 13: Verify Docker installation and build capability
            self.progress.emit("🔍 Verifying Docker installation...")
            
            # Check if docker binary exists and is executable
            try:
                docker_version_result = subprocess.run(['docker', '--version'], 
                                                     capture_output=True, text=True, check=True)
                self.progress.emit(f"✅ Docker binary working: {docker_version_result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError) as e:
                self.progress.emit("❌ Docker binary not found or not working!")
                self.progress.emit("🔄 Attempting to reinstall Docker CLI...")
                try:
                    run_sudo_command(['sudo', 'apt-get', 'reinstall', '-y', 'docker-ce-cli'])
                    # Try again
                    docker_version_result = subprocess.run(['docker', '--version'], 
                                                         capture_output=True, text=True, check=True)
                    self.progress.emit(f"✅ Docker binary working after reinstall: {docker_version_result.stdout.strip()}")
                except Exception as reinstall_error:
                    self.progress.emit(f"❌ Failed to fix Docker CLI: {str(reinstall_error)}")
                    self.finished.emit(False)
                    return
            
            # Check Docker Compose
            try:
                compose_result = subprocess.run(['docker', 'compose', 'version'], 
                                              capture_output=True, text=True, check=True)
                self.progress.emit(f"✅ Docker Compose working: {compose_result.stdout.strip()}")
            except Exception as e:
                self.progress.emit(f"⚠️  Docker Compose verification failed: {str(e)}")
            
            # Check if Docker service is running
            try:
                service_result = subprocess.run(['systemctl', 'is-active', 'docker'], 
                                              capture_output=True, text=True, check=True)
                if service_result.stdout.strip() == 'active':
                    self.progress.emit("✅ Docker service is running")
                else:
                    self.progress.emit("⚠️  Docker service not active, starting it...")
                    run_sudo_command(['sudo', 'systemctl', 'start', 'docker'])
            except subprocess.CalledProcessError:
                self.progress.emit("⚠️  Could not check Docker service status")
            
            # Check containerd service
            try:
                containerd_result = subprocess.run(['systemctl', 'is-active', 'containerd'], 
                                                  capture_output=True, text=True, check=True)
                if containerd_result.stdout.strip() == 'active':
                    self.progress.emit("✅ Containerd service is running")
            except:
                self.progress.emit("⚠️  Containerd service status unknown")
            
            # Test Docker with a simple command (as root since user may not be in group yet)
            try:
                test_result = run_sudo_command(['sudo', 'docker', 'run', '--rm', 'hello-world'])
                self.progress.emit("✅ Docker test successful - container can run!")
            except subprocess.CalledProcessError as e:
                self.progress.emit("⚠️  Docker test failed - may need logout/login for group permissions")
                self.progress.emit(f"   Error: {e.stderr if e.stderr else str(e)}")
            
            # Test Docker build capability
            self.progress.emit("🔍 Testing Docker build capability...")
            try:
                # Create a minimal Dockerfile for testing
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    dockerfile_path = os.path.join(tmpdir, 'Dockerfile')
                    with open(dockerfile_path, 'w') as f:
                        f.write('FROM alpine:latest\nRUN echo "Build test successful"')
                    
                    # Try to build the test image
                    build_result = subprocess.run(
                        ['sudo', 'docker', 'build', '-t', 'test-build', tmpdir],
                        capture_output=True, text=True, timeout=60
                    )
                    
                    if build_result.returncode == 0:
                        self.progress.emit("✅ Docker build test successful!")
                        # Clean up test image
                        subprocess.run(['sudo', 'docker', 'rmi', 'test-build'], 
                                     capture_output=True, timeout=30)
                    else:
                        self.progress.emit("⚠️  Docker build test failed:")
                        self.progress.emit(f"   {build_result.stderr}")
            except Exception as e:
                self.progress.emit(f"⚠️  Could not test Docker build: {str(e)}")
            
            self.progress.emit("✅ Docker installation completed successfully!")
            self.progress.emit("ℹ️  IMPORTANT: Please log out and log back in for group permissions to take effect.")
            self.progress.emit("ℹ️  After logout/login, you can use Docker without 'sudo'.")
            
            self.finished.emit(True)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Command failed: {e.cmd}"
            if e.stderr:
                error_msg += f"\n   Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}"
            self.progress.emit(error_msg)
            self.finished.emit(False)
            
        except Exception as e:
            self.progress.emit(f"❌ Installation error: {str(e)}")
            self.finished.emit(False)

class MemryXInstallWorker(QThread):
    """Background worker for MemryX driver installation"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, script_dir, sudo_password=None):
        super().__init__()
        self.script_dir = script_dir
        self.sudo_password = sudo_password
    
    def run(self):
        try:
            # Helper function to run sudo commands with password
            def run_sudo_command(cmd, input_text=None, **kwargs):
                if self.sudo_password:
                    # Use sudo -S to read password from stdin
                    sudo_cmd = ['sudo', '-S'] + cmd[1:]  # Remove 'sudo' from original cmd
                    if input_text:
                        # For commands that need input, we can't mix password and content
                        raise ValueError("Use write_sudo_file for commands that need file input")
                    return subprocess.run(sudo_cmd, input=f"{self.sudo_password}\n", text=True, check=True, capture_output=True, **kwargs)
                else:
                    # Fallback to normal sudo (will work if terminal=true)
                    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=True, **kwargs)
            
            # Helper function to write files with sudo
            def write_sudo_file(file_path, content):
                if self.sudo_password:
                    # Write to temp file first, then move with sudo
                    import tempfile
                    with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_file:
                        temp_file.write(content)
                        temp_file_path = temp_file.name
                    
                    try:
                        # Move temp file to target location with sudo
                        sudo_cmd = ['sudo', '-S', 'mv', temp_file_path, file_path]
                        subprocess.run(sudo_cmd, input=f"{self.sudo_password}\n", text=True, check=True, capture_output=True)
                    finally:
                        # Clean up temp file if it still exists
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
                else:
                    # Fallback to normal write (won't work for protected paths)
                    with open(file_path, 'w') as f:
                        f.write(content)
            
            self.progress.emit("🚀 Starting MemryX driver and runtime installation...")
            
            # Detect architecture
            arch_result = subprocess.run(['uname', '-m'], capture_output=True, text=True, check=True)
            architecture = arch_result.stdout.strip()
            self.progress.emit(f"🏗️ Detected architecture: {architecture}")
            
            # Step 1: Purge existing packages and repo
            self.progress.emit("🗑️ Removing old MemryX installations...")
            
            # Remove any holds on MemryX packages (if they exist)
            try:
                run_sudo_command(['sudo', 'apt-mark', 'unhold', 'memx-*', 'mxa-manager'])
            except subprocess.CalledProcessError:
                pass  # May not exist
            
            try:
                run_sudo_command(['sudo', 'apt', 'purge', '-y', 'memx-*', 'mxa-manager'])
            except subprocess.CalledProcessError:
                pass  # May not exist
                
            # Remove existing MemryX repository and keys (both old and new formats)
            try:
                run_sudo_command(['sudo', 'rm', '-f', 
                                '/etc/apt/sources.list.d/memryx.list',
                                '/etc/apt/trusted.gpg.d/memryx.asc',
                                '/etc/apt/trusted.gpg.d/memryx.gpg'])
            except subprocess.CalledProcessError:
                pass  # May not exist
            
            # Also try to remove from apt-key (legacy method)
            try:
                # List keys and remove any MemryX keys
                list_result = subprocess.run(['apt-key', 'list'], capture_output=True, text=True)
                if 'memryx' in list_result.stdout.lower() or 'D3F12469DCF7E731' in list_result.stdout:
                    run_sudo_command(['sudo', 'apt-key', 'del', 'D3F12469DCF7E731'])
            except subprocess.CalledProcessError:
                pass  # Key may not exist
            
            # Step 2: Install kernel headers
            kernel_version_result = subprocess.run(['uname', '-r'], capture_output=True, text=True, check=True)
            kernel_version = kernel_version_result.stdout.strip()
            self.progress.emit(f"🔧 Installing kernel headers for: {kernel_version}")
            
            run_sudo_command(['sudo', 'apt', 'update'])
            run_sudo_command(['sudo', 'apt', 'install', '-y', 'dkms', f'linux-headers-{kernel_version}'])
            
            # Step 3: Add MemryX key and repo
            self.progress.emit("🔑 Adding MemryX GPG key and repository...")
            
            # Method 1: Try using wget and gpg --dearmor (modern approach)
            try:
                # Download GPG key and convert to proper format
                self.progress.emit("📥 Downloading MemryX GPG key...")
                subprocess.run([
                    'wget', '-qO-', 'https://developer.memryx.com/deb/memryx.asc'
                ], stdout=open('/tmp/memryx_key.asc', 'w'), check=True)
                
                # Convert ASCII armored key to binary format that apt can use
                subprocess.run([
                    'gpg', '--dearmor', '--output', '/tmp/memryx.gpg', '/tmp/memryx_key.asc'
                ], check=True)
                
                # Copy the binary GPG key to the correct location with proper permissions
                run_sudo_command(['sudo', 'cp', '/tmp/memryx.gpg', '/etc/apt/trusted.gpg.d/memryx.gpg'])
                run_sudo_command(['sudo', 'chmod', '644', '/etc/apt/trusted.gpg.d/memryx.gpg'])
                run_sudo_command(['sudo', 'chown', 'root:root', '/etc/apt/trusted.gpg.d/memryx.gpg'])
                
                # Clean up temporary files
                subprocess.run(['rm', '-f', '/tmp/memryx_key.asc', '/tmp/memryx.gpg'], check=False)
                
            except subprocess.CalledProcessError as e:
                self.progress.emit(f"⚠️ GPG method 1 failed: {e}")
                self.progress.emit("🔄 Trying alternative GPG key installation method...")
                
                # Method 2: Direct curl and apt-key approach (fallback)
                try:
                    # Use curl to download and pipe directly to apt-key
                    curl_cmd = ['curl', '-fsSL', 'https://developer.memryx.com/deb/memryx.asc']
                    apt_key_cmd = ['sudo', '-S', 'apt-key', 'add', '-']
                    
                    # Run curl and pipe to apt-key
                    curl_proc = subprocess.Popen(curl_cmd, stdout=subprocess.PIPE)
                    apt_key_proc = subprocess.Popen(apt_key_cmd, stdin=curl_proc.stdout, 
                                                   input=f"{self.sudo_password}\n" if self.sudo_password else None,
                                                   text=True, capture_output=True)
                    curl_proc.stdout.close()
                    curl_proc.wait()
                    apt_key_proc.wait()
                    
                    if apt_key_proc.returncode != 0:
                        raise subprocess.CalledProcessError(apt_key_proc.returncode, 'apt-key')
                        
                except subprocess.CalledProcessError as e2:
                    self.progress.emit(f"❌ Both GPG methods failed. Last error: {e2}")
                    raise Exception("Failed to install MemryX GPG key")
            
            # Add repository
            self.progress.emit("📝 Adding MemryX repository...")
            write_sudo_file('/etc/apt/sources.list.d/memryx.list', 
                          'deb https://developer.memryx.com/deb stable main\n')
            
            # Step 4: Update and install memx-drivers
            self.progress.emit("📦 Installing memx-drivers...")
            
            # Update package lists with detailed error handling
            try:
                result = run_sudo_command(['sudo', 'apt', 'update'])
                self.progress.emit("✅ Package lists updated successfully")
            except subprocess.CalledProcessError as e:
                self.progress.emit(f"⚠️ Package update had warnings (this is often normal): {e}")
                # Continue anyway - warnings are often non-fatal
                
            # Try to install memx-drivers
            try:
                run_sudo_command(['sudo', 'apt', 'install', '-y', 'memx-drivers'])
                self.progress.emit("✅ memx-drivers installed successfully")
            except subprocess.CalledProcessError as e:
                self.progress.emit(f"❌ Failed to install memx-drivers: {e}")
                # Try to get more specific error information
                try:
                    search_result = subprocess.run(['apt', 'search', 'memx-drivers'], 
                                                 capture_output=True, text=True)
                    if 'memx-drivers' in search_result.stdout:
                        self.progress.emit("📦 Package memx-drivers is available in repository")
                    else:
                        self.progress.emit("❌ Package memx-drivers not found in repository")
                        self.progress.emit("🔍 Checking repository configuration...")
                        
                        # Check if repository was added correctly
                        try:
                            with open('/etc/apt/sources.list.d/memryx.list', 'r') as f:
                                repo_content = f.read().strip()
                            self.progress.emit(f"📝 Repository content: {repo_content}")
                        except:
                            self.progress.emit("❌ Repository file not found or not readable")
                            
                except Exception as search_error:
                    self.progress.emit(f"❌ Could not search for package: {search_error}")
                    
                raise e  # Re-raise the original error
            
            # Step 5: ARM-specific board setup
            if architecture in ['aarch64', 'arm64']:
                self.progress.emit("🔧 Running ARM board setup...")
                run_sudo_command(['sudo', 'mx_arm_setup'])
            
            self.progress.emit("⚠️ SYSTEM RESTART REQUIRED AFTER DRIVER INSTALLATION")
            
            # Step 6: Install other runtime packages
            packages = ['memx-accl', 'mxa-manager']
            for pkg in packages:
                self.progress.emit(f"📦 Installing {pkg}...")
                run_sudo_command(['sudo', 'apt', 'install', '-y', pkg])
            
            self.progress.emit("✅ MemryX installation completed successfully!")
            self.progress.emit("🔄 Please restart your computer to complete the installation.")
            
            self.finished.emit(True)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Command failed: {e.cmd}"
            if e.stderr:
                error_msg += f"\n   Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}"
            self.progress.emit(error_msg)
            self.finished.emit(False)
            
        except Exception as e:
            self.progress.emit(f"❌ Installation error: {str(e)}")
            self.finished.emit(False)

class MemryXUpdateWorker(QThread):
    """Background worker for MemryX SDK update to version 2.1"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, script_dir, sudo_password=None):
        super().__init__()
        self.script_dir = script_dir
        self.sudo_password = sudo_password
    
    def run(self):
        try:
            # Helper function to run sudo commands with password
            def run_sudo_command(cmd, input_text=None, **kwargs):
                if self.sudo_password:
                    sudo_cmd = ['sudo', '-S'] + cmd[1:]
                    if input_text:
                        raise ValueError("Use write_sudo_file for commands that need file input")
                    return subprocess.run(sudo_cmd, input=f"{self.sudo_password}\n", text=True, check=True, capture_output=True, **kwargs)
                else:
                    return subprocess.run(cmd, input=input_text, text=True, check=True, capture_output=True, **kwargs)
            
            self.progress.emit("🚀 Starting MemryX SDK update to version 2.1...")
            
            # Check current version
            try:
                result = subprocess.run(['dpkg-query', '-W', '-f=${Version}', 'memx-drivers'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    current_version = result.stdout.strip()
                    version_major_minor = '.'.join(current_version.split('.')[:2])
                    self.progress.emit(f"📦 Current MemryX SDK version: {current_version}")
                    
                    if version_major_minor == "2.1":
                        self.progress.emit("✅ MemryX SDK is already at version 2.1")
                        # Still ensure packages are held
                        self.progress.emit("🔒 Ensuring packages are held at version 2.1...")
                        try:
                            run_sudo_command(['sudo', 'apt-mark', 'hold', 'memx-drivers', 'memx-accl', 'mxa-manager'])
                            self.progress.emit("✅ Packages held successfully")
                        except Exception as e:
                            self.progress.emit(f"⚠️ Could not hold packages: {e}")
                        self.finished.emit(True)
                        return
                else:
                    self.progress.emit("📥 MemryX SDK not installed - installing version 2.1...")
            except Exception as e:
                self.progress.emit(f"⚠️ Could not check current version: {e}")
                self.progress.emit("📥 Proceeding with installation...")
            
            # Remove any holds on MemryX packages
            self.progress.emit("🔓 Removing package holds...")
            try:
                run_sudo_command(['sudo', 'apt-mark', 'unhold', 'memx-drivers', 'memx-accl', 'mxa-manager'])
            except subprocess.CalledProcessError:
                pass  # May not be held
            
            # Update package lists
            self.progress.emit("📥 Updating package lists...")
            run_sudo_command(['sudo', 'apt', 'update'])
            
            # Run dist-upgrade to ensure dependencies are up to date
            self.progress.emit("⬆️ Upgrading system packages...")
            run_sudo_command(['sudo', 'apt', 'dist-upgrade', '-y'])
            
            # Install specific version 2.1.* for all three packages
            self.progress.emit("📦 Installing MemryX SDK 2.1 packages...")
            self.progress.emit("   • memx-drivers=2.1.*")
            self.progress.emit("   • memx-accl=2.1.*")
            self.progress.emit("   • mxa-manager=2.1.*")
            
            try:
                run_sudo_command(['sudo', 'apt', 'install', '-y', 
                                'memx-drivers=2.1.*', 
                                'memx-accl=2.1.*', 
                                'mxa-manager=2.1.*'])
                self.progress.emit("✅ MemryX SDK 2.1 packages installed successfully")
            except subprocess.CalledProcessError as e:
                self.progress.emit(f"❌ Failed to install packages: {e}")
                # Try to get more info
                try:
                    search_result = subprocess.run(['apt-cache', 'policy', 'memx-drivers'], 
                                                 capture_output=True, text=True)
                    self.progress.emit(f"📋 Available versions:\n{search_result.stdout}")
                except:
                    pass
                raise e
            
            # Hold packages at version 2.1
            self.progress.emit("🔒 Holding packages at version 2.1 to prevent auto-updates...")
            run_sudo_command(['sudo', 'apt-mark', 'hold', 'memx-drivers', 'memx-accl', 'mxa-manager'])
            self.progress.emit("✅ Packages held at version 2.1")
            
            # Verify installation
            self.progress.emit("🔍 Verifying installation...")
            try:
                result = subprocess.run(['dpkg-query', '-W', '-f=${Version}', 'memx-drivers'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    new_version = result.stdout.strip()
                    self.progress.emit(f"✅ Installed version: {new_version}")
            except:
                pass
            
            self.progress.emit("=" * 60)
            self.progress.emit("✅ MemryX SDK 2.1 update completed successfully!")
            self.progress.emit("🎯 Your system is now compatible with Frigate")
            self.progress.emit("=" * 60)
            
            self.finished.emit(True)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Command failed: {e.cmd}"
            if e.stderr:
                error_msg += f"\n   Error: {e.stderr.decode() if isinstance(e.stderr, bytes) else e.stderr}"
            self.progress.emit(error_msg)
            self.finished.emit(False)
            
        except Exception as e:
            self.progress.emit(f"❌ Update error: {str(e)}")
            self.finished.emit(False)

class FFmpegInstallWorker(QThread):
    """Background worker for FFmpeg VA-API installation"""
    progress = Signal(str)
    finished = Signal(bool)
    config_path = Signal(str)  # Emit config path for auto-update
    
    def __init__(self, script_dir, sudo_password=None):
        super().__init__()
        self.script_dir = script_dir
        self.sudo_password = sudo_password
    
    def run(self):
        try:
            # Helper function to run sudo commands with password
            def run_sudo_command(cmd, input_text=None, **kwargs):
                if self.sudo_password:
                    sudo_cmd = ['sudo', '-S'] + cmd[1:]
                    if input_text:
                        raise ValueError("Cannot mix password and content input")
                    return subprocess.run(sudo_cmd, input=f"{self.sudo_password}\n", 
                                        text=True, check=True, capture_output=True, **kwargs)
                else:
                    return subprocess.run(cmd, input=input_text, text=True, 
                                        check=True, capture_output=True, **kwargs)
            
            self.progress.emit("⚡ Starting FFmpeg VA-API drivers installation...")
            self.progress.emit("=" * 60)
            
            # Step 1: Update package repositories
            self.progress.emit("📦 Updating package repositories...")
            run_sudo_command(['sudo', 'apt', 'update'])
            self.progress.emit("✅ Package repositories updated")
            
            # Step 2: Install FFmpeg VA-API packages
            self.progress.emit("📦 Installing VA-API hardware acceleration packages:")
            self.progress.emit("   • ffmpeg - Video encoding/decoding framework")
            self.progress.emit("   • vainfo - VA-API information utility")
            self.progress.emit("   • intel-media-va-driver - Intel Media SDK VA-API driver")
            self.progress.emit("   • i965-va-driver - Legacy Intel VA-API driver")
            self.progress.emit("   • mesa-va-drivers - Mesa VA-API drivers")
            self.progress.emit("   • libva2 - VA-API library")
            self.progress.emit("   • libva-drm2 - VA-API DRM runtime")
            
            packages = [
                'ffmpeg',
                'vainfo',
                'intel-media-va-driver',
                'i965-va-driver',
                'mesa-va-drivers',
                'libva2',
                'libva-drm2'
            ]
            
            run_sudo_command(['sudo', 'apt', 'install', '-y'] + packages)
            self.progress.emit("✅ All VA-API packages installed successfully")
            
            # Step 3: Verify installation
            self.progress.emit("")
            self.progress.emit("🔍 Verifying installation...")
            
            # Verify each package
            all_installed = True
            for package in packages:
                result = subprocess.run(['dpkg-query', '-W', '-f=${Status}', package],
                                      capture_output=True, text=True)
                if result.returncode == 0 and 'install ok installed' in result.stdout:
                    self.progress.emit(f"   ✅ {package}")
                else:
                    self.progress.emit(f"   ❌ {package} - NOT INSTALLED")
                    all_installed = False
            
            if not all_installed:
                self.progress.emit("")
                self.progress.emit("⚠️  Some packages failed to install")
                self.finished.emit(False)
                return
            
            # Step 4: Test VA-API
            self.progress.emit("")
            self.progress.emit("🧪 Testing VA-API capability...")
            try:
                vainfo_result = subprocess.run(['vainfo'], capture_output=True, 
                                             text=True, timeout=5)
                if vainfo_result.returncode == 0:
                    self.progress.emit("✅ VA-API is working correctly")
                    # Parse and show driver info
                    for line in vainfo_result.stdout.split('\n'):
                        if 'Driver version' in line or 'VAProfile' in line[:15]:
                            self.progress.emit(f"   {line.strip()}")
                            if 'VAProfile' in line[:15]:  # Only show first few profiles
                                break
                else:
                    self.progress.emit("⚠️  VA-API test completed with warnings")
                    self.progress.emit("   Your GPU may not support hardware acceleration")
            except subprocess.TimeoutExpired:
                self.progress.emit("⚠️  VA-API test timed out")
            except Exception as e:
                self.progress.emit(f"⚠️  VA-API test error: {str(e)}")
            
            # Step 5: Emit config path for auto-update
            config_file = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
            self.config_path.emit(config_file)
            
            self.progress.emit("")
            self.progress.emit("=" * 60)
            self.progress.emit("✅ FFmpeg VA-API installation completed successfully!")
            self.progress.emit("🎯 Hardware acceleration is now available for Frigate")
            self.progress.emit("=" * 60)
            
            self.finished.emit(True)
            
        except subprocess.CalledProcessError as e:
            error_msg = f"❌ Command failed: {' '.join(e.cmd)}"
            if e.stderr:
                error_msg += f"\n   Error: {e.stderr}"
            self.progress.emit(error_msg)
            self.finished.emit(False)
            
        except Exception as e:
            self.progress.emit(f"❌ Installation error: {str(e)}")
            self.finished.emit(False)

class StatusCheckWorker(QThread):
    """Background worker for status checking to prevent UI blocking"""
    status_updated = Signal(dict)  # Emit status results
    finished = Signal()
    
    def __init__(self, script_dir):
        super().__init__()
        self.script_dir = script_dir
        
    def run(self):
        """Run status checks in background thread"""
        try:
            status_data = {}
            
            # Check Frigate container status
            status_data['frigate'] = self._check_frigate_status()
            
            # Check Docker service status  
            status_data['docker'] = self._check_docker_status()
            
            # Check configuration status
            status_data['config'] = self._check_config_status()
            
            # Check MemryX devices
            status_data['memryx'] = self._check_memryx_status()
            
            # Emit results
            self.status_updated.emit(status_data)
            
        except Exception as e:
            # Emit error status
            error_status = {
                'frigate': {'text': '❓ Check Failed', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'},
                'docker': {'text': '❓ Check Failed', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'},
                'config': {'text': '❓ Check Failed', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'},
                'memryx': {'text': '❓ Check Failed', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'}
            }
            self.status_updated.emit(error_status)
        finally:
            self.finished.emit()
    
    def _check_frigate_status(self):
        """Check Frigate container status"""
        try:
            # Check if container exists (running or stopped)
            all_containers = subprocess.run(['docker', 'ps', '-a', '-q', '-f', 'name=frigate'], 
                                          capture_output=True, text=True, timeout=10)
            
            if all_containers.stdout.strip():
                # Container exists, check if it's running
                running_containers = subprocess.run(['docker', 'ps', '-q', '-f', 'name=frigate'], 
                                                  capture_output=True, text=True, timeout=10)
                
                if running_containers.stdout.strip():
                    return {'text': '✅ Running', 'style': 'background: #e8f4f0; color: #2d5a4a; padding: 6px; border-radius: 4px;'}
                else:
                    return {'text': '⏸️ Stopped', 'style': 'background: #fff3cd; color: #856404; padding: 6px; border-radius: 4px;'}
            else:
                return {'text': '❌ Not Created', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
                
        except subprocess.TimeoutExpired:
            return {'text': '⏱️ Docker Timeout', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'}
        except FileNotFoundError:
            return {'text': '❌ Docker Not Installed', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
        except Exception:
            return {'text': '❓ Unknown Error', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'}
    
    def _check_docker_status(self):
        """Check Docker service status"""
        try:
            result = subprocess.run(['docker', 'info'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return {'text': '✅ Running', 'style': 'background: #e8f4f0; color: #2d5a4a; padding: 6px; border-radius: 4px;'}
            else:
                return {'text': '❌ Not Available', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
        except subprocess.TimeoutExpired:
            return {'text': '⏱️ Docker Timeout', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'}
        except FileNotFoundError:
            return {'text': '❌ Not Installed', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
        except Exception:
            return {'text': '❌ Not Installed', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
    
    def _check_config_status(self):
        """Check configuration file status"""
        config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
        if os.path.exists(config_path):
            return {'text': '✅ Found', 'style': 'background: #e8f4f0; color: #2d5a4a; padding: 6px; border-radius: 4px;'}
        else:
            return {'text': '❌ Missing', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
    
    def _check_memryx_status(self):
        """Check MemryX devices status"""
        try:
            import glob
            devices = [d for d in glob.glob("/dev/memx*") if "_feature" not in d]
            if devices:
                device_count = len(devices)
                return {'text': f'✅ {device_count} devices found', 'style': 'background: #e8f4f0; color: #2d5a4a; padding: 6px; border-radius: 4px;'}
            else:
                return {'text': '❌ No Devices', 'style': 'background: #fbeaea; color: #6b3737; padding: 6px; border-radius: 4px;'}
        except Exception:
            return {'text': '❓ Check Failed', 'style': 'background: #fdf6e3; color: #8b7355; padding: 6px; border-radius: 4px;'}

class FrigateLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.config_file_mtime = 0  # Track config file modification time
        self.suppress_config_change_popup = False  # Flag to suppress config change popup
        
        # Setup completion tracking
        self.setup_complete_file = os.path.join(self.script_dir, '.camera_setup_complete')
        self.is_first_run = not os.path.exists(self.setup_complete_file)

        # Initialize worker thread reference
        self.docker_worker = None
        
        # Initialize loading state
        self.is_initializing = True
        
        # Button state enhancement variables
        self.button_animation_timer = QTimer()
        self.button_animation_timer.timeout.connect(self.update_button_animation)
        self.button_animation_dots = 0
        self.button_base_text = ""
        self.button_operation_state = "idle"  # idle, starting, building, starting_container, running, stopping
        
        # Store references to container layouts for responsive resizing
        self.responsive_containers = []
        
        # Modal overlay for dimming background during dialogs
        self.modal_overlay = ModalOverlay(self)
        self.modal_overlay.hide()  # Initially hidden
        
        # Common scroll bar styling for consistency across all text areas
        self.scroll_bar_style = """
            QScrollBar:vertical {
                background: #f0f0f0;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #4a90a4;
                border-radius: 6px;
                min-height: 20px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background: #38758a;
            }
            QScrollBar::handle:vertical:pressed {
                background: #2c6b7d;
            }
            QScrollBar:horizontal {
                background: #f0f0f0;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QScrollBar::handle:horizontal {
                background: #4a90a4;
                border-radius: 6px;
                min-width: 20px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #38758a;
            }
            QScrollBar::handle:horizontal:pressed {
                background: #2c6b7d;
            }
            QScrollBar::add-line, QScrollBar::sub-line {
                border: none;
                background: none;
            }
        """
        
        # Create timers before setup_ui() so they're available during tab creation
        # Status check timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status)
        
        # Config file watcher timer
        self.config_watcher_timer = QTimer()
        self.config_watcher_timer.timeout.connect(self.check_config_file_changes)
        
        # Logs auto-refresh timer
        self.logs_timer = QTimer()
        self.logs_timer.timeout.connect(self.refresh_logs)
        
        # Setup UI (this will create tabs and potentially start timers)
        self.setup_ui()
        
        # Defer heavy operations until after UI is shown to improve startup time
        QTimer.singleShot(100, self._initialize_async_components)
    
    def create_header(self, layout):
        """Create professional header with MemryX and Frigate logos"""
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 {SURFACE_BG});
                border: none;
                padding: 15px 30px;
            }}
        """)
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(20, 10, 20, 10)
        header_layout.setSpacing(20)
        
        # MemryX Logo (left)
        memryx_logo_path = os.path.join(self.script_dir, "assets", "memryx.png")
        if os.path.exists(memryx_logo_path):
            memryx_logo_label = QLabel()
            memryx_pixmap = QPixmap(memryx_logo_path)
            memryx_logo_label.setPixmap(memryx_pixmap.scaledToHeight(70, Qt.SmoothTransformation))
            memryx_logo_label.setStyleSheet("background: transparent;")
            header_layout.addWidget(memryx_logo_label)
        
        # Spacer
        header_layout.addSpacing(10)
        
        # Title section (center) with modern design
        title_container = QWidget()
        title_container.setStyleSheet("background: transparent;")
        title_container.setMinimumWidth(400)  # Prevent shrinking too much
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 5, 0, 5)
        title_layout.setSpacing(2)
        
        # Main title with gradient text effect
        title = QLabel("Frigate MemryX Manager")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)  # Allow text to wrap if needed
        title.setMinimumHeight(50)  # Ensure minimum height
        title.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 rgba(74, 144, 164, 0.08), 
                    stop:0.5 rgba(66, 153, 225, 0.12),
                    stop:1 rgba(74, 144, 164, 0.08));
                border-radius: 10px;
                padding: 12px 30px;
                letter-spacing: -0.5px;
            }}
        """)
        title_layout.addWidget(title)
        
        # Subtitle
        subtitle = QLabel("Professional NVR Management System")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                background: transparent;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
        """)
        title_layout.addWidget(subtitle)
        
        header_layout.addWidget(title_container, 1)
        
        # Spacer
        header_layout.addSpacing(10)
        
        # Frigate Logo (right)
        frigate_logo_path = os.path.join(self.script_dir, "assets", "frigate.png")
        if os.path.exists(frigate_logo_path):
            frigate_logo_label = QLabel()
            frigate_pixmap = QPixmap(frigate_logo_path)
            frigate_logo_label.setPixmap(frigate_pixmap.scaledToHeight(70, Qt.SmoothTransformation))
            frigate_logo_label.setStyleSheet("background: transparent;")
            header_layout.addWidget(frigate_logo_label)
        
        layout.addWidget(header_frame)
    
    def on_section_toggled(self, section, expanded):
        """Handle section toggle with accordion behavior and auto-scroll"""
        if expanded:
            # Accordion behavior: Collapse all other sections
            for other_section in self.all_sections:
                if other_section != section and other_section.is_expanded:
                    other_section.collapse()
            
            # Auto-scroll to the expanded section after a short delay
            # This allows the expand animation to start first
            QTimer.singleShot(100, lambda: self.scroll_to_section(section))
    
    def scroll_to_section(self, section):
        """Smoothly scroll to make the section prominent in the viewport"""
        try:
            # Get the section's position relative to the content widget
            section_pos = section.mapTo(self.content_widget, section.rect().topLeft())
            
            # Calculate target scroll position to show section at top with some padding
            target_y = section_pos.y() - 20  # 20px padding from top
            
            # Get current scroll position
            scrollbar = self.main_scroll_area.verticalScrollBar()
            current_pos = scrollbar.value()
            
            # Smooth scroll animation
            from PySide6.QtCore import QPropertyAnimation, QEasingCurve
            
            self.scroll_animation = QPropertyAnimation(scrollbar, b"value")
            self.scroll_animation.setDuration(400)  # 400ms smooth scroll
            self.scroll_animation.setStartValue(current_pos)
            self.scroll_animation.setEndValue(target_y)
            self.scroll_animation.setEasingCurve(QEasingCurve.OutCubic)
            self.scroll_animation.start()
            
        except Exception as e:
            print(f"Scroll animation error: {e}")
    
    def show_modal_overlay(self):
        """Show the modal overlay to dim the background"""
        if hasattr(self, 'modal_overlay'):
            self.modal_overlay.show_overlay()
    
    def hide_modal_overlay(self):
        """Hide the modal overlay"""
        if hasattr(self, 'modal_overlay'):
            self.modal_overlay.hide_overlay()
    
    def show_message_box(self, icon, title, text, buttons=None, default_button=None):
        """Show a QMessageBox with modal overlay"""
        self.show_modal_overlay()
        
        try:
            if buttons is None:
                buttons = QMessageBox.Ok
            if default_button is None:
                default_button = QMessageBox.Ok
                
            msg_box = QMessageBox(icon, title, text, buttons, self)
            msg_box.setDefaultButton(default_button)
            result = msg_box.exec()
            return result
        finally:
            self.hide_modal_overlay()
    
    def show_dialog(self, dialog):
        """Show a QDialog with modal overlay"""
        self.show_modal_overlay()
        
        try:
            result = dialog.exec()
            return result
        finally:
            self.hide_modal_overlay()
    
    def show_external_gui(self, gui_instance):
        """Show an external GUI window with modal overlay"""
        self.show_modal_overlay()
        
        # Store original close event if it exists
        if hasattr(gui_instance, 'closeEvent'):
            original_close = gui_instance.closeEvent
        else:
            original_close = None
        
        # Create enhanced close event handler
        def enhanced_close(event):
            self.hide_modal_overlay()
            if original_close:
                original_close(event)
            else:
                event.accept()
        
        # Override the closeEvent
        gui_instance.closeEvent = enhanced_close
        
        # Also handle if the GUI emits a finished signal
        if hasattr(gui_instance, 'finished'):
            gui_instance.finished.connect(self.hide_modal_overlay)
        
        # Show the GUI
        gui_instance.show()
    
    def setup_ui(self):
        """New setup_ui method with collapsible sections instead of tabs"""
        self.setWindowTitle("Frigate MemryX Manager")
        
        # Set window icon if available
        icon_path = os.path.join(self.script_dir, "assets", "frigate.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # Get screen size and set window geometry
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        self.setGeometry(screen_geometry)
        
        # Set minimum size
        self.setMinimumSize(900, 700)
        
        # Enable window controls
        self.setWindowFlags(Qt.Window | Qt.WindowMinimizeButtonHint | 
                           Qt.WindowMaximizeButtonHint | Qt.WindowCloseButtonHint)
        
        # Create menu bar (simplified version)
        self.create_simple_menu_bar()
        
        # Apply modern styling with professional teal theme
        self.setStyleSheet(f"""
            QMainWindow {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 {BACKGROUND}, stop:1 {SURFACE_BG});
                color: {TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Inter', 'system-ui', '-apple-system', sans-serif;
            }}
            QMenuBar {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff, stop:1 {SURFACE_BG});
                border-bottom: 1px solid {BORDER_COLOR};
                spacing: 3px;
                padding: 6px 10px;
                font-weight: 500;
                font-size: 16px;
                color: {TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            QMenuBar::item {{
                padding: 8px 14px;
                border-radius: 6px;
                margin: 1px;
            }}
            QMenuBar::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_DARK});
                color: white;
            }}
            QMenuBar::item:pressed {{
                background: {PRIMARY_DARKER};
                color: white;
            }}
            QMenu {{
                background: white;
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 6px;
                font-size: 16px;
                color: {TEXT_PRIMARY};
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            QMenu::item {{
                padding: 10px 26px 10px 34px;
                border-radius: 6px;
                margin: 2px;
            }}
            QMenu::item:selected {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_DARK});
                color: white;
            }}
            QMenu::separator {{
                height: 1px;
                background: {BORDER_COLOR};
                margin: 4px 16px;
            }}
        """)
        
        # Central widget with scroll area
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Add professional header with logos
        self.create_header(main_layout)
        
        # Create scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QScrollArea.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollArea {{
                background: {BACKGROUND};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {SURFACE_BG};
                width: 14px;
                border-radius: 7px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PRIMARY_COLOR}, stop:1 {PRIMARY_DARK});
                border-radius: 7px;
                min-height: 30px;
                margin: 2px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {PRIMARY_LIGHT}, stop:1 {PRIMARY_COLOR});
            }}
            QScrollBar::handle:vertical:pressed {{
                background: {PRIMARY_DARKER};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                border: none;
                background: none;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)
        # Content widget
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(30, 20, 30, 20)
        content_layout.setSpacing(20)
        
        # Import widgets
        from frigate_widgets import (
            FrigateInstallWidget, ConfigureWidget, LaunchMonitorWidget
        )
        
        # 1. Welcome Widget (always visible)
        welcome_widget = WelcomeWidget(self)
        content_layout.addWidget(welcome_widget)
        
        # 2. Section 1: Get Started (Prerequisites)
        self.section1 = CollapsibleSection(
            "1. Get Started (Prerequisites)",
            "Install required system components before setting up Frigate"
        )
        self.prerequisites_widget = PrerequisitesWidget(self.script_dir, self)
        self.prerequisites_widget.status_changed.connect(
            lambda status: self.section1.set_status(status)
        )
        self.section1.set_content(self.prerequisites_widget)
        self.section1.toggled.connect(lambda expanded: self.on_section_toggled(self.section1, expanded))
        content_layout.addWidget(self.section1)
        
        # 3. Section 2: Install Frigate
        self.section2 = CollapsibleSection(
            "2. Install Frigate",
            "Clone and set up the Frigate NVR system"
        )
        self.frigate_install_widget = FrigateInstallWidget(self.script_dir, self)
        self.frigate_install_widget.status_changed.connect(
            lambda status: self.section2.set_status(status)
        )
        self.section2.set_content(self.frigate_install_widget)
        self.section2.toggled.connect(lambda expanded: self.on_section_toggled(self.section2, expanded))
        content_layout.addWidget(self.section2)
        
        # 4. Section 3: Configure Frigate (no status indicator needed)
        self.section3 = CollapsibleSection(
            "3. Configure Frigate",
            "Set up cameras and configure detection settings",
            show_status=False
        )
        self.configure_widget = ConfigureWidget(self.script_dir, self)
        self.section3.set_content(self.configure_widget)
        self.section3.toggled.connect(lambda expanded: self.on_section_toggled(self.section3, expanded))
        content_layout.addWidget(self.section3)
        
        # 5. Section 4: Launch & Monitor (no status indicator needed)
        self.section4 = CollapsibleSection(
            "4. Launch & Monitor",
            "Start Frigate and monitor system status",
            show_status=False
        )
        self.launch_monitor_widget = LaunchMonitorWidget(self.script_dir, self)
        self.section4.set_content(self.launch_monitor_widget)
        self.section4.toggled.connect(lambda expanded: self.on_section_toggled(self.section4, expanded))
        content_layout.addWidget(self.section4)
        
        # Store all sections for accordion behavior
        self.all_sections = [self.section1, self.section2, self.section3, self.section4]
        
        # Store scroll area reference for auto-scrolling
        self.main_scroll_area = scroll_area
        self.content_widget = content_widget
        
        # Add stretch at the end
        content_layout.addStretch()
        
        # Set content widget to scroll area
        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)
        
        # Create simplified status bar
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                background: #e8f4f0;
                color: #2d5a4a;
                padding: 8px 12px;
                border-radius: 4px;
                font-weight: 600;
                font-size: 16px;
            }
        """)
        self.statusBar().addPermanentWidget(self.status_label)
        self.statusBar().showMessage('Frigate MemryX Manager - Ready')
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: white;
                border-top: 1px solid #e2e8f0;
                color: #2d3748;
                font-size: 16px;
                padding: 8px 12px;
            }
        """)
    
    def create_simple_menu_bar(self):
        """Create simplified menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        exit_action = file_menu.addAction('E&xit')
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        about_action = help_menu.addAction('&About')
        about_action.triggered.connect(lambda: QMessageBox.about(
            self,
            "About Frigate MemryX Manager",
            "Frigate MemryX Manager\n\n"
            "A comprehensive GUI for managing Frigate NVR with MemryX acceleration.\n\n"
            "Version: 2.0"
        ))
    
    def close_application(self):
        """Close the application with confirmation"""
        reply = QMessageBox.question(
            self, 'Exit Confirmation',
            'Are you sure you want to exit Frigate Launcher?',
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.close()
    
    def _initialize_async_components(self):
        """Initialize components that require heavy operations after UI is shown"""
        # Initialize status check worker reference
        self.status_worker = None
        
        # Start the initial status check in background thread
        self.start_background_status_check()
        
        # Start the timers after UI is set up and first status check is done
        self.status_timer.start(5000)  # Check every 5 seconds
        self.config_watcher_timer.start(1000)  # Check every 1 second for file changes
        # Timer will be started/stopped based on auto-refresh checkbox state
        
        # Mark initialization as complete
        self.is_initializing = False
        
        # Re-enable buttons now that initialization is complete
        if hasattr(self, 'preconfigured_start_btn'):
            self.preconfigured_start_btn.setEnabled(True)
        if hasattr(self, 'preconfigured_stop_btn'):
            self.preconfigured_stop_btn.setEnabled(True)
        if hasattr(self, 'preconfigured_open_ui_btn'):
            self.preconfigured_open_ui_btn.setEnabled(True)
        if hasattr(self, 'setup_cameras_btn'):
            self.setup_cameras_btn.setEnabled(True)
        if hasattr(self, 'camera_guide_btn'):
            self.camera_guide_btn.setEnabled(True)
        
        # Update status bar to ready state
        if hasattr(self, 'status_label'):
            self.status_label.setText("✅ Ready")
            self.status_label.setStyleSheet("background: #e8f4f0; color: #2d5a4a; padding: 8px 12px; border-radius: 4px; font-weight: 600; font-size: 14px;")
        
        self.statusBar().showMessage('Frigate MemryX Manager - Ready | F11: Fullscreen | F5: Refresh | F1: Help | Ctrl+Q: Exit')
        
        # Hide status bar after a delay
        QTimer.singleShot(3000, lambda: self.statusBar().hide())

    def start_background_status_check(self):
        """Start status checking in background thread"""
        # Don't start new worker if one is already running
        if self.status_worker and self.status_worker.isRunning():
            return
            
        self.status_worker = StatusCheckWorker(self.script_dir)
        self.status_worker.status_updated.connect(self.update_status_from_worker)
        self.status_worker.finished.connect(self.on_status_check_finished)
        self.status_worker.start()
    
    def update_status_from_worker(self, status_data):
        """Update UI with status data from background worker"""
        # Update Frigate status labels
        if 'frigate' in status_data:
            frigate_data = status_data['frigate']
            if hasattr(self, 'frigate_status'):
                self.frigate_status.setText(frigate_data['text'])
                self.frigate_status.setStyleSheet(frigate_data['style'])
            if hasattr(self, 'docker_manager_frigate_status'):
                self.docker_manager_frigate_status.setText(frigate_data['text'])
                self.docker_manager_frigate_status.setStyleSheet(frigate_data['style'])
        
        # Update Docker status
        if 'docker' in status_data and hasattr(self, 'docker_status'):
            docker_data = status_data['docker']
            self.docker_status.setText(docker_data['text'])
            self.docker_status.setStyleSheet(docker_data['style'])
        
        # Update config status
        if 'config' in status_data and hasattr(self, 'config_status'):
            config_data = status_data['config']
            self.config_status.setText(config_data['text'])
            self.config_status.setStyleSheet(config_data['style'])
        
        # Update MemryX status  
        if 'memryx' in status_data and hasattr(self, 'memryx_overview_status'):
            memryx_data = status_data['memryx']
            self.memryx_overview_status.setText(memryx_data['text'])
            self.memryx_overview_status.setStyleSheet(memryx_data['style'])
        
        # Update system monitoring (non-blocking)
        self.update_system_monitoring()
        
        # Update button states
        self.update_button_states_from_status(status_data)
    
    def update_button_states_from_status(self, status_data):
        """Update button states based on status data"""
        if 'frigate' in status_data:
            frigate_text = status_data['frigate']['text']
            container_running = '✅ Running' in frigate_text
            container_exists = container_running or '⏸️ Stopped' in frigate_text
            
            # Update button states
            if hasattr(self, 'docker_restart_btn') and hasattr(self, 'docker_remove_btn'):
                self.docker_restart_btn.setEnabled(container_exists)
                self.docker_remove_btn.setEnabled(container_exists)
    
    def on_status_check_finished(self):
        """Called when background status check completes"""
        # Worker finished, clean up reference
        if self.status_worker:
            self.status_worker.deleteLater()
            self.status_worker = None

    def _check_container_exists_sync(self):
        """Synchronously check if Frigate container exists (for UI updates)"""
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=frigate', '--format', '{{.Names}}'], 
                                    capture_output=True, text=True, timeout=5)
            return 'frigate' in result.stdout
        except:
            return False
    
    def check_status(self):
        """Check system status using background thread to avoid UI blocking"""
        # Use background worker instead of blocking subprocess calls
        self.start_background_status_check()
    
    def update_system_monitoring(self):
        """Update system monitoring labels for both Overview and Docker Manager tabs"""
        if not PSUTIL_AVAILABLE:
            return
        
        try:
            import psutil
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=0.1)
            cpu_text = f"{cpu_percent:.1f}%"
            
            # Get memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            memory_text = f"{memory_percent:.1f}% ({memory_used_gb:.1f} GB / {memory_total_gb:.1f} GB)"
            
            # Update Overview tab labels (if they exist)
            if hasattr(self, 'cpu_usage_label'):
                self.cpu_usage_label.setText(cpu_text)
            if hasattr(self, 'memory_usage_label'):
                self.memory_usage_label.setText(memory_text)
            if hasattr(self, 'disk_usage_label'):
                # Get disk usage for the script directory
                disk_usage = psutil.disk_usage(self.script_dir)
                disk_percent = (disk_usage.used / disk_usage.total) * 100
                disk_used_gb = disk_usage.used / (1024**3)
                disk_total_gb = disk_usage.total / (1024**3)
                disk_text = f"{disk_percent:.1f}% ({disk_used_gb:.1f} GB / {disk_total_gb:.1f} GB)"
                self.disk_usage_label.setText(disk_text)
                
        except Exception as e:
            # Handle any errors gracefully
            error_text = f"❌ Error: {str(e)[:20]}..."
            
            # Update Overview tab labels with error
            if hasattr(self, 'cpu_usage_label'):
                self.cpu_usage_label.setText(error_text)
            if hasattr(self, 'memory_usage_label'):
                self.memory_usage_label.setText(error_text)
            if hasattr(self, 'disk_usage_label'):
                self.disk_usage_label.setText(error_text)
    
    def get_memryx_devices(self):
        """Get MemryX devices with caching to improve performance"""
        # Use cached result if available and not too old (cache for 10 seconds)
        current_time = time.time()
        if hasattr(self, '_memryx_cache') and hasattr(self, '_memryx_cache_time'):
            if current_time - self._memryx_cache_time < 10:
                return self._memryx_cache
        
        try:
            import glob
            devices = [d for d in glob.glob("/dev/memx*") if "_feature" not in d]
            result = f"{len(devices)} devices found" if devices else "No devices found"
            
            # Cache the result
            self._memryx_cache = result
            self._memryx_cache_time = current_time
            return result
        except Exception:
            result = "Unable to check devices"
            # Cache the error result too (but for shorter time)
            self._memryx_cache = result
            self._memryx_cache_time = current_time - 5  # Cache error for only 5 seconds
            return result
    
    def check_repo_status(self):
        """Check the current status of the Frigate repository"""
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if not os.path.exists(frigate_path):
            self.repo_status_label.setText("❌ No Frigate repository found")
            self.repo_status_label.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
            return
        
        git_dir = os.path.join(frigate_path, '.git')
        if not os.path.exists(git_dir):
            self.repo_status_label.setText("⚠️ Frigate directory exists but is not a git repository")
            self.repo_status_label.setStyleSheet("background: #fdf6e3; color: #8b7355; padding: 8px; border-radius: 6px;")
            return
        
        try:
            # Check git status
            result = subprocess.run(['git', 'status', '--porcelain'], 
                                  cwd=frigate_path, capture_output=True, text=True)
            if result.returncode != 0:
                self.repo_status_label.setText("❌ Git repository is corrupted")
                self.repo_status_label.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
                return
            
            # Check for local changes
            has_changes = bool(result.stdout.strip())
            
            # Get current branch and commit info
            branch_result = subprocess.run(['git', 'branch', '--show-current'], 
                                         cwd=frigate_path, capture_output=True, text=True)
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "detached"
            
            # Get last commit info
            commit_result = subprocess.run(['git', 'log', '-1', '--format=%h - %s (%cr)'], 
                                         cwd=frigate_path, capture_output=True, text=True)
            last_commit = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
            
            # Check if we can fetch (to see if there are remote updates)
            try:
                subprocess.run(['git', 'fetch', '--dry-run'], cwd=frigate_path, 
                             capture_output=True, timeout=10)
                fetch_status = "✅ Can connect to remote"
            except:
                fetch_status = "⚠️ Cannot connect to remote"
            
            status_text = f"✅ Valid git repository\n"
            status_text += f"Branch: {current_branch}\n"
            status_text += f"Last commit: {last_commit}\n"
            status_text += f"Local changes: {'Yes' if has_changes else 'No'}\n"
            status_text += f"Remote status: {fetch_status}"
            
            self.repo_status_label.setText(status_text)
            self.repo_status_label.setStyleSheet("background: #e8f4f0; color: #2d5a4a; padding: 8px; border-radius: 6px;")
            
        except Exception as e:
            self.repo_status_label.setText(f"❌ Error checking repository: {str(e)}")
            self.repo_status_label.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
        
        # Update guidance after checking status
        if hasattr(self, 'step2_guidance'):
            self.update_step2_guidance()
    
    def install_frigate(self, action_type='skip_frigate'):
        """Start the installation process with specified action type"""
        # Clear progress and show action being performed
        self.install_progress.clear()
        
        action_descriptions = {
            'clone_only': "🚀 Starting Frigate repository clone process...",
            'update_only': "🔄 Starting Frigate repository update process...",
        }
        
        self.install_progress.append(action_descriptions.get(action_type, "Starting installation..."))
        
        # Enhanced validation for repository actions
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if action_type == 'clone_only':
            self.install_progress.append("📋 Cloning fresh Frigate repository...")
            if os.path.exists(frigate_path):
                self.install_progress.append("⚠️  Existing Frigate directory will be removed and replaced.")
        
        if action_type == 'update_only':
            self.install_progress.append("📋 Updating existing Frigate repository...")
            if not os.path.exists(frigate_path):
                QMessageBox.warning(self, "Cannot Update", 
                                  "❌ No Frigate repository found to update.\n\n"
                                  "Please use 'Clone Fresh Repository' instead to download Frigate for the first time.")
                self.install_progress.append("❌ Update aborted: No repository found")
                return
            
            git_dir = os.path.join(frigate_path, '.git')
            if not os.path.exists(git_dir):
                QMessageBox.warning(self, "Cannot Update", 
                                  "❌ Frigate directory exists but is not a git repository.\n\n"
                                  "Please use 'Clone Fresh Repository' instead to fix this issue.")
                self.install_progress.append("❌ Update aborted: Invalid repository")
                return
            
            self.install_progress.append("✅ Valid repository found, proceeding with update...")
        
        # Disable buttons during operation
        if hasattr(self, 'clone_frigate_btn'):
            self.clone_frigate_btn.setEnabled(False)
        if hasattr(self, 'update_frigate_btn'):
            self.update_frigate_btn.setEnabled(False)
        
        # Start the worker
        self.worker = InstallWorker(self.script_dir, action_type)
        self.worker.progress.connect(self.handle_install_progress)
        self.worker.finished.connect(self.on_install_finished)
        self.worker.start()
    
    def handle_install_progress(self, message):
        """Handle progress messages from install worker, with special handling for config file updates"""
        if message == "UPDATE_CONFIG_MTIME":
            # Special signal to update config file mtime after creating default config
            # This prevents the reload popup when we automatically create the config
            config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
            if os.path.exists(config_path):
                try:
                    self.config_file_mtime = os.path.getmtime(config_path)
                except Exception:
                    pass  # Silently handle any errors
        else:
            # Normal progress message, append to log
            self.install_progress.append(message)
    
    def on_install_finished(self, success):
        # Re-enable buttons
        if hasattr(self, 'clone_frigate_btn'):
            self.clone_frigate_btn.setEnabled(True)
        if hasattr(self, 'update_frigate_btn'):
            self.update_frigate_btn.setEnabled(True)
        
        if success:
            self.install_progress.append("🎉 Operation completed successfully!")
            QMessageBox.information(self, "Success", 
                                  "✅ Setup completed successfully!\n\n"
                                  "You can now proceed to the next steps or configure Frigate.")
        else:
            self.install_progress.append("💡 Please check the error messages above and try again.")
            QMessageBox.warning(self, "Error", 
                              "❌ Setup failed. Please check the progress log for details.\n\n"
                              "Common issues:\n"
                              "• Missing dependencies (git, python3, docker)\n"
                              "• Network connectivity problems\n"
                              "• Permission issues")
        
        # Refresh status displays
        self.check_status()
        self.check_repo_status()
        if hasattr(self, 'step2_guidance'):
            self.update_step2_guidance()

    def set_docker_buttons_enabled(self, enabled, keep_stop_enabled=False):
        """Enable or disable Docker operation buttons to prevent conflicts
        
        Args:
            enabled (bool): Whether to enable/disable buttons
            keep_stop_enabled (bool): If True, keeps the Stop button enabled even when others are disabled
        """
        # Disable/enable all Docker operation buttons
        if hasattr(self, 'docker_start_btn'):
            self.docker_start_btn.setEnabled(enabled)
        if hasattr(self, 'docker_stop_btn'):
            # Keep stop button enabled if requested, or follow the general enabled state
            self.docker_stop_btn.setEnabled(enabled or keep_stop_enabled)
        if hasattr(self, 'docker_restart_btn'):
            # Smart enable for restart: only enable if operation is enabled AND container exists
            if enabled:
                self.docker_restart_btn.setEnabled(self._check_container_exists_sync())
            else:
                self.docker_restart_btn.setEnabled(False)
        if hasattr(self, 'docker_rebuild_btn'):
            self.docker_rebuild_btn.setEnabled(enabled)
        if hasattr(self, 'docker_remove_btn'):
            self.docker_remove_btn.setEnabled(enabled)
        
        # Note: Web UI button is intentionally NOT disabled as it's just opening a URL
        # Users should be able to check the web interface even during operations

        # Update status indicator if it exists
        if hasattr(self, 'operation_status_label'):
            if enabled:
                self.operation_status_label.setText("🟢 Ready - All operations available")
                self.operation_status_label.setStyleSheet("""
                    QLabel {
                        background: #e8f4f0;
                        color: #2d5a4a;
                        padding: 8px;
                        border-radius: 6px;
                        font-size: 14px;
                        font-weight: bold;
                        margin: 4px 0px;
                    }
                """)
            else:
                if keep_stop_enabled:
                    self.operation_status_label.setText("🟡 Operation in progress - Stop button remains available")
                    self.operation_status_label.setStyleSheet("""
                        QLabel {
                            background: #fef3c7;
                            color: #92400e;
                            padding: 8px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                            margin: 4px 0px;
                        }
                    """)
                else:
                    self.operation_status_label.setText("🔴 Operation in progress - buttons disabled")
                    self.operation_status_label.setStyleSheet("""
                        QLabel {
                            background: #fbeaea;
                            color: #6b3737;
                            padding: 8px;
                            border-radius: 6px;
                            font-size: 14px;
                            font-weight: bold;
                            margin: 4px 0px;
                        }
                    """)

    def show_first_time_startup_info_if_needed(self):
        """Show first-time startup info only if this is the first time starting Frigate"""
        try:
            # Check if we've shown this dialog before by looking for a flag file
            first_start_flag = os.path.join(self.script_dir, '.frigate_first_start_shown')
            
            # Also check if Frigate container exists (if it exists, probably not first time)
            container_exists = self._check_container_exists_sync()
            
            # Only show dialog if:
            # 1. We haven't shown it before (.frigate_first_start_shown doesn't exist)
            # 2. AND no Frigate container exists (truly first time)
            if not os.path.exists(first_start_flag) and not container_exists:
                self.show_first_time_startup_info()
                # Create flag file to prevent showing again
                try:
                    with open(first_start_flag, 'w') as f:
                        f.write("First start dialog shown")
                except Exception as e:
                    print(f"Could not create first start flag: {e}")
                    
        except Exception as e:
            print(f"Error checking first-time startup status: {e}")
            # On error, don't show the dialog to be safe

    def _check_container_exists_sync(self):
        """Synchronously check if Frigate container exists"""
        try:
            result = subprocess.run(['docker', 'ps', '-a', '--filter', 'name=frigate', '--format', '{{.Names}}'], 
                                  capture_output=True, text=True, timeout=10)
            return 'frigate' in result.stdout
        except Exception:
            return False

    def show_first_time_startup_info(self):
        """Show information dialog about first-time Frigate startup duration"""
        info_dialog = QDialog(self)
        info_dialog.setWindowTitle("Starting Frigate")
        info_dialog.setFixedSize(480, 320)
        info_dialog.setModal(True)
        
        # Create layout
        layout = QVBoxLayout(info_dialog)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Icon and title
        title_layout = QHBoxLayout()
        
        # Icon label
        icon_label = QLabel("🚀")
        icon_label.setStyleSheet("font-size: 32px;")
        title_layout.addWidget(icon_label)
        
        # Title
        title_label = QLabel("Starting Frigate...")
        title_label.setStyleSheet("""
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            font-weight: 700;
            color: #0694a2;
            margin-left: 10px;
        """)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        layout.addLayout(title_layout)
        
        # Info text
        info_text = QLabel(
            "⏰ <b>First-time startup may take 3-5 minutes</b><br><br>"
            "You'll see <b>\"🔨 Building Image\"</b> in the button - this is normal and expected."
        )
        info_text.setTextFormat(Qt.RichText)
        info_text.setStyleSheet("""
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 14px;
            color: #2d3748;
            line-height: 1.5;
            padding: 15px;
            background: #f0f9ff;
            border-radius: 8px;
            border-left: 4px solid #0694a2;
        """)
        info_text.setWordWrap(True)
        layout.addWidget(info_text)
        
        # Button
        got_it_btn = QPushButton("Got It, Let's Start!")
        got_it_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0694a2, stop: 1 #0f766e);
                color: white;
                border: none;
                border-radius: 6px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                font-weight: 600;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0891b2, stop: 1 #164e63);
            }
        """)
        got_it_btn.clicked.connect(info_dialog.accept)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(got_it_btn)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        # Show dialog with modal overlay
        self.show_dialog(info_dialog)

    def get_operation_status_message(self, enabled, keep_stop_enabled=False):
        """Get a user-friendly message about button states"""
        if enabled:
            return "🔓 All Docker operation buttons are now available"
        else:
            if keep_stop_enabled:
                return "🔒 Docker operation buttons disabled to prevent conflicts - Stop button remains available for emergency use"
            else:
                return "🔒 Docker operation buttons disabled to prevent conflicts - please wait for current operation to complete"
            
    def docker_action(self, action):
        # Check if application is still initializing
        if self.is_initializing:
            QMessageBox.information(
                self, "Please Wait", 
                "The application is still initializing. Please wait for the initialization to complete.",
                QMessageBox.Ok
            )
            return
            
        # PREVENT MULTIPLE CONCURRENT OPERATIONS
        if hasattr(self, 'docker_worker') and self.docker_worker is not None:
            if self.docker_worker.isRunning():
                if hasattr(self, 'docker_progress'):
                    self.docker_progress.append("⚠️ Another Docker operation is already in progress!")
                    self.docker_progress.append("Please wait for the current operation to complete, or use Stop to cancel it.")
                else:
                    QMessageBox.information(self, "Operation in Progress", 
                                          "Another Docker operation is already in progress!\n"
                                          "Please wait for it to complete.")
                return
            else:
                # Clean up finished worker
                try:
                    self.docker_worker.deleteLater()
                except:
                    pass
                self.docker_worker = None

        # Clear progress and show initial message
        if hasattr(self, 'docker_progress'):
            self.docker_progress.clear()
        
        # Store current action for completion message
        self.current_docker_action = action
        
        # Show first-time startup information dialog for start action (only on first time)
        if action == 'start':
            self.show_first_time_startup_info_if_needed()
        
        action_messages = {
            'start': "▶️ Initiating Frigate container start...",
            'stop': "⏹️ Initiating Frigate container stop...",
            'restart': "🔄 Initiating Frigate container restart...",
            'rebuild': "🔨 Initiating complete Frigate rebuild...",
            'remove': "🗑️ Initiating Frigate container removal..."
        }
        
        if hasattr(self, 'docker_progress'):
            self.docker_progress.append(action_messages.get(action, f"Starting {action} operation..."))
            self.docker_progress.append("=" * 50)  # Visual separator
        
        # DISABLE BUTTONS TO PREVENT CONFLICTS
        # For non-stop operations, keep the Stop button enabled for emergency use
        keep_stop_enabled = action != 'stop'
        self.set_docker_buttons_enabled(False, keep_stop_enabled=keep_stop_enabled)
        
        # Also disable Section 4 control buttons during operation
        if hasattr(self, 'launch_monitor_widget'):
            if hasattr(self.launch_monitor_widget, 'start_btn'):
                self.launch_monitor_widget.start_btn.setEnabled(False)
            if hasattr(self.launch_monitor_widget, 'stop_btn'):
                self.launch_monitor_widget.stop_btn.setEnabled(keep_stop_enabled)
            if hasattr(self.launch_monitor_widget, 'restart_btn'):
                self.launch_monitor_widget.restart_btn.setEnabled(False)
        
        # Also disable PreConfigured Box buttons during operation
        if hasattr(self, 'preconfigured_start_btn'):
            self.preconfigured_start_btn.setEnabled(False)
        if hasattr(self, 'preconfigured_stop_btn'):
            # For stop operations, disable the stop button completely
            # For other operations, keep stop enabled for emergency use
            self.preconfigured_stop_btn.setEnabled(keep_stop_enabled)
            
        if hasattr(self, 'docker_progress'):
            self.docker_progress.append(self.get_operation_status_message(False, keep_stop_enabled=keep_stop_enabled))
        
        # Show confirmation for destructive actions
        if action in ['rebuild', 'remove']:
            action_names = {
                'rebuild': 'rebuild the Frigate container completely',
                'remove': 'stop and remove the Frigate container'
            }
            
            reply = self.show_message_box(
                QMessageBox.Question, "Confirm Action", 
                f"Are you sure you want to {action_names[action]}?\n\n"
                f"This action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                if hasattr(self, 'docker_progress'):
                    self.docker_progress.append("❌ Operation cancelled by user")
                # RE-ENABLE BUTTONS IF USER CANCELS
                self.set_docker_buttons_enabled(True)
                # Re-enable Section 4 control buttons
                if hasattr(self, 'launch_monitor_widget'):
                    if hasattr(self.launch_monitor_widget, 'start_btn'):
                        self.launch_monitor_widget.start_btn.setEnabled(True)
                    if hasattr(self.launch_monitor_widget, 'stop_btn'):
                        self.launch_monitor_widget.stop_btn.setEnabled(True)
                    if hasattr(self.launch_monitor_widget, 'restart_btn'):
                        self.launch_monitor_widget.restart_btn.setEnabled(True)
                # Re-enable PreConfigured Box buttons
                if hasattr(self, 'preconfigured_start_btn'):
                    self.preconfigured_start_btn.setEnabled(True)
                if hasattr(self, 'preconfigured_stop_btn'):
                    self.preconfigured_stop_btn.setEnabled(True)
                if hasattr(self, 'docker_progress'):
                    self.docker_progress.append(self.get_operation_status_message(True))
                return
            else:
                # User confirmed - make sure buttons stay disabled
                # Re-disable the buttons that might have been re-enabled by the dialog
                self.set_docker_buttons_enabled(False, keep_stop_enabled=keep_stop_enabled)
                # Re-disable Section 4 control buttons
                if hasattr(self, 'launch_monitor_widget'):
                    if hasattr(self.launch_monitor_widget, 'start_btn'):
                        self.launch_monitor_widget.start_btn.setEnabled(False)
                    if hasattr(self.launch_monitor_widget, 'stop_btn'):
                        self.launch_monitor_widget.stop_btn.setEnabled(keep_stop_enabled)
                    if hasattr(self.launch_monitor_widget, 'restart_btn'):
                        self.launch_monitor_widget.restart_btn.setEnabled(False)
                # Re-disable PreConfigured Box buttons
                if hasattr(self, 'preconfigured_start_btn'):
                    self.preconfigured_start_btn.setEnabled(False)
                if hasattr(self, 'preconfigured_stop_btn'):
                    self.preconfigured_stop_btn.setEnabled(keep_stop_enabled)
        
        # Create and start the worker
        self.docker_worker = DockerWorker(self.script_dir, action)
        self.docker_worker.progress.connect(self._append_docker_progress)
        self.docker_worker.progress.connect(self.on_docker_progress_for_button)  # Connect button updates
        self.docker_worker.finished.connect(self.on_docker_finished)
        
        # Update button state based on action - simplified to 3 states only
        if action == 'start' or action == 'rebuild':
            self.update_preconfigured_button_state("starting")  # Start with "Starting Frigate"
        elif action == 'remove':
            # For remove action (stop+remove), show stopping state
            self.update_preconfigured_button_state("stopping")
            
        self.docker_worker.start()

    def update_preconfigured_button_state(self, state, operation_text=""):
        """Update the preconfigured Start/Stop Frigate button states with animation"""
        if not hasattr(self, 'preconfigured_start_btn'):
            return
            
        self.button_operation_state = state
        
        if state == "idle":
            self.button_animation_timer.stop()
            self.preconfigured_start_btn.setText("▶️ Start Frigate")
            self.preconfigured_start_btn.setStyleSheet("")  # Reset to default
            self.preconfigured_start_btn.setEnabled(True)
            
            # Reset stop button to default state
            if hasattr(self, 'preconfigured_stop_btn'):
                self.preconfigured_stop_btn.setText("⏹️ Stop")
                self.preconfigured_stop_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #f87171, stop:1 #ef4444);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 14px 16px;
                        font-weight: 600;
                        font-size: 14px;
                        font-family: 'Segoe UI', 'Inter', sans-serif;
                    }
                    QPushButton:hover:enabled {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #fca5a5, stop:1 #f87171);
                    }
                    QPushButton:pressed {
                        background: #dc2626;
                    }
                    QPushButton:disabled {
                        background: #a0aec0;
                        color: #718096;
                    }
                """)
                self.preconfigured_stop_btn.setEnabled(False)
            
        elif state == "building":
            self.button_base_text = "🔨 Building Image"
            self.button_animation_dots = 0
            self.preconfigured_start_btn.setEnabled(False)
            self.preconfigured_start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #ff9800, stop:1 #f57c00);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 14px 16px;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                }
            """)
            self.button_animation_timer.start(500)  # Update every 500ms
            
        elif state == "starting":
            self.button_base_text = "🚀 Starting Frigate"
            self.button_animation_dots = 0
            self.preconfigured_start_btn.setEnabled(False)
            self.preconfigured_start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #2196f3, stop:1 #1976d2);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 14px 16px;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                }
            """)
            self.button_animation_timer.start(500)
            
        elif state == "starting_container":
            self.button_base_text = "🚀 Starting Container"
            self.button_animation_dots = 0
            self.preconfigured_start_btn.setEnabled(False)
            self.preconfigured_start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #4caf50, stop:1 #388e3c);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 14px 16px;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                }
            """)
            self.button_animation_timer.start(500)
            
        elif state == "stopping":
            self.button_base_text = "🛑 Stopping"
            self.button_animation_dots = 0
            self.preconfigured_start_btn.setEnabled(False)
            
            # Update stop button state during stopping
            if hasattr(self, 'preconfigured_stop_btn'):
                self.stop_button_base_text = "🛑 Stopping"
                self.preconfigured_stop_btn.setEnabled(False)
                self.preconfigured_stop_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #ff5722, stop:1 #d84315);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 14px 16px;
                        font-weight: 600;
                        font-size: 14px;
                        font-family: 'Segoe UI', 'Inter', sans-serif;
                    }
                """)
            self.button_animation_timer.start(500)
            
        elif state == "running":
            self.button_animation_timer.stop()
            self.preconfigured_start_btn.setText("✅ Frigate Running")
            self.preconfigured_start_btn.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                        stop:0 #4caf50, stop:1 #388e3c);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 14px 16px;
                    font-weight: 600;
                    font-size: 14px;
                    font-family: 'Segoe UI', 'Inter', sans-serif;
                }
            """)
            self.preconfigured_start_btn.setEnabled(False)
            
            # Enable stop button when running
            if hasattr(self, 'preconfigured_stop_btn'):
                self.preconfigured_stop_btn.setText("⏹️ Stop")
                self.preconfigured_stop_btn.setEnabled(True)
                
        elif state == "stopped":
            self.button_animation_timer.stop()
            self.preconfigured_start_btn.setText("▶️ Start Frigate")
            self.preconfigured_start_btn.setStyleSheet("")  # Reset to default
            self.preconfigured_start_btn.setEnabled(True)
            
            # Update stop button to stopped state
            if hasattr(self, 'preconfigured_stop_btn'):
                self.preconfigured_stop_btn.setText("✅ Stopped")
                self.preconfigured_stop_btn.setStyleSheet("""
                    QPushButton {
                        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                            stop:0 #6c757d, stop:1 #5a6268);
                        color: white;
                        border: none;
                        border-radius: 8px;
                        padding: 14px 16px;
                        font-weight: 600;
                        font-size: 14px;
                        font-family: 'Segoe UI', 'Inter', sans-serif;
                    }
                """)
                self.preconfigured_stop_btn.setEnabled(False)

    def update_button_animation(self):
        """Update button text with animated dots"""
        if not hasattr(self, 'preconfigured_start_btn') or self.button_operation_state == "idle":
            return
            
        # Cycle through different numbers of dots (0, 1, 2, 3, then repeat)
        self.button_animation_dots = (self.button_animation_dots + 1) % 4
        dots = "." * self.button_animation_dots
        
        # Add padding spaces to keep button width consistent
        padding = "   " if self.button_animation_dots == 0 else "  " if self.button_animation_dots == 1 else " " if self.button_animation_dots == 2 else ""
        
        # Update start button animation
        if hasattr(self, 'button_base_text'):
            animated_text = f"{self.button_base_text}{dots}{padding}"
            self.preconfigured_start_btn.setText(animated_text)
        
        # Update stop button animation during stopping state
        if (self.button_operation_state == "stopping" and 
            hasattr(self, 'preconfigured_stop_btn') and 
            hasattr(self, 'stop_button_base_text')):
            stop_animated_text = f"{self.stop_button_base_text}{dots}{padding}"
            self.preconfigured_stop_btn.setText(stop_animated_text)

    def on_docker_progress_for_button(self, text):
        """Handle docker progress updates for button state enhancement - simplified to only show 3 states"""
        if not hasattr(self, 'preconfigured_start_btn'):
            return
            
        # Only map specific progress messages to button states - ignore errors and warnings
        text_lower = text.lower()
        
        # Progression: Starting Frigate -> Building Image -> Starting Container -> Running
        if ("building" in text_lower or "build" in text_lower) and "building image" not in text_lower:
            # Only switch to building if not already in that state
            if hasattr(self, 'button_operation_state') and self.button_operation_state != "building":
                self.update_preconfigured_button_state("building")
        elif ("starting" in text_lower or "creating" in text_lower) and "starting container" not in text_lower:
            # Only switch to starting container if currently building
            if hasattr(self, 'button_operation_state') and self.button_operation_state in ["starting", "building", "starting_container"]:
                self.update_preconfigured_button_state("starting_container")
        elif "started successfully" in text_lower or "frigate is now running" in text_lower:
            self.update_preconfigured_button_state("running")
        # Removed error state handling - keep current state even if errors/warnings occur

    
    def _append_docker_progress(self, text):
        """Append text to docker progress with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Don't add timestamp to separator lines or empty lines
        if text.strip() and not text.startswith("="):
            formatted_text = f"[{timestamp}] {text}"
        else:
            formatted_text = text
            
        if hasattr(self, 'docker_progress'):
            self.docker_progress.append(formatted_text)
        else:
            # Print to console if no docker_progress widget available
            print(f"Docker Progress: {formatted_text}")
    
    def on_docker_finished(self, success):
        # Update button state based on completion - no error state, just reset to idle
        if hasattr(self, 'current_docker_action'):
            action = self.current_docker_action
            if action == 'start':
                if success:
                    self.update_preconfigured_button_state("running")
                else:
                    # Even on failure, just reset to idle instead of showing error
                    self.update_preconfigured_button_state("idle")
            else:
                # For other actions, reset to idle state
                self.update_preconfigured_button_state("idle")
        
        # Add completion separator
        if hasattr(self, 'docker_progress'):
            self.docker_progress.append("=" * 50)
        
        if success:
            # Check what operation was performed and provide specific messages
            if hasattr(self, 'current_docker_action'):
                if self.current_docker_action == 'start':
                    if hasattr(self, 'docker_progress'):
                        self.docker_progress.append("🎉 Frigate Docker container started successfully!")
                    self.show_message_box(QMessageBox.Information, "Success", "Frigate Docker container started successfully!\n\nOpen Frigate Web UI to monitor.")
                elif self.current_docker_action == 'stop':
                    if hasattr(self, 'docker_progress'):
                        self.docker_progress.append("🎉 Frigate Docker container stopped successfully!")
                    self.show_message_box(QMessageBox.Information, "Success", "Frigate Docker container stopped successfully!")
                elif self.current_docker_action == 'restart':
                    if hasattr(self, 'docker_progress'):
                        self.docker_progress.append("🎉 Frigate Docker container restarted successfully!")
                    self.show_message_box(QMessageBox.Information, "Success", "Frigate Docker container restarted successfully!\n\nOpen Frigate Web UI to monitor.")
                elif self.current_docker_action == 'rebuild':
                    if hasattr(self, 'docker_progress'):
                        self.docker_progress.append("🎉 Frigate Docker container rebuilt successfully!")
                    self.show_message_box(QMessageBox.Information, "Success", "Frigate Docker container rebuilt successfully!")
                elif self.current_docker_action == 'remove':
                    if hasattr(self, 'docker_progress'):
                        self.docker_progress.append("🎉 Frigate Docker container stopped and removed successfully!")
                    self.show_message_box(QMessageBox.Information, "Success", "Frigate Docker container stopped and removed successfully!")
                    # Set stopped state for buttons
                    if hasattr(self, 'preconfigured_start_btn'):
                        QTimer.singleShot(500, lambda: self.update_preconfigured_button_state("stopped"))
                else:
                    # Fallback for unknown operations
                    if hasattr(self, 'docker_progress'):
                        self.docker_progress.append("🎉 Docker operation completed successfully!")
                    self.show_message_box(QMessageBox.Information, "Success", "Docker operation completed successfully!")
            else:
                # Fallback if no action stored
                if hasattr(self, 'docker_progress'):
                    self.docker_progress.append("🎉 Docker operation completed successfully!")
                self.show_message_box(QMessageBox.Information, "Success", "Docker operation completed successfully!")
        else:
            if hasattr(self, 'docker_progress'):
                self.docker_progress.append("❌ Docker operation failed. Check the logs above for details.")
            self.show_message_box(QMessageBox.Warning, "Error", "Docker operation failed. Please check the logs.")
        
        # RE-ENABLE ALL BUTTONS AFTER OPERATION COMPLETES
        self.set_docker_buttons_enabled(True)
        
        # Re-enable Section 4 control buttons
        if hasattr(self, 'launch_monitor_widget'):
            if hasattr(self.launch_monitor_widget, 'start_btn'):
                self.launch_monitor_widget.start_btn.setEnabled(True)
            if hasattr(self.launch_monitor_widget, 'stop_btn'):
                self.launch_monitor_widget.stop_btn.setEnabled(True)
            if hasattr(self.launch_monitor_widget, 'restart_btn'):
                self.launch_monitor_widget.restart_btn.setEnabled(True)
        
        # Re-enable PreConfigured Box buttons and update their states
        if hasattr(self, 'preconfigured_start_btn'):
            self.preconfigured_start_btn.setEnabled(True)
        
        if hasattr(self, 'docker_progress'):
            self.docker_progress.append(self.get_operation_status_message(True))
        
        # Update PreConfigured Box button states after operation
        if hasattr(self, 'preconfigured_start_btn') and hasattr(self, 'preconfigured_stop_btn'):
            QTimer.singleShot(1000, self.update_preconfigured_button_states)  # Update after 1 second delay
        
        # CLEAN UP WORKER THREAD
        if hasattr(self, 'docker_worker') and self.docker_worker is not None:
            try:
                self.docker_worker.deleteLater()
            except:
                pass
            self.docker_worker = None
        
        # Refresh the status
        self.check_status()
    
    def resizeEvent(self, event):
        """Handle window resize events to update responsive layouts"""
        super().resizeEvent(event)
        
        # Update modal overlay size to match new window size
        if hasattr(self, 'modal_overlay'):
            self.modal_overlay.setGeometry(self.rect())
        
        # Only update layouts if not in initialization phase
        if not getattr(self, 'is_initializing', True):
            # Use QTimer to defer the update and avoid blocking during resize
            QTimer.singleShot(50, self.update_responsive_layouts)
    
    def update_responsive_layouts(self):
        """Update responsive container layouts based on current window size"""
        if not hasattr(self, 'responsive_containers'):
            return
            
        window_size = self.size()
        # Calculate new responsive 10% padding with minimum values
        new_horizontal = max(20, int(window_size.width() * 0.05))   # 5% each side = 10% total, min 20px
        new_vertical = max(15, int(window_size.height() * 0.05))    # 5% each side = 10% total, min 15px
        
        # Update all registered responsive containers
        for tab_name, layout in self.responsive_containers:
            if layout and not layout.parent().isHidden():  # Only update visible layouts
                layout.setContentsMargins(new_horizontal, new_vertical, new_horizontal, new_vertical)
    
    def changeEvent(self, event):
        """Handle window state changes (minimize, maximize, restore)"""
        super().changeEvent(event)
        
        # If window is restored from minimized state or window state changes
        if event.type() == QEvent.WindowStateChange:
            # Update layouts after a short delay to ensure window is fully restored
            if not self.isMinimized():
                QTimer.singleShot(100, self.update_responsive_layouts)
    
    def showEvent(self, event):
        """Handle window show events"""
        super().showEvent(event)
        
        # Update layouts when window is shown
        if not getattr(self, 'is_initializing', True):
            QTimer.singleShot(50, self.update_responsive_layouts)
    
    def closeEvent(self, event):
        """Handle application close event - clean up worker threads"""
        try:
            # Stop and clean up docker worker thread
            if hasattr(self, 'docker_worker') and self.docker_worker is not None:
                if self.docker_worker.isRunning():
                    self.docker_worker.terminate()  # Force terminate if still running
                    self.docker_worker.wait(3000)  # Wait up to 3 seconds for termination
                try:
                    self.docker_worker.deleteLater()
                except:
                    pass
                self.docker_worker = None
            
            # Stop all timers
            if hasattr(self, 'status_timer'):
                self.status_timer.stop()
            if hasattr(self, 'config_watcher_timer'):
                self.config_watcher_timer.stop()
            if hasattr(self, 'logs_timer'):
                self.logs_timer.stop()
            if hasattr(self, 'preconfigured_refresh_timer'):
                self.preconfigured_refresh_timer.stop()
                
        except Exception as e:
            print(f"Error during cleanup: {e}")
        
        # Accept the close event
        event.accept()
    
    def open_web_ui(self):
        subprocess.Popen(['xdg-open', 'http://localhost:5000'])
    
    def open_config(self):
        """Open the advanced configuration GUI"""
        # Check if application is still initializing
        if self.is_initializing:
            self.show_message_box(
                QMessageBox.Information, "Please Wait", 
                "The application is still initializing. Please wait for the initialization to complete."
            )
            return
            
        if ConfigGUI is None:
            self.show_message_box(
                QMessageBox.Critical, 'Advanced Config GUI Unavailable',
                'The Advanced Configuration GUI could not be loaded.\n'
                'Please ensure advanced_config_gui.py is available in the same directory.'
            )
            return
        
        try:
            # Create and show the advanced config GUI (same pattern as simple camera GUI)
            self.config_gui = ConfigGUI()
            # Pass reference to this launcher so config GUI can suppress popups if needed
            self.config_gui.launcher_parent = self
            # Show with overlay
            self.show_external_gui(self.config_gui)
        except Exception as e:
            self.show_message_box(
                QMessageBox.Critical, 'Error Opening Config GUI',
                f'Could not open the Advanced Configuration GUI:\n{str(e)}'
            )
    
    def edit_config_manual(self):
        config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
        subprocess.Popen(['xdg-open', config_path])
    
    def save_config(self):
        """Save the configuration from the editor to the config file"""
        config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
        
        try:
            # Ensure the config directory exists
            config_dir = os.path.dirname(config_path)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            # Get content from the text editor
            content = self.config_preview.toPlainText()
            
            # Basic YAML validation (optional - just check if it's not empty)
            if not content.strip():
                reply = QMessageBox.question(
                    self, "Empty Configuration", 
                    "The configuration is empty. Are you sure you want to save this?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            # Create backup of existing config
            if os.path.exists(config_path):
                backup_path = config_path + '.backup'
                import shutil
                shutil.copy2(config_path, backup_path)
            
            # Save the new configuration
            with open(config_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Update the tracked modification time after saving
            self.config_file_mtime = os.path.getmtime(config_path)
            
            QMessageBox.information(
                self, "Configuration Saved", 
                f"✅ Configuration saved successfully to:\n{config_path}\n\n"
                "A backup of the previous configuration was created."
            )
            
            # Update the config status in overview
            self.check_status()
            
        except Exception as e:
            QMessageBox.warning(
                self, "Save Error", 
                f"❌ Failed to save configuration:\n{str(e)}\n\n"
                "Please check file permissions and try again."
            )
    
    def toggle_config_edit_mode(self):
        """Toggle between read-only and edit mode for configuration editor"""
        if self.config_is_read_only:
            # Switch to edit mode
            self.config_preview.setReadOnly(False)
            self.config_is_read_only = False
            self.edit_config_btn.setText("👁️ View")
            self.edit_config_btn.setToolTip("Switch to read-only view mode")
            self.save_config_btn.setEnabled(True)
            
            # Update styling for edit mode
            self.config_preview.setStyleSheet("""
                QTextEdit {
                    background: #ffffff;
                    border: 2px solid #28a745;
                    border-radius: 6px;
                    font-family: 'Consolas', 'Monaco', 'Liberation Mono', monospace;
                    font-size: 16px;
                    color: #2d3748;
                    padding: 12px;
                    line-height: 1.5;
                }
            """)
        else:
            # Switch to read-only mode
            self.config_preview.setReadOnly(True)
            self.config_is_read_only = True
            self.edit_config_btn.setText("✏️ Edit")
            self.edit_config_btn.setToolTip("Switch to edit mode to modify the configuration")
            self.save_config_btn.setEnabled(False)
            
            # Update styling for read-only mode
            self.config_preview.setStyleSheet("""
                QTextEdit {
                    background: #f8f9fa;
                    border: 1px solid #cbd5e0;
                    border-radius: 6px;
                    font-family: 'Consolas', 'Monaco', 'Liberation Mono', monospace;
                    font-size: 16px;
                    color: #495057;
                    padding: 12px;
                    line-height: 1.5;
                }
            """)
    
    def check_prerequisites(self):
        """Check basic prerequisites - only if widgets exist (for backward compatibility)"""
        # This method is kept for compatibility with existing calls
        # The main prerequisite checking is now in the Prerequisites tab
        if hasattr(self, 'git_check') and hasattr(self, 'python_check') and hasattr(self, 'docker_check'):
            tools = {'git': self.git_check, 'python3': self.python_check, 'docker': self.docker_check}
            
            for tool, label in tools.items():
                result = subprocess.run(['which', tool], capture_output=True)
                if result.returncode == 0:
                    label.setText("✅ Installed")
                    label.setStyleSheet("background: #e8f4f0; color: #2d5a4a;")
                else:
                    label.setText("❌ Missing")
                    label.setStyleSheet("background: #fbeaea; color: #6b3737;")
    
    def load_config_preview(self):
        config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.config_preview.setPlainText(content)
                # Update the tracked modification time
                self.config_file_mtime = os.path.getmtime(config_path)
            except Exception as e:
                self.config_preview.setPlainText(f"Error loading configuration file:\n{str(e)}")
        else:
            # Show a default configuration template if no config exists
            default_config = """# Frigate Configuration
# This is a basic template. Customize it for your cameras and setup.

mqtt:
  enabled: False

detectors:
  memx0:
    type: memryx
    device: PCIe:0

model:
  model_type: yolo-generic
  width: 320
  height: 320
  input_tensor: nchw
  input_dtype: float
  labelmap_path: /labelmap/coco-80.txt

# cameras:
# Add your cameras here
# example_camera:
#   ffmpeg:
#     inputs:
#       - path: rtsp://username:password@camera_ip:554/stream
#         roles:
#           - detect
#   detect:
#     width: 2560
#     height: 1440

cameras:
  cam1:
    ffmpeg:
      inputs:
        - path: 
            rtsp://username:password@camera_ip:554/stream
          roles:
            - detect
    detect:
      width: 2560
      height: 1440
      fps: 5
      enabled: true

    objects:
      track:
        - person
        - car
        - bottle
        - cup

    snapshots:
      enabled: false
      bounding_box: true
      retain:
        default: 0  # Keep snapshots for 2 days
    record:
      enabled: false
      alerts:
        retain:
          days: 0
      detections:
        retain:
          days: 0

version: 0.17-0

# For more configuration options, visit:
# https://docs.frigate.video/configuration/
"""
            self.config_preview.setPlainText(default_config)
            self.config_file_mtime = 0  # No file exists yet
        
        # Ensure read-only state is maintained after reload
        if hasattr(self, 'config_is_read_only') and self.config_is_read_only:
            self.config_preview.setReadOnly(True)
    
    def check_config_file_changes(self):
        """Check if the config file has been modified externally and reload if necessary"""
        # Skip check if popup is suppressed (e.g., when saving from simple camera GUI)
        if self.suppress_config_change_popup:
            return
            
        config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
        
        if os.path.exists(config_path):
            try:
                current_mtime = os.path.getmtime(config_path)
                # If the file has been modified since we last loaded it
                if current_mtime > self.config_file_mtime:
                    # Check if the text editor has unsaved changes
                    with open(config_path, 'r', encoding='utf-8') as f:
                        file_content = f.read()
                    
                    editor_content = self.config_preview.toPlainText()
                    
                    # Only reload if the content is actually different
                    if file_content != editor_content:
                        # Ask user if they want to reload (to avoid losing unsaved changes)
                        reply = QMessageBox.question(
                            self, "Configuration File Changed",
                            "The configuration file has been modified externally.\n"
                            "Do you want to reload it? This will discard any unsaved changes in the editor.",
                            QMessageBox.Yes | QMessageBox.No,
                            QMessageBox.Yes
                        )
                        
                        if reply == QMessageBox.Yes:
                            self.config_preview.setPlainText(file_content)
                            self.config_file_mtime = current_mtime
                        else:
                            # User chose not to reload, update mtime to avoid asking again
                            # until the file changes again
                            self.config_file_mtime = current_mtime
                    else:
                        # Content is the same, just update mtime silently
                        self.config_file_mtime = current_mtime
                        
            except Exception as e:
                # Silently handle errors (file might be temporarily locked during writing)
                pass
        elif self.config_file_mtime > 0:
            # File was deleted externally
            self.config_file_mtime = 0
    
    def refresh_logs(self):
        try:
            # Get recent logs (last 200 lines to show more context)
            result = subprocess.run(['docker', 'logs', '--tail', '200', 'frigate'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                new_text = result.stdout
                current_text = self.logs_display.toPlainText()
                
                # Only update if text has changed
                if new_text != current_text:
                    # Check if this is new content being appended or completely different content
                    if current_text and new_text.startswith(current_text):
                        # New content appended - extract and append only the new part
                        new_part = new_text[len(current_text):]
                        if new_part.strip():  # Only append if there's actual new content
                            # Remove leading newline if present
                            new_part = new_part.lstrip('\n')
                            if new_part:
                                self.logs_display.append(new_part.rstrip('\n'))
                    else:
                        # Completely different content or first load - use setPlainText and force scroll
                        self.logs_display.setPlainText(new_text)
                        # Force scroll to bottom immediately after setPlainText
                        scrollbar = self.logs_display.verticalScrollBar()
                        scrollbar.setValue(scrollbar.maximum())
            else:
                self.logs_display.setPlainText("Unable to fetch logs. Is Frigate container running?")
        except subprocess.FileNotFoundError:
            self.logs_display.setPlainText("Docker not found. Please ensure Docker is installed and running.")
        except Exception as e:
            self.logs_display.setPlainText(f"Error fetching logs: {str(e)}\n\nIs Frigate container running?")
    
    def start_logs_auto_refresh(self):
        """Start automatic logs refresh with 3-second interval"""
        # Start the logs timer immediately
        self.logs_timer.start(3000)  # Refresh every 3 seconds
        # Also refresh immediately to show current logs
        self.refresh_logs()
    
    def update_step2_guidance(self):
        """Update the guidance text for Step 2 based on current repository status"""
        # Only update if the step2_guidance label exists
        if not hasattr(self, 'step2_guidance'):
            return
            
        frigate_path = os.path.join(self.script_dir, 'frigate')
        
        if not os.path.exists(frigate_path):
            # No repository found
            guidance_text = (
                "💡 No Frigate repository found. Choose 'Clone Fresh Repository' to download "
                "Frigate for the first time."
            )
            self.step2_guidance.setText(guidance_text)
            if hasattr(self, 'clone_frigate_btn'):
                self.clone_frigate_btn.setEnabled(True)
            if hasattr(self, 'update_frigate_btn'):
                self.update_frigate_btn.setEnabled(False)
            
        elif not os.path.exists(os.path.join(frigate_path, '.git')):
            # Directory exists but not a git repository
            guidance_text = (
                "⚠️ Frigate directory exists but is not a git repository. "
                "Choose 'Clone Fresh Repository' to fix this issue."
            )
            self.step2_guidance.setText(guidance_text)
            if hasattr(self, 'clone_frigate_btn'):
                self.clone_frigate_btn.setEnabled(True)
            if hasattr(self, 'update_frigate_btn'):
                self.update_frigate_btn.setEnabled(False)
            
        else:
            # Valid git repository exists
            try:
                result = subprocess.run(['git', 'status', '--porcelain'], 
                                      cwd=frigate_path, capture_output=True, text=True)
                if result.returncode == 0:
                    guidance_text = (
                        "✅ Valid Frigate repository found. You can either:\n"
                        "• Use 'Update Existing Repository' to get the latest changes\n"
                        "• Use 'Clone Fresh Repository' to start completely fresh"
                    )
                    self.step2_guidance.setText(guidance_text)
                    if hasattr(self, 'clone_frigate_btn'):
                        self.clone_frigate_btn.setEnabled(True)
                    if hasattr(self, 'update_frigate_btn'):
                        self.update_frigate_btn.setEnabled(True)
                else:
                    guidance_text = (
                        "❌ Git repository appears corrupted. "
                        "Choose 'Clone Fresh Repository' to fix this issue."
                    )
                    self.step2_guidance.setText(guidance_text)
                    if hasattr(self, 'clone_frigate_btn'):
                        self.clone_frigate_btn.setEnabled(True)
                    if hasattr(self, 'update_frigate_btn'):
                        self.update_frigate_btn.setEnabled(False)
            except:
                guidance_text = (
                    "❓ Cannot determine repository status. "
                    "Choose 'Clone Fresh Repository' to be safe."
                )
                self.step2_guidance.setText(guidance_text)
                if hasattr(self, 'clone_frigate_btn'):
                    self.clone_frigate_btn.setEnabled(True)
                if hasattr(self, 'update_frigate_btn'):
                    self.update_frigate_btn.setEnabled(False)

    def check_setup_dependencies(self):
        """Check the Python environment dependencies for Frigate Setup"""
        try:
            # Check Python 3
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.strip()
                self.setup_python_check.setText(f"✅ {version}")
                self.setup_python_check.setStyleSheet("background: #e8f4f0; color: #2d5a4a;")
                self.install_setup_python_btn.setVisible(False)
            else:
                self.setup_python_check.setText("❌ Not Installed")
                self.setup_python_check.setStyleSheet("background: #fbeaea; color: #6b3737;")
                self.install_setup_python_btn.setVisible(True)
            
            # Check Pip
            result = subprocess.run(['python3', '-m', 'pip', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                version = result.stdout.split()[1] if result.stdout else "installed"
                self.setup_pip_check.setText(f"✅ pip {version}")
                self.setup_pip_check.setStyleSheet("background: #e8f4f0; color: #2d5a4a;")
                self.install_setup_pip_btn.setVisible(False)
            else:
                self.setup_pip_check.setText("❌ Not Available")
                self.setup_pip_check.setStyleSheet("background: #fbeaea; color: #6b3737;")
                self.install_setup_pip_btn.setVisible(True)
            
            # Check Virtual Environment
            venv_path = os.path.join(self.script_dir, '.venv')
            if os.path.exists(venv_path) and os.path.exists(os.path.join(venv_path, 'bin', 'python')):
                self.setup_venv_check.setText("✅ Created")
                self.setup_venv_check.setStyleSheet("background: #e8f4f0; color: #2d5a4a;")
                self.install_setup_venv_btn.setVisible(False)
            else:
                self.setup_venv_check.setText("❌ Not Created")
                self.setup_venv_check.setStyleSheet("background: #fbeaea; color: #6b3737;")
                self.install_setup_venv_btn.setVisible(True)
                
        except Exception as e:
            self.install_progress.append(f"❌ Error checking setup dependencies: {str(e)}")
    
    def install_setup_dependency(self, dep_type):
        """Install a setup dependency (python, pip, or venv)"""
        # Disable all install buttons during installation
        self.install_setup_python_btn.setEnabled(False)
        self.install_setup_pip_btn.setEnabled(False)
        self.install_setup_venv_btn.setEnabled(False)
        
        # Clear progress and show starting message
        self.install_progress.clear()
        dep_names = {
            'python': 'Python 3',
            'pip': 'Pip Package Manager',
            'venv': 'Virtual Environment'
        }
        
        self.install_progress.append(f"🚀 Starting {dep_names[dep_type]} setup...")
        
        if dep_type == 'python':
            self._install_python_for_setup()
        elif dep_type == 'pip':
            self._install_pip_for_setup()
        elif dep_type == 'venv':
            self._create_virtual_environment()
    
    def _install_python_for_setup(self):
        """Install Python 3 for setup tab"""
        try:
            self.install_progress.append("📦 Installing Python 3 and related packages...")
            
            # Update package repositories
            self.install_progress.append("🔄 Updating package repositories...")
            subprocess.run(['sudo', 'apt', 'update'], check=True)
            
            # Install Python 3 and related packages
            self.install_progress.append("📥 Installing Python 3, pip, and venv...")
            subprocess.run(['sudo', 'apt', 'install', '-y', 
                           'python3', 'python3-pip', 'python3-venv', 'python3-dev'], check=True)
            
            # Verify installation
            result = subprocess.run(['python3', '--version'], capture_output=True, text=True, check=True)
            version = result.stdout.strip()
            self.install_progress.append(f"✅ Python installed successfully: {version}")
            
            # Re-enable buttons
            self.install_setup_python_btn.setEnabled(True)
            self.install_setup_pip_btn.setEnabled(True)
            self.install_setup_venv_btn.setEnabled(True)
            
            # Refresh checks
            self.check_setup_dependencies()
            
        except subprocess.CalledProcessError as e:
            self.install_progress.append(f"❌ Python installation failed: {str(e)}")
            self.install_setup_python_btn.setEnabled(True)
            self.install_setup_pip_btn.setEnabled(True)
            self.install_setup_venv_btn.setEnabled(True)
    
    def _install_pip_for_setup(self):
        """Install/upgrade pip for setup tab"""
        try:
            self.install_progress.append("📦 Installing/upgrading pip...")
            
            # Check if python3 is available
            result = subprocess.run(['python3', '--version'], capture_output=True)
            if result.returncode != 0:
                self.install_progress.append("❌ Python 3 must be installed first")
                return
            
            # Install/upgrade pip
            self.install_progress.append("📥 Installing pip...")
            subprocess.run(['sudo', 'apt', 'install', '-y', 'python3-pip'], check=True)
            
            # Upgrade pip
            self.install_progress.append("⬆️ Upgrading pip...")
            subprocess.run(['python3', '-m', 'pip', 'install', '--upgrade', '--user', 'pip'], check=True)
            
            # Verify installation
            result = subprocess.run(['python3', '-m', 'pip', '--version'], capture_output=True, text=True, check=True)
            version = result.stdout.split()[1] if result.stdout else "unknown"
            self.install_progress.append(f"✅ Pip installed successfully: version {version}")
            
            # Re-enable buttons
            self.install_setup_python_btn.setEnabled(True)
            self.install_setup_pip_btn.setEnabled(True)
            self.install_setup_venv_btn.setEnabled(True)
            
            # Refresh checks
            self.check_setup_dependencies()
            
        except subprocess.CalledProcessError as e:
            self.install_progress.append(f"❌ Pip installation failed: {str(e)}")
            self.install_setup_python_btn.setEnabled(True)
            self.install_setup_pip_btn.setEnabled(True)
            self.install_setup_venv_btn.setEnabled(True)
    
    def _create_virtual_environment(self):
        """Create virtual environment for setup tab"""
        try:
            venv_path = os.path.join(self.script_dir, '.venv')
            
            # Check if python3 and venv are available
            result = subprocess.run(['python3', '-m', 'venv', '--help'], capture_output=True)
            if result.returncode != 0:
                self.install_progress.append("❌ Python 3 venv module not available. Install python3-venv first.")
                return
            
            # Check if environment already exists and is functional
            if os.path.exists(venv_path):
                venv_python = os.path.join(venv_path, 'bin', 'python')
                if os.path.exists(venv_python):
                    try:
                        # Test if the existing venv works
                        result = subprocess.run([venv_python, '--version'], capture_output=True, timeout=5)
                        if result.returncode == 0:
                            self.install_progress.append("✅ Virtual environment already exists and is functional!")
                            # Re-enable buttons and refresh checks
                            self.install_setup_python_btn.setEnabled(True)
                            self.install_setup_pip_btn.setEnabled(True)
                            self.install_setup_venv_btn.setEnabled(True)
                            self.check_setup_dependencies()
                            return
                    except:
                        pass
            
            self.install_progress.append(f"🏠 Creating virtual environment at: {venv_path}")
            
            # Remove existing venv if it exists but is broken
            if os.path.exists(venv_path):
                self.install_progress.append("🗑️ Removing existing virtual environment...")
                subprocess.run(['rm', '-rf', venv_path], check=True)
            
            # Create new virtual environment
            subprocess.run(['python3', '-m', 'venv', venv_path], check=True)
            
            # Verify creation
            venv_python = os.path.join(venv_path, 'bin', 'python')
            if os.path.exists(venv_python):
                self.install_progress.append("✅ Virtual environment created successfully!")
                
                # Upgrade pip in venv
                self.install_progress.append("⬆️ Upgrading pip in virtual environment...")
                subprocess.run([venv_python, '-m', 'pip', 'install', '--upgrade', 'pip'], check=True)
                
            else:
                raise Exception("Virtual environment creation failed")
            
            # Re-enable buttons
            self.install_setup_python_btn.setEnabled(True)
            self.install_setup_pip_btn.setEnabled(True)
            self.install_setup_venv_btn.setEnabled(True)
            
            # Refresh checks
            self.check_setup_dependencies()
            
        except subprocess.CalledProcessError as e:
            self.install_progress.append(f"❌ Virtual environment creation failed: {str(e)}")
            self.install_setup_python_btn.setEnabled(True)
            self.install_setup_pip_btn.setEnabled(True)
            self.install_setup_venv_btn.setEnabled(True)

    def auto_scroll_prereq_progress(self):
        """Auto-scroll the prerequisites progress text to the bottom when new content is added"""
        # Get the scroll bar of the QTextEdit
        scrollbar = self.prereq_progress.verticalScrollBar()
        # Move to the maximum (bottom) position
        scrollbar.setValue(scrollbar.maximum())
    
    def auto_scroll_install_progress(self):
        """Auto-scroll the setup/install progress text to the bottom when new content is added"""
        scrollbar = self.install_progress.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def auto_scroll_docker_progress(self):
        """Auto-scroll the docker progress text to the bottom when new content is added"""
        scrollbar = self.docker_progress.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def auto_scroll_logs_display(self):
        """Auto-scroll the logs display to the bottom when new content is added"""
        scrollbar = self.logs_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    
    def check_system_prerequisites(self):
        """Check the system-level prerequisites for Frigate"""
        try:
            # Check Git
            result = subprocess.run(['git', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                self.prereq_git_check.setText("✅ Installed")
                self.prereq_git_check.setStyleSheet("background: #e8f4f0; color: #2d5a4a;")
                self.install_git_btn.setVisible(False)
            else:
                self.prereq_git_check.setText("❌ Not Installed")
                self.prereq_git_check.setStyleSheet("background: #fbeaea; color: #6b3737;")
                self.install_git_btn.setVisible(True)
            
            # Check build-essential (for DKMS and other build tools)
            result = subprocess.run(['dpkg', '-l', 'build-essential'], capture_output=True)
            if result.returncode == 0:
                self.prereq_build_check.setText("✅ Installed")
                self.prereq_build_check.setStyleSheet("background: #e8f4f0; color: #2d5a4a;")
                self.install_build_btn.setVisible(False)
            else:
                self.prereq_build_check.setText("❌ Not Installed")
                self.prereq_build_check.setStyleSheet("background: #fbeaea; color: #6b3737;")
                self.install_build_btn.setVisible(True)
            
        except Exception as e:
            self.prereq_progress.append(f"❌ Error checking prerequisites: {str(e)}")
    
    def install_system_prereq(self, install_type):
        """Install a system prerequisite (git, python, or build-tools)"""
        # Get sudo password from user
        install_names = {
            'git': 'Git',
            'build-tools': 'Build Tools'
        }
        
        sudo_password = PasswordDialog.get_sudo_password(self, f"{install_names[install_type]} installation")
        if sudo_password is None:
            self.prereq_progress.append(f"❌ {install_names[install_type]} installation cancelled - password required")
            return
        
        # Disable all install buttons during installation
        self.install_git_btn.setEnabled(False)
        self.install_build_btn.setEnabled(False)
        
        # Clear progress and show starting message
        self.prereq_progress.clear()
        
        self.prereq_progress.append(f"🚀 Starting {install_names[install_type]} installation...")
        
        # Create and start worker thread with password
        self.system_prereq_worker = SystemPrereqInstallWorker(self.script_dir, install_type, sudo_password)
        self.system_prereq_worker.progress.connect(self.prereq_progress.append)
        self.system_prereq_worker.finished.connect(self.on_system_prereq_install_finished)
        self.system_prereq_worker.start()
    
    def on_system_prereq_install_finished(self, success):
        """Handle completion of system prerequisite installation"""
        # Re-enable install buttons
        self.install_git_btn.setEnabled(True)
        self.install_build_btn.setEnabled(True)
        
        if success:
            self.prereq_progress.append("✅ Installation completed successfully!")
            # Refresh the status checks
            self.check_system_prerequisites()
        else:
            self.prereq_progress.append("❌ Installation failed. Please check the error messages above.")
    
    def check_docker_prereq_status(self):
        """Check the Docker installation and service status"""
        try:
            status_lines = []
            docker_installed = False
            docker_accessible = False
            
            # Check if Docker is installed
            result = subprocess.run(['which', 'docker'], capture_output=True, text=True)
            if result.returncode == 0:
                docker_installed = True
                
                # Get Docker version
                try:
                    version_check = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=5)
                    if version_check.returncode == 0:
                        docker_accessible = True
                        version_info = version_check.stdout.strip()
                        status_lines.append(f"✅ {version_info}")
                        
                        # Check Docker service status
                        service_check = subprocess.run(['systemctl', 'is-active', 'docker'], 
                                                     capture_output=True, text=True)
                        if service_check.returncode == 0:
                            status_lines.append("✅ Service: Active")
                        else:
                            status_lines.append("⚠️ Service: Inactive")
                        
                    else:
                        status_lines.append("❌ Docker installed but not accessible")
                        status_lines.append("💡 Try: logout and login again")
                        
                except subprocess.TimeoutExpired:
                    status_lines.append("⏰ Docker not responding")
                    status_lines.append("💡 Try: sudo systemctl restart docker")
            else:
                status_lines.append("❌ Docker not installed")
                status_lines.append("💡 Click 'Install Docker' below")
            
            # Set the status text
            status_text = '\n'.join(status_lines)
            self.prereq_docker_status.setText(status_text)
            
            # Set style based on overall status
            if docker_installed and docker_accessible:
                self.prereq_docker_status.setStyleSheet("background: #e8f4f0; color: #2d5a4a; padding: 8px; border-radius: 6px;")
                self.install_docker_prereq_btn.setVisible(False)
            elif docker_installed:
                self.prereq_docker_status.setStyleSheet("background: #fff3cd; color: #856404; padding: 8px; border-radius: 6px;")
                self.install_docker_prereq_btn.setVisible(False)
            else:
                self.prereq_docker_status.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
                self.install_docker_prereq_btn.setVisible(True)
        
        except Exception as e:
            self.prereq_progress.append(f"❌ Error checking Docker status: {str(e)}")
            self.prereq_docker_status.setText(f"❌ Error checking Docker: {str(e)}")
            self.prereq_docker_status.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
            self.install_docker_prereq_btn.setVisible(True)
    
    def check_memryx_prereq_status(self):
        """Check the MemryX driver and runtime installation status"""
        try:
            # Check if MemryX devices exist
            devices = [d for d in glob.glob("/dev/memx*") if "_feature" not in d]
            device_count = len(devices)
            
            # Helper function to get package version
            def get_package_version(package_name):
                """Get the installed version of a package using apt policy"""
                try:
                    result = subprocess.run(['apt', 'policy', package_name], capture_output=True, text=True)
                    if result.returncode == 0:
                        lines = result.stdout.split('\n')
                        for line in lines:
                            if 'Installed:' in line:
                                version = line.split('Installed:')[1].strip()
                                if version and version != '(none)':
                                    # Extract just the version number (e.g., "2.0.1" from "2.0.1-1ubuntu1")
                                    version_parts = version.split('-')[0].split('+')[0]
                                    return version_parts
                except:
                    pass
                return None
            
            # Check if memx-drivers package is installed
            drivers_result = subprocess.run(['dpkg', '-l', 'memx-drivers'], capture_output=True, text=True)
            drivers_installed = drivers_result.returncode == 0
            drivers_version = get_package_version('memx-drivers') if drivers_installed else None
            
            # Check if mxa-manager package is installed
            manager_result = subprocess.run(['dpkg', '-l', 'mxa-manager'], capture_output=True, text=True)
            manager_installed = manager_result.returncode == 0
            manager_version = get_package_version('mxa-manager') if manager_installed else None
            
            # Check if memx-accl package is installed
            accl_result = subprocess.run(['dpkg', '-l', 'memx-accl'], capture_output=True, text=True)
            accl_installed = accl_result.returncode == 0
            accl_version = get_package_version('memx-accl') if accl_installed else None
            
            if not drivers_installed:
                self.prereq_memryx_status.setText("❌ MemryX drivers not installed")
                self.prereq_memryx_status.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
                self.install_memryx_prereq_btn.setVisible(True)
                self.install_memryx_prereq_btn.setEnabled(True)
                self.restart_system_btn.setVisible(False)  # Hide restart button
                self.memryx_prereq_guidance.setText(
                    "⚠️ MemryX drivers are not installed. Click 'Install MemryX Drivers & Runtime' to "
                    "automatically install the MemryX drivers and runtime components required for hardware acceleration."
                )
                return
            
            if device_count == 0:
                drivers_text = "drivers installed"
                if drivers_version:
                    drivers_text += f" (v{drivers_version})"
                self.prereq_memryx_status.setText(f"⚠️ MemryX {drivers_text} but no devices detected, restart required")
                self.prereq_memryx_status.setStyleSheet("background: #fdf6e3; color: #8b7355; padding: 8px; border-radius: 6px;")
                self.install_memryx_prereq_btn.setVisible(False)
                self.restart_system_btn.setVisible(True)  # Show restart button
                self.memryx_prereq_guidance.setText(
                    "💡 MemryX drivers are installed but no devices are detected.\n"
                    "A system restart is required for the drivers to take effect.\n\n"
                    "Click 'Restart System Now' to restart your computer and activate the MemryX drivers.\n\n"
                    "If devices are still not detected after restart:\n"
                    "• Check that MemryX hardware is properly connected\n"
                    "• Verify hardware compatibility"
                )
                return
            
            if not (manager_installed and accl_installed):
                missing_packages = []
                if not manager_installed:
                    missing_packages.append("mxa-manager")
                if not accl_installed:
                    missing_packages.append("memx-accl")
                
                self.prereq_memryx_status.setText(f"⚠️ Missing runtime packages: {', '.join(missing_packages)}")
                self.prereq_memryx_status.setStyleSheet("background: #fdf6e3; color: #8b7355; padding: 8px; border-radius: 6px;")
                self.install_memryx_prereq_btn.setVisible(True)
                self.install_memryx_prereq_btn.setEnabled(True)
                self.restart_system_btn.setVisible(False)  # Hide restart button
                self.memryx_prereq_guidance.setText(
                    f"💡 MemryX drivers installed but missing runtime packages: {', '.join(missing_packages)}\n"
                    "Click 'Install MemryX Drivers & Runtime' to complete the installation."
                )
                return
            
            # Everything looks good - show version information
            status_text = f"✅ MemryX fully installed and operational\n"
            status_text += f"Devices detected: {device_count}\n"
            
            # Show drivers with version
            drivers_text = "✅ memx-drivers"
            if drivers_version:
                drivers_text += f" (v{drivers_version})"
            status_text += f"Drivers: {drivers_text}\n"
            
            # Show runtime with versions
            runtime_parts = []
            if manager_installed:
                manager_text = "mxa-manager"
                if manager_version:
                    manager_text += f" (v{manager_version})"
                runtime_parts.append(manager_text)
            
            if accl_installed:
                accl_text = "memx-accl"
                if accl_version:
                    accl_text += f" (v{accl_version})"
                runtime_parts.append(accl_text)
            
            status_text += f"Runtime: ✅ {', '.join(runtime_parts)}"
            
            self.prereq_memryx_status.setText(status_text)
            self.prereq_memryx_status.setStyleSheet("background: #e8f4f0; color: #2d5a4a; padding: 8px; border-radius: 6px;")
            self.install_memryx_prereq_btn.setVisible(False)
            self.restart_system_btn.setVisible(False)  # Hide restart button when everything is working
            self.memryx_prereq_guidance.setText(
                "✅ MemryX is ready for use. Hardware acceleration is available for Frigate."
            )
            
        except Exception as e:
            self.prereq_memryx_status.setText(f"❌ Error checking MemryX: {str(e)}")
            self.prereq_memryx_status.setStyleSheet("background: #fbeaea; color: #6b3737; padding: 8px; border-radius: 6px;")
            self.install_memryx_prereq_btn.setVisible(True)
            self.install_memryx_prereq_btn.setEnabled(True)
            self.restart_system_btn.setVisible(False)  # Hide restart button on error
            self.memryx_prereq_guidance.setText(
                "❓ Could not determine MemryX status. You may need to install MemryX drivers."
            )
    
    def install_docker_prereq(self):
        """Install Docker for Prerequisites tab"""
        reply = QMessageBox.question(
            self, "Install Docker", 
            "This will install Docker CE from scratch on your system.\n\n"
            "The installation process will:\n"
            "• Update package repositories\n"
            "• Install Docker CE and related components\n"
            "• Start and enable Docker service\n"
            "• Add your user to the docker group\n\n"
            "This requires sudo privileges and may take several minutes.\n\n"
            "Continue with Docker installation?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Get sudo password from user
        sudo_password = PasswordDialog.get_sudo_password(self, "Docker installation")
        if sudo_password is None:
            self.prereq_progress.append("❌ Docker installation cancelled - password required")
            return
        
        # Disable the install button during operation
        self.install_docker_prereq_btn.setEnabled(False)
        self.install_docker_prereq_btn.setText("🔄 Installing Docker...")
        
        # Start Docker installation worker with password
        self.docker_install_worker = DockerInstallWorker(self.script_dir, sudo_password)
        self.docker_install_worker.progress.connect(self.prereq_progress.append)
        self.docker_install_worker.finished.connect(self.on_docker_prereq_install_finished)
        self.docker_install_worker.start()
    
    def on_docker_prereq_install_finished(self, success):
        """Handle Docker installation completion for Prerequisites tab"""
        # Re-enable the install button
        self.install_docker_prereq_btn.setEnabled(True)
        self.install_docker_prereq_btn.setText("🐳 Install Docker from Scratch")
        
        if success:
            self.prereq_progress.append("🎉 Docker installation completed successfully!")
            QMessageBox.information(
                self, "Docker Installation Complete", 
                "✅ Docker has been installed successfully!\n\n"
                "Please log out and log back in for group permissions to take effect.\n"
                "After re-login, Docker will be ready for use."
            )
        else:
            self.prereq_progress.append("💡 Please check the error messages above.")
            QMessageBox.warning(
                self, "Docker Installation Failed", 
                "❌ Docker installation failed. Please check the progress log for details.\n\n"
                "You may need to install Docker manually or resolve any system issues."
            )
        
        # Refresh Docker status
        self.check_docker_prereq_status()
        self.check_system_prerequisites()
    
    def install_memryx_prereq(self):
        """Install MemryX for Prerequisites tab"""
        reply = QMessageBox.question(
            self, "Install MemryX", 
            "This will install MemryX drivers and runtime on your system.\n\n"
            "The installation process will:\n"
            "• Remove any existing MemryX installations\n"
            "• Install kernel headers and DKMS\n"
            "• Add MemryX repository and GPG key\n"
            "• Install memx-drivers (requires restart after)\n"
            "• Install memx-accl and mxa-manager runtime\n"
            "• Run ARM setup if on ARM architecture\n\n"
            "This requires sudo privileges and may take several minutes.\n"
            "A system restart will be required after driver installation.\n\n"
            "Continue with MemryX installation?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Get sudo password from user
        sudo_password = PasswordDialog.get_sudo_password(self, "MemryX installation")
        if sudo_password is None:
            self.prereq_progress.append("❌ MemryX installation cancelled - password required")
            return
        
        # Disable the install button during operation
        self.install_memryx_prereq_btn.setEnabled(False)
        self.install_memryx_prereq_btn.setText("🔄 Installing MemryX...")
        
        # Start MemryX installation worker with password
        self.memryx_install_worker = MemryXInstallWorker(self.script_dir, sudo_password)
        self.memryx_install_worker.progress.connect(self.prereq_progress.append)
        self.memryx_install_worker.finished.connect(self.on_memryx_prereq_install_finished)
        self.memryx_install_worker.start()
    
    def on_memryx_prereq_install_finished(self, success):
        """Handle MemryX installation completion for Prerequisites tab"""
        # Re-enable the install button
        self.install_memryx_prereq_btn.setEnabled(True)
        self.install_memryx_prereq_btn.setText("🧠 Install MemryX Drivers & Runtime")
        
        if success:
            self.prereq_progress.append("🎉 MemryX installation completed successfully!")
            
            # Check if restart is needed by checking for devices
            devices = [d for d in glob.glob("/dev/memx*") if "_feature" not in d]
            device_count = len(devices)
            
            if device_count == 0:
                # No devices detected, restart is needed
                QMessageBox.information(
                    self, "MemryX Installation Complete", 
                    "✅ MemryX drivers and runtime have been installed successfully!\n\n"
                    "IMPORTANT: You must restart your computer now for the drivers to take effect.\n\n"
                    "After restart:\n"
                    "• MemryX devices should be detected\n"
                    "• Hardware acceleration will be available\n"
                    "• Frigate can use MemryX for AI inference\n\n"
                    "The 'Restart System Now' button is now available for your convenience."
                )
            else:
                # Devices already detected (unusual but possible)
                QMessageBox.information(
                    self, "MemryX Installation Complete", 
                    "✅ MemryX drivers and runtime have been installed successfully!\n\n"
                    "MemryX devices are already detected and ready for use.\n"
                    "Hardware acceleration is now available for Frigate."
                )
        else:
            self.prereq_progress.append("💡 Please check the error messages above.")
            QMessageBox.warning(
                self, "MemryX Installation Failed", 
                "❌ MemryX installation failed. Please check the progress log for details.\n\n"
                "Common issues:\n"
                "• Missing kernel headers\n"
                "• Network connectivity problems\n"
                "• Unsupported system configuration\n\n"
                "You may need to install MemryX manually or resolve system issues."
            )
        
        # Refresh MemryX status
        self.check_memryx_prereq_status()
        self.check_system_prerequisites()

    def restart_system(self):
        """Restart the system after confirming with user"""
        reply = QMessageBox.question(
            self, "Restart System", 
            "This will restart your computer to activate the MemryX drivers.\n\n"
            "⚠️ IMPORTANT:\n"
            "• Save any open work before proceeding\n"
            "• Close all applications\n"
            "• Make sure no important processes are running\n\n"
            "After restart, MemryX devices should be detected and available for use.\n\n"
            "Do you want to restart your computer now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No  # Default to No for safety
        )
        
        if reply == QMessageBox.Yes:
            # Get sudo password for restart
            sudo_password = PasswordDialog.get_sudo_password(self, "system restart")
            if sudo_password is None:
                self.prereq_progress.append("❌ System restart cancelled - password required")
                return
            
            try:
                self.prereq_progress.append("🔄 Initiating system restart...")
                self.prereq_progress.append("💾 Please save any open work before the restart completes.")
                
                # Store password for _perform_restart
                self.restart_sudo_password = sudo_password
                
                # Give user a few seconds to see the message
                QTimer.singleShot(2000, self._perform_restart)
                
            except Exception as e:
                self.prereq_progress.append(f"❌ Error initiating restart: {str(e)}")
                QMessageBox.warning(
                    self, "Restart Failed", 
                    f"❌ Could not restart the system automatically: {str(e)}\n\n"
                    "Please restart your computer manually:\n"
                    "• Open terminal and run: sudo reboot\n"
                    "• Or use your system's restart option"
                )
    
    def _perform_restart(self):
        """Actually perform the system restart"""
        try:
            # Show final warning
            QMessageBox.information(
                self, "Restarting Now", 
                "🔄 Your computer will restart in a few seconds.\n\n"
                "The Frigate Launcher will start automatically after restart.\n"
                "MemryX devices should be detected and ready for use.",
                QMessageBox.Ok
            )
            
            # Perform the restart with sudo password
            if hasattr(self, 'restart_sudo_password') and self.restart_sudo_password:
                # Use sudo -S to read password from stdin
                sudo_cmd = ['sudo', '-S', 'reboot']
                result = subprocess.run(sudo_cmd, input=f"{self.restart_sudo_password}\n", 
                                      text=True, check=True, capture_output=True)
                self.prereq_progress.append("✅ Restart command executed successfully")
            else:
                # Fallback to normal sudo (will prompt for password)
                subprocess.run(['sudo', 'reboot'], check=True)
            
        except subprocess.CalledProcessError as e:
            self.prereq_progress.append(f"❌ Restart command failed: {str(e)}")
            if e.stderr:
                self.prereq_progress.append(f"   Error details: {e.stderr}")
            QMessageBox.warning(
                self, "Restart Failed", 
                "❌ Could not restart the system.\n\n"
                "Please restart your computer manually:\n"
                "• Open terminal and run: sudo reboot\n"
                "• Or use your system's restart option"
            )
        except Exception as e:
            self.prereq_progress.append(f"❌ Unexpected error during restart: {str(e)}")
            QMessageBox.warning(
                self, "Restart Error", 
                f"❌ Unexpected error: {str(e)}\n\n"
                "Please restart your computer manually."
            )
        finally:
            # Clean up the stored password
            if hasattr(self, 'restart_sudo_password'):
                self.restart_sudo_password = None

    def run_sudo_command(self, command, description):
        """Run a sudo command with password authentication"""
        try:
            self.progress.emit(description)
            
            if self.sudo_password:
                # Use sudo -S to read password from stdin (safer than shell=True)
                sudo_cmd = ['sudo', '-S'] + command[1:]  # Remove 'sudo' from original command
                password_input = f"{self.sudo_password}\n"
                result = subprocess.run(sudo_cmd, input=password_input, text=True, 
                                      check=True, capture_output=True)
            else:
                # Fallback to regular sudo (will fail if no terminal)
                result = subprocess.run(command, check=True, capture_output=True, text=True)
            
            return True
        except subprocess.CalledProcessError as e:
            self.progress.emit(f"❌ Error in {description}: {e}")
            if e.stderr:
                self.progress.emit(f"Error details: {e.stderr}")
            return False
        except Exception as e:
            self.progress.emit(f"❌ Unexpected error in {description}: {e}")
            return False

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("MemryX + Frigate Launcher")
    app.setApplicationVersion("1.0.0")
    
    # Apply system palette for better integration
    palette = app.palette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, QColor(73, 80, 87))
    app.setPalette(palette)
    
    window = FrigateLauncher()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()