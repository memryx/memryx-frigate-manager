#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
New Widgets for Frigate Launcher Redesign
Contains StartFrigateWidget and ConfigureWidget
"""

import os
import sys
import subprocess
import glob
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QMessageBox, QProgressBar, QGridLayout,
    QSpacerItem, QSizePolicy, QApplication, QFrame, QDialog
)
from PySide6.QtCore import Signal, QTimer, Qt, QUrl, QThread
from PySide6.QtGui import QFont, QDesktopServices

# Import from main file
try:
    from frigate_launcher import (
        PRIMARY_COLOR, SUCCESS_COLOR, WARNING_COLOR, ERROR_COLOR, INFO_COLOR,
        BACKGROUND, CARD_BG, TEXT_PRIMARY, TEXT_SECONDARY, BORDER_COLOR,
        STATUS_NOT_STARTED, STATUS_IN_PROGRESS, STATUS_COMPLETED, STATUS_WARNING,
        PasswordDialog, SimpleCameraGUI, ConfigGUI
    )
except ImportError:
    # Fallback color definitions
    PRIMARY_COLOR = "#4a90a4"
    SUCCESS_COLOR = "#48bb78"
    WARNING_COLOR = "#ed8936"
    ERROR_COLOR = "#f56565"
    INFO_COLOR = "#4299e1"
    BACKGROUND = "#f7fafc"
    CARD_BG = "#ffffff"
    TEXT_PRIMARY = "#2d3748"
    TEXT_SECONDARY = "#718096"
    BORDER_COLOR = "#e2e8f0"
    STATUS_NOT_STARTED = "not_started"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_COMPLETED = "completed"
    STATUS_WARNING = "warning"

# ============================================================================
# START FRIGATE WIDGET (Section 2) - SIMPLIFIED
# ============================================================================
class StartFrigateWidget(QWidget):
    """Simplified widget to pull official image and start Frigate container"""
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.config_dir = os.path.join(script_dir, "frigate", "config")
        self.docker_worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)
        
        # ===== Info Section =====
        info_note = QLabel(
            "🚀 <b>Get Started with Frigate</b><br><br>"
            "Click <b>Start Frigate</b> below to:<br>"
            "• Pull the official Frigate image (ghcr.io/blakeblackshear/frigate:stable with MemryX built-in)<br>"
            "• Create and start the container<br>"
            "• Auto-generate default config.yaml<br><br>"
            "<b>Next Steps:</b><br>"
            "1. Once started, go to <b>Section 3</b> to add your cameras<br>"
            "2. Click <b>Restart</b> here to apply your camera changes<br>"
            "3. Click <b>Open Live View</b> to view your camera feeds!"
        )
        info_note.setWordWrap(True)
        info_note.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 400;
                padding: 20px;
                background: #f0f9ff;
                border: 2px solid #60a5fa;
                border-radius: 12px;
                line-height: 1.8;
            }}
        """)
        layout.addWidget(info_note)
        
        # ===== Container Status =====
        status_section = QWidget()
        status_layout = QVBoxLayout(status_section)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(12)
        
        status_header = QLabel("🐳 Container Status")
        status_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        status_layout.addWidget(status_header)
        
        # Status display
        status_container = QHBoxLayout()
        self.status_label = QLabel("Status: 🔍 Checking...")
        self.status_label.setWordWrap(False)
        self.status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 500;
                padding: 14px 18px;
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }}
        """)
        status_container.addWidget(self.status_label)
        status_container.addStretch()
        status_layout.addLayout(status_container)
        
        layout.addWidget(status_section)
        
        # ===== Action Buttons =====
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(12)
        
        self.start_btn = QPushButton("▶️ Start Frigate")
        self.start_btn.clicked.connect(self.start_frigate)
        self.start_btn.setStyleSheet(self.get_button_style(SUCCESS_COLOR))
        self.start_btn.setMinimumHeight(48)
        self.start_btn.setMinimumWidth(180)
        
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.clicked.connect(self.stop_frigate)
        self.stop_btn.setStyleSheet(self.get_button_style(ERROR_COLOR))
        self.stop_btn.setMinimumHeight(48)
        self.stop_btn.setMinimumWidth(140)
        self.stop_btn.setEnabled(False)
        
        self.restart_btn = QPushButton("🔄 Restart")
        self.restart_btn.clicked.connect(self.restart_frigate)
        self.restart_btn.setStyleSheet(self.get_button_style(WARNING_COLOR))
        self.restart_btn.setMinimumHeight(48)
        self.restart_btn.setMinimumWidth(140)
        self.restart_btn.setEnabled(False)
        
        self.open_ui_btn = QPushButton("📹 Open Live View")
        self.open_ui_btn.clicked.connect(lambda: webbrowser.open('http://localhost:5000'))
        self.open_ui_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.open_ui_btn.setMinimumHeight(48)
        self.open_ui_btn.setMinimumWidth(160)
        
        self.delete_btn = QPushButton("🗑️ Delete Container")
        self.delete_btn.clicked.connect(self.delete_container)
        self.delete_btn.setStyleSheet(self.get_button_style("#dc2626"))
        self.delete_btn.setMinimumHeight(48)
        self.delete_btn.setMinimumWidth(160)
        self.delete_btn.setEnabled(False)
        
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.restart_btn)
        buttons_layout.addWidget(self.open_ui_btn)
        buttons_layout.addWidget(self.delete_btn)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # ===== Log Output =====
        log_section = QWidget()
        log_layout = QVBoxLayout(log_section)
        log_layout.setContentsMargins(0, 0, 0, 0)
        log_layout.setSpacing(12)
        
        log_header = QLabel("📋 Container Log")
        log_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        log_layout.addWidget(log_header)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(200)
        self.log_output.setMaximumHeight(300)
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
        log_layout.addWidget(self.log_output)
        
        layout.addWidget(log_section)
        layout.addStretch()
        
        # Initial status check
        QTimer.singleShot(100, self.check_status)
    
    def get_button_style(self, color):
        """Get styled button CSS"""
        hover_map = {
            SUCCESS_COLOR: "#059669",
            ERROR_COLOR: "#dc2626",
            WARNING_COLOR: "#d97706",
            INFO_COLOR: "#0891b2",
        }
        hover_color = hover_map.get(color, color)
        
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
                background: #e2e8f0;
                color: #94a3b8;
            }}
        """
    
    def check_status(self):
        """Check Frigate container status"""
        self.log_output.append("🔍 Checking Frigate container status...")
        
        try:
            # Check if container exists
            result = subprocess.run(
                ['docker', 'ps', '-a', '--format', '{{.Names}}'],
                capture_output=True, text=True, timeout=5
            )
            
            if 'frigate' in result.stdout:
                # Container exists, check if running
                running_result = subprocess.run(
                    ['docker', 'ps', '--format', '{{.Names}}'],
                    capture_output=True, text=True, timeout=5
                )
                
                if 'frigate' in running_result.stdout:
                    self.status_label.setText("Status: ✅ Running")
                    self.status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {TEXT_PRIMARY};
                            font-size: 16px;
                            font-weight: 500;
                            padding: 14px 18px;
                            background: #f0fdf4;
                            border: 1px solid #86efac;
                            border-radius: 8px;
                        }}
                    """)
                    self.start_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
                    self.restart_btn.setEnabled(True)
                    self.delete_btn.setEnabled(False)
                    self.log_output.append("✅ Frigate container is running")
                    self.log_output.append("🌐 Access at: http://localhost:5000")
                else:
                    self.status_label.setText("Status: ⏸️ Stopped")
                    self.status_label.setStyleSheet(f"""
                        QLabel {{
                            color: {TEXT_PRIMARY};
                            font-size: 16px;
                            font-weight: 500;
                            padding: 14px 18px;
                            background: #fef3c7;
                            border: 1px solid #fbbf24;
                            border-radius: 8px;
                        }}
                    """)
                    self.start_btn.setEnabled(True)
                    self.stop_btn.setEnabled(False)
                    self.restart_btn.setEnabled(False)
                    self.delete_btn.setEnabled(True)
                    self.log_output.append("⏸️ Frigate container exists but is stopped")
            else:
                self.status_label.setText("Status: ❌ Not Created")
                self.status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {TEXT_PRIMARY};
                        font-size: 16px;
                        font-weight: 500;
                        padding: 14px 18px;
                        background: #fee2e2;
                        border: 1px solid #fca5a5;
                        border-radius: 8px;
                    }}
                """)
                self.start_btn.setEnabled(True)
                self.stop_btn.setEnabled(False)
                self.restart_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
                self.log_output.append("ℹ️ Frigate container not found - click Start to create")
                
        except Exception as e:
            self.log_output.append(f"⚠️ Error checking status: {str(e)}")
    
    def start_frigate(self):
        """Start Frigate - pull image and create/start container"""
        self.log_output.append("🚀 Starting Frigate...")
        self.start_btn.setEnabled(False)
        
        # Import and use the Docker worker from main launcher
        from frigate_launcher import DockerWorker
        
        # Start with 'start' action which creates/starts the container
        self.docker_worker = DockerWorker(self.script_dir, 'start')
        self.docker_worker.progress.connect(self.log_output.append)
        self.docker_worker.finished.connect(self.on_docker_finished)
        self.docker_worker.start()
    
    def stop_frigate(self):
        """Stop Frigate container"""
        self.log_output.append("⏹️ Stopping Frigate...")
        self.stop_btn.setEnabled(False)
        
        from frigate_launcher import DockerWorker
        self.docker_worker = DockerWorker(self.script_dir, 'stop')
        self.docker_worker.progress.connect(self.log_output.append)
        self.docker_worker.finished.connect(self.on_docker_finished)
        self.docker_worker.start()
    
    def restart_frigate(self):
        """Restart Frigate container"""
        self.log_output.append("🔄 Restarting Frigate...")
        self.restart_btn.setEnabled(False)
        
        from frigate_launcher import DockerWorker
        self.docker_worker = DockerWorker(self.script_dir, 'restart')
        self.docker_worker.progress.connect(self.log_output.append)
        self.docker_worker.finished.connect(self.on_docker_finished)
        self.docker_worker.start()
    
    def delete_container(self):
        """Delete Frigate container"""
        from PySide6.QtWidgets import QMessageBox
        
        reply = QMessageBox.question(
            self,
            "Delete Container",
            "Are you sure you want to delete the Frigate container?\n\n"
            "⚠️ This will:\n"
            "  • Remove the container completely\n"
            "  • Keep your configuration files safe\n"
            "  • Require you to click 'Start Frigate' again\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        self.log_output.append("🗑️ Deleting Frigate container...")
        self.delete_btn.setEnabled(False)
        
        try:
            result = subprocess.run(
                ['docker', 'rm', '-f', 'frigate'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                self.log_output.append("✅ Container deleted successfully")
                QMessageBox.information(self, "Success", "Frigate container has been deleted successfully!")
            else:
                self.log_output.append(f"❌ Failed to delete container: {result.stderr}")
                QMessageBox.warning(self, "Error", f"Failed to delete container:\n{result.stderr}")
                
        except Exception as e:
            self.log_output.append(f"❌ Error: {str(e)}")
            QMessageBox.critical(self, "Error", f"Error deleting container:\n{str(e)}")
        
        # Refresh status
        QTimer.singleShot(500, self.check_status)
    
    def on_docker_finished(self, success):
        """Handle Docker operation completion"""
        if success:
            self.log_output.append("✅ Operation completed successfully!")
        else:
            self.log_output.append("❌ Operation failed - check log above")
        
        # Refresh status
        QTimer.singleShot(500, self.check_status)

# ============================================================================
# CONFIGURE WIDGET (Section 3)
# ============================================================================
class ConfigureWidget(QWidget):
    """Widget for configuring Frigate (cameras and advanced settings)"""
    
    status_changed = Signal(str)
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.config_file = os.path.join(script_dir, "frigate", "config", "config.yaml")
        self.camera_gui_window = None
        self.config_gui_window = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components with clean, minimal design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)
        
        # ===== Simple Info Message =====
        info_row = QHBoxLayout()
        info_row.setSpacing(0)
        
        info_label = QLabel(
            "💡 After configuring cameras, return to <b>Section 2</b> and click <b>Restart</b> to apply changes."
        )
        info_label.setWordWrap(False)
        info_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        info_label.setStyleSheet(f"""
            QLabel {{
                color: #991b1b;
                font-size: 17px;
                font-weight: 500;
                padding: 16px 20px;
                background: #fee2e2;
                border-left: 4px solid #ef4444;
                border-radius: 8px;
            }}
        """)
        info_row.addWidget(info_label)
        info_row.addStretch()
        
        layout.addLayout(info_row)
        
        # ===== Main Configuration Options (All 3 in one row - EXACT same size) =====
        config_row = QWidget()
        config_layout = QHBoxLayout(config_row)
        config_layout.setSpacing(15)
        config_layout.setContentsMargins(0, 0, 0, 0)
        
        # Method 1: Quick Camera Setup
        quick_setup_card = QWidget()
        quick_setup_card.setFixedHeight(120)  # Fixed height for all cards
        quick_layout = QVBoxLayout(quick_setup_card)
        quick_layout.setContentsMargins(16, 14, 16, 14)
        quick_layout.setSpacing(8)
        quick_setup_card.setStyleSheet(f"""
            QWidget {{
                background: #f0f9ff;
                border-radius: 10px;
            }}
        """)
        
        quick_header = QLabel("📹 <b>Quick Camera Setup</b>")
        quick_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; background: transparent;")
        quick_layout.addWidget(quick_header)
        
        quick_desc = QLabel("Add cameras with default YOLOv9 model and settings")
        quick_desc.setWordWrap(True)
        quick_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; background: transparent;")
        quick_layout.addWidget(quick_desc)
        
        quick_layout.addStretch()
        
        quick_btn = QPushButton("Open Camera Setup")
        quick_btn.clicked.connect(self.open_camera_gui)
        quick_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        quick_btn.setFixedHeight(45)
        quick_layout.addWidget(quick_btn)
        
        config_layout.addWidget(quick_setup_card, 1)  # Equal stretch factor
        
        # Method 2: Advanced Editor
        adv_card = QWidget()
        adv_card.setFixedHeight(120)  # Fixed height for all cards
        adv_card_layout = QVBoxLayout(adv_card)
        adv_card_layout.setContentsMargins(16, 14, 16, 14)
        adv_card_layout.setSpacing(8)
        adv_card.setStyleSheet(f"""
            QWidget {{
                background: #f9fafb;
                border-radius: 8px;
            }}
        """)
        
        adv_header = QLabel("🔧 <b>Advanced Editor</b>")
        adv_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; background: transparent;")
        adv_card_layout.addWidget(adv_header)
        
        adv_desc = QLabel("Choose models, edit resolutions, and configure all options")
        adv_desc.setWordWrap(True)
        adv_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; background: transparent;")
        adv_card_layout.addWidget(adv_desc)
        
        adv_card_layout.addStretch()
        
        adv_btn = QPushButton("Open Advanced Editor")
        adv_btn.clicked.connect(self.open_advanced_config)
        adv_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        adv_btn.setFixedHeight(45)
        adv_card_layout.addWidget(adv_btn)
        
        config_layout.addWidget(adv_card, 1)  # Equal stretch factor
        
        # Method 3: Manual YAML Editor
        manual_card = QWidget()
        manual_card.setFixedHeight(120)  # Fixed height for all cards
        manual_card_layout = QVBoxLayout(manual_card)
        manual_card_layout.setContentsMargins(16, 14, 16, 14)
        manual_card_layout.setSpacing(8)
        manual_card.setStyleSheet(f"""
            QWidget {{
                background: #fffbeb;
                border-radius: 8px;
            }}
        """)
        
        manual_header = QLabel("📝 <b>Manual YAML Editor</b>")
        manual_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; background: transparent;")
        manual_card_layout.addWidget(manual_header)
        
        manual_desc = QLabel("Edit config.yaml directly in your text editor")
        manual_desc.setWordWrap(True)
        manual_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px; background: transparent;")
        manual_card_layout.addWidget(manual_desc)
        
        manual_card_layout.addStretch()
        
        manual_btn = QPushButton("Open YAML Editor")
        manual_btn.clicked.connect(self.open_manual_editor)
        manual_btn.setStyleSheet(self.get_button_style("#fbbf24"))
        manual_btn.setFixedHeight(45)
        manual_card_layout.addWidget(manual_btn)
        
        config_layout.addWidget(manual_card, 1)  # Equal stretch factor
        
        layout.addWidget(config_row)
        
        # ===== Status Display =====
        status_row = QHBoxLayout()
        status_row.setSpacing(0)
        
        # Config path display
        config_path_label = QLabel(f"⚙️ <b>Config Path:</b> {self.config_file}")
        config_path_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                padding: 8px 12px;
                background: #f9fafb;
                border-radius: 6px;
            }}
        """)
        status_row.addWidget(config_path_label)
        status_row.addStretch()
        
        layout.addLayout(status_row)
        
        # ===== FFmpeg Hardware Acceleration (With border and padding) =====
        layout.addSpacing(10)
        
        # Container to prevent full-width stretching
        ffmpeg_row = QHBoxLayout()
        ffmpeg_row.setSpacing(0)
        
        ffmpeg_container = QWidget()
        ffmpeg_container.setObjectName("ffmpegContainer")
        ffmpeg_container.setMaximumWidth(900)  # Limit width
        ffmpeg_container.setStyleSheet(f"""
            #ffmpegContainer {{
                background: white;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
            }}
        """)
        ffmpeg_main_layout = QVBoxLayout(ffmpeg_container)
        ffmpeg_main_layout.setContentsMargins(20, 16, 20, 16)
        ffmpeg_main_layout.setSpacing(10)
        
        # Header with icon
        ffmpeg_header = QLabel("⚡ <b>FFmpeg Hardware Acceleration (Intel & AMD VAAPI)</b>")
        ffmpeg_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 15px; font-weight: 600;")
        ffmpeg_main_layout.addWidget(ffmpeg_header)
        
        # Description
        ffmpeg_desc = QLabel("Install VA-API drivers for hardware-accelerated video decoding (Intel/AMD GPUs)")
        ffmpeg_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        ffmpeg_main_layout.addWidget(ffmpeg_desc)
        
        # Status and buttons row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        status_label = QLabel("Status:")
        status_label.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        controls_layout.addWidget(status_label)
        
        self.ffmpeg_status_label = QLabel("Checking...")
        self.ffmpeg_status_label.setStyleSheet(f"""
            QLabel {{
                color: #065f46;
                font-size: 14px;
                padding: 4px 8px;
                background: #ecfdf5;
                border-radius: 4px;
            }}
        """)
        controls_layout.addWidget(self.ffmpeg_status_label)
        
        controls_layout.addStretch()
        
        self.ffmpeg_install_btn = QPushButton("✓ VA-API Installed")
        self.ffmpeg_install_btn.clicked.connect(self.install_ffmpeg_packages)
        self.ffmpeg_install_btn.setStyleSheet(self.get_button_style("#8b5cf6"))
        self.ffmpeg_install_btn.setFixedHeight(36)
        self.ffmpeg_install_btn.setMinimumWidth(140)
        controls_layout.addWidget(self.ffmpeg_install_btn)
        
        self.ffmpeg_docs_btn = QPushButton("📖 View Documentation")
        self.ffmpeg_docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://docs.frigate.video/configuration/ffmpeg_presets/")))
        self.ffmpeg_docs_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.ffmpeg_docs_btn.setFixedHeight(36)
        self.ffmpeg_docs_btn.setMinimumWidth(170)
        controls_layout.addWidget(self.ffmpeg_docs_btn)
        
        ffmpeg_main_layout.addLayout(controls_layout)
        
        # Add to row with stretch on the right
        ffmpeg_row.addWidget(ffmpeg_container)
        ffmpeg_row.addStretch()
        
        layout.addLayout(ffmpeg_row)
        
        # Add generous bottom spacing for better scrolling experience
        layout.addSpacing(150)
        layout.addStretch()
        
        # Check initial status
        QTimer.singleShot(100, self.check_ffmpeg_status)
    
    def get_button_style(self, color):
        """Get styled button CSS with professional teal theme"""
        # Determine hover and pressed colors based on input color
        if color == PRIMARY_COLOR:
            hover_color = "#38758a"
            pressed_color = "#2d6374"
        elif color == SUCCESS_COLOR:
            hover_color = "#38a169"
            pressed_color = "#2f855a"
        elif color == WARNING_COLOR:
            hover_color = "#dd6b20"
            pressed_color = "#c05621"
        elif color == ERROR_COLOR:
            hover_color = "#e53e3e"
            pressed_color = "#c53030"
        elif color == INFO_COLOR:
            hover_color = "#3182ce"
            pressed_color = "#2c5282"
        elif color == "#8b5cf6":  # Purple for FFmpeg
            hover_color = "#7c3aed"
            pressed_color = "#6d28d9"
        else:
            hover_color = color
            pressed_color = color
            
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {hover_color});
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {hover_color}, stop:1 {pressed_color});
            }}
            QPushButton:pressed {{
                background: {pressed_color};
            }}
        """
        
    def check_camera_config(self):
        """Check camera configuration status"""
        try:
            if os.path.exists(self.config_file):
                import yaml
                with open(self.config_file, 'r') as f:
                    config = yaml.safe_load(f)
                    
                if config and 'cameras' in config:
                    camera_count = len(config['cameras'])
                    
                    if camera_count == 0:
                        self.camera_summary_label.setText("📹 Cameras: None configured")
                    else:
                        camera_names = list(config['cameras'].keys())
                        if camera_count <= 2:
                            names_str = ", ".join(camera_names)
                            self.camera_summary_label.setText(f"📹 Cameras: {camera_count} ({names_str})")
                        else:
                            self.camera_summary_label.setText(f"📹 Cameras: {camera_count} configured")
                    
                    self.status_changed.emit(STATUS_COMPLETED)
                else:
                    self.camera_summary_label.setText("📹 Cameras: None configured")
            else:
                self.camera_summary_label.setText("📹 Cameras: No config file")
                
        except Exception as e:
            self.camera_summary_label.setText("📹 Cameras: Error reading config")

            
    def open_camera_gui(self):
        """Open the camera configuration GUI"""
        try:
            if SimpleCameraGUI:
                self.camera_gui_window = SimpleCameraGUI()
                self.camera_gui_window.show()
            else:
                QMessageBox.warning(self, "Not Available", "Camera GUI is not available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Camera GUI: {str(e)}")
            
    def open_advanced_config(self):
        """Open the advanced configuration GUI"""
        try:
            if ConfigGUI:
                self.config_gui_window = ConfigGUI()
                # Set launcher_parent to indicate it's launched from the launcher
                # This prevents closing the entire application when closing ConfigGUI
                self.config_gui_window.launcher_parent = self
                self.config_gui_window.show()
            else:
                QMessageBox.warning(self, "Not Available", "Config GUI is not available")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open Config GUI: {str(e)}")
    
    def open_manual_editor(self):
        """Open manual YAML editor for config file"""
        try:
            if not os.path.exists(self.config_file):
                QMessageBox.warning(
                    self, 
                    "Config Not Found", 
                    f"Configuration file not found:\n{self.config_file}\n\n"
                    "Please create a config file first using the Simple Camera Configuration or Advanced Editor."
                )
                return
            
            # Try to open with system's default YAML/text editor
            if sys.platform == 'darwin':  # macOS
                subprocess.Popen(['open', '-e', self.config_file])
            elif sys.platform == 'win32':  # Windows
                os.startfile(self.config_file)
            else:  # Linux and other Unix-like
                # Try common editors in order of preference
                editors = ['code', 'gedit', 'kate', 'nano', 'vim', 'vi', 'xdg-open']
                editor_found = False
                for editor in editors:
                    try:
                        subprocess.Popen([editor, self.config_file])
                        editor_found = True
                        break
                    except FileNotFoundError:
                        continue
                
                if not editor_found:
                    QMessageBox.warning(
                        self,
                        "No Editor Found",
                        f"Could not find a text editor.\n\n"
                        f"Please manually edit: {self.config_file}"
                    )
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open manual editor: {str(e)}")
    
    def check_ffmpeg_status(self):
        """Check if FFmpeg VA-API drivers are installed"""
        try:
            packages = [
                'ffmpeg',
                'vainfo',
                'intel-media-va-driver',
                'i965-va-driver',
                'mesa-va-drivers',
                'libva2',
                'libva-drm2'
            ]
            
            installed = []
            missing = []
            
            for package in packages:
                result = subprocess.run(
                    ['dpkg-query', '-W', '-f=${Status}', package],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 and 'install ok installed' in result.stdout:
                    installed.append(package)
                else:
                    missing.append(package)
            
            if not missing:
                self.ffmpeg_status_label.setText("Status: ✅ All VA-API drivers installed")
                self.ffmpeg_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: #065f46;
                        font-size: 14px;
                        padding: 6px 10px;
                        background: #ecfdf5;
                        border-radius: 4px;
                        margin-top: 5px;
                    }}
                """)
                self.ffmpeg_install_btn.setText("✓ VA-API Installed")
                self.ffmpeg_install_btn.setEnabled(False)
                
                # Auto-update config if FFmpeg is installed
                config_path = os.path.join(self.script_dir, "frigate", "config", "config.yaml")
                self.update_config_with_ffmpeg(config_path)
            else:
                self.ffmpeg_status_label.setText(f"Status: ⚠️ Missing {len(missing)} package(s)")
                self.ffmpeg_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {TEXT_SECONDARY};
                        font-size: 14px;
                        padding: 6px 10px;
                        background: #fef9e7;
                        border-radius: 4px;
                        margin-top: 5px;
                    }}
                """)
                self.ffmpeg_install_btn.setEnabled(True)
                
        except Exception as e:
            self.ffmpeg_status_label.setText(f"Status: Error checking packages")
            self.ffmpeg_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_SECONDARY};
                    font-size: 14px;
                    padding: 6px 10px;
                    background: #f7fafc;
                    border-radius: 4px;
                    margin-top: 5px;
                }}
            """)
    
    def update_config_with_ffmpeg(self, config_path):
        """Update config.yaml with FFmpeg hardware acceleration (if not already present)"""
        try:
            import yaml
            from collections import OrderedDict
            
            # Check if config file exists
            if not os.path.exists(config_path):
                return  # Silently skip if no config
            
            # Read current config preserving order
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Check if ffmpeg section already has hwaccel_args at top level
            if 'ffmpeg' in config and isinstance(config['ffmpeg'], dict) and 'hwaccel_args' in config['ffmpeg']:
                return
            
            # Create new ordered config with ffmpeg after mqtt
            new_config = OrderedDict()
            ffmpeg_added = False
            
            for key, value in config.items():
                new_config[key] = value
                
                # After adding mqtt section, add ffmpeg (top-level)
                if key == 'mqtt' and not ffmpeg_added:
                    if 'ffmpeg' not in config:
                        new_config['ffmpeg'] = {'hwaccel_args': 'preset-vaapi'}
                        ffmpeg_added = True
                    elif 'hwaccel_args' not in config.get('ffmpeg', {}):
                        if 'ffmpeg' not in new_config:
                            new_config['ffmpeg'] = {}
                        new_config['ffmpeg']['hwaccel_args'] = 'preset-vaapi'
                        ffmpeg_added = True
            
            # If mqtt doesn't exist or ffmpeg wasn't added, add ffmpeg at the end
            if not ffmpeg_added:
                if 'ffmpeg' not in new_config:
                    new_config['ffmpeg'] = {'hwaccel_args': 'preset-vaapi'}
                elif 'hwaccel_args' not in new_config.get('ffmpeg', {}):
                    new_config['ffmpeg']['hwaccel_args'] = 'preset-vaapi'
            
            # Write updated config
            with open(config_path, 'w') as f:
                yaml.dump(dict(new_config), f, default_flow_style=False, sort_keys=False)
            
        except Exception as e:
            pass  # Silently handle errors in auto-update
    
    def install_ffmpeg_packages(self):
        """Install FFmpeg VA-API hardware acceleration packages"""
        reply = QMessageBox.question(
            self,
            "Install FFmpeg VA-API Drivers",
            "This will install FFmpeg hardware acceleration drivers.\n\n"
            "Packages to install:\n"
            "• ffmpeg - Video encoding/decoding framework\n"
            "• vainfo - VA-API information utility\n"
            "• intel-media-va-driver - Intel Media SDK VA-API driver\n"
            "• i965-va-driver - Legacy Intel VA-API driver\n"
            "• mesa-va-drivers - Mesa VA-API drivers\n"
            "• libva2 - VA-API library\n"
            "• libva-drm2 - VA-API DRM runtime\n\n"
            "This requires sudo privileges and may take several minutes.\n\n"
            "Continue with installation?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
        
        # Import PasswordDialog from frigate_launcher
        from frigate_launcher import PasswordDialog, FFmpegInstallWorker
        
        # Get sudo password
        sudo_password = PasswordDialog.get_sudo_password(self, "FFmpeg VA-API installation")
        if sudo_password is None:
            QMessageBox.warning(self, "Cancelled", "Installation cancelled - password required")
            return
        
        # Disable install button during operation
        self.ffmpeg_install_btn.setEnabled(False)
        self.ffmpeg_install_btn.setText("🔄 Installing...")
        
        # Create progress dialog
        from PySide6.QtWidgets import QDialog, QTextEdit
        self.ffmpeg_progress_dialog = QDialog(self)
        self.ffmpeg_progress_dialog.setWindowTitle("Installing FFmpeg VA-API Drivers")
        self.ffmpeg_progress_dialog.setMinimumWidth(600)
        self.ffmpeg_progress_dialog.setMinimumHeight(400)
        
        progress_layout = QVBoxLayout(self.ffmpeg_progress_dialog)
        
        progress_label = QLabel("Installing FFmpeg hardware acceleration packages...")
        progress_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        progress_layout.addWidget(progress_label)
        
        self.ffmpeg_progress_text = QTextEdit()
        self.ffmpeg_progress_text.setReadOnly(True)
        self.ffmpeg_progress_text.setStyleSheet("""
            QTextEdit {
                background: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                border: 1px solid #3e3e3e;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        progress_layout.addWidget(self.ffmpeg_progress_text)
        
        # Start installation worker
        self.ffmpeg_install_worker = FFmpegInstallWorker(self.script_dir, sudo_password)
        self.ffmpeg_install_worker.progress.connect(self.ffmpeg_progress_text.append)
        self.ffmpeg_install_worker.config_path.connect(self.on_ffmpeg_config_update)
        self.ffmpeg_install_worker.finished.connect(self.on_ffmpeg_install_finished)
        self.ffmpeg_install_worker.start()
        
        # Show progress dialog
        self.ffmpeg_progress_dialog.exec()
    
    def on_ffmpeg_config_update(self, config_path):
        """Auto-update config.yaml with FFmpeg hardware acceleration settings"""
        try:
            import yaml
            
            # Check if config file exists
            if not os.path.exists(config_path):
                self.ffmpeg_progress_text.append("⚠️  Config file not found - skipping auto-update")
                self.ffmpeg_progress_text.append(f"   Please manually add to {config_path}:")
                self.ffmpeg_progress_text.append("   ffmpeg:")
                self.ffmpeg_progress_text.append("     hwaccel_args: preset-vaapi")
                return
            
            # Read current config
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f) or {}
            
            # Check if ffmpeg section already has hwaccel_args
            if 'ffmpeg' in config and 'hwaccel_args' in config['ffmpeg']:
                current_value = config['ffmpeg']['hwaccel_args']
                if current_value == 'preset-vaapi':
                    self.ffmpeg_progress_text.append("ℹ️  Config already has hwaccel_args: preset-vaapi")
                    return
                else:
                    self.ffmpeg_progress_text.append(f"ℹ️  Config has different hwaccel_args: {current_value}")
                    self.ffmpeg_progress_text.append("   Keeping existing configuration")
                    return
            
            # Add ffmpeg hardware acceleration
            if 'ffmpeg' not in config:
                config['ffmpeg'] = {}
            config['ffmpeg']['hwaccel_args'] = 'preset-vaapi'
            
            # Write updated config
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            
            self.ffmpeg_progress_text.append("")
            self.ffmpeg_progress_text.append("🎯 Config.yaml updated with hardware acceleration!")
            self.ffmpeg_progress_text.append("   Added: ffmpeg:")
            self.ffmpeg_progress_text.append("            hwaccel_args: preset-vaapi")
            
        except Exception as e:
            self.ffmpeg_progress_text.append(f"⚠️  Could not auto-update config: {str(e)}")
            self.ffmpeg_progress_text.append(f"   Please manually add to {config_path}:")
            self.ffmpeg_progress_text.append("   ffmpeg:")
            self.ffmpeg_progress_text.append("     hwaccel_args: preset-vaapi")
    
    def on_ffmpeg_install_finished(self, success):
        """Handle FFmpeg installation completion"""
        # Re-enable button
        self.ffmpeg_install_btn.setEnabled(True)
        self.ffmpeg_install_btn.setText("⚡ Install VA-API Drivers")
        
        if success:
            self.ffmpeg_progress_text.append("")
            self.ffmpeg_progress_text.append("✅ Installation completed successfully!")
            QMessageBox.information(
                self,
                "Installation Complete",
                "✅ FFmpeg VA-API drivers installed successfully!\n\n"
                "Hardware acceleration is now available for Frigate.\n"
                "Your config.yaml has been updated automatically."
            )
            # Refresh status
            self.check_ffmpeg_status()
        else:
            self.ffmpeg_progress_text.append("")
            self.ffmpeg_progress_text.append("❌ Installation failed. Please check the log above.")
            QMessageBox.warning(
                self,
                "Installation Failed",
                "❌ FFmpeg installation failed.\n\n"
                "Please check the progress log for details."
            )
            
    def validate_config(self):
        """Validate the configuration file"""
        try:
            if not os.path.exists(self.config_file):
                self.validation_status_label.setText("Status: ❌ Config file not found")
                self.validation_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {ERROR_COLOR};
                        font-size: 16px;
                        font-weight: bold;
                        padding: 10px;
                        background: #fed7d7;
                        border-radius: 4px;
                    }}
                """)
                return
                
            import yaml
            with open(self.config_file, 'r') as f:
                config = yaml.safe_load(f)
                
            # Basic validation
            if not config:
                raise ValueError("Config file is empty")
                
            if 'cameras' not in config:
                raise ValueError("No cameras configured")
                
            self.validation_status_label.setText("Status: ✅ Configuration is valid")
            self.validation_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {SUCCESS_COLOR};
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                    background: #c6f6d5;
                    border-radius: 4px;
                }}
            """)
            
            QMessageBox.information(self, "Validation Success", "✅ Configuration file is valid!")
            
        except Exception as e:
            self.validation_status_label.setText(f"Status: ❌ Validation failed: {str(e)}")
            self.validation_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {ERROR_COLOR};
                    font-size: 16px;
                    font-weight: bold;
                    padding: 10px;
                    background: #fed7d7;
                    border-radius: 4px;
                }}
            """)
            QMessageBox.critical(self, "Validation Error", f"❌ Config validation failed:\n\n{str(e)}")
            
    def test_cameras(self):
        """Test camera connections"""
        QMessageBox.information(
            self, "Test Cameras",
            "Camera connection testing will be implemented soon.\n\n"
            "For now, please verify your camera streams manually."
        )



# Required import to prevent circular dependency
import time
