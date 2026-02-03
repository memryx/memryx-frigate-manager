#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
New Widgets for Frigate Launcher Redesign
Contains FrigateInstallWidget, ConfigureWidget, and LaunchMonitorWidget
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
# WORKER CLASSES
# ============================================================================
class GitCloneWorker(QThread):
    """Background worker for git clone operations"""
    progress = Signal(str)
    finished = Signal(bool)
    
    def __init__(self, repo_url, target_dir, remove_existing=False):
        super().__init__()
        self.repo_url = repo_url
        self.target_dir = target_dir
        self.remove_existing = remove_existing
    
    def run(self):
        import shutil
        try:
            # Remove existing directory if requested
            if self.remove_existing and os.path.exists(self.target_dir):
                self.progress.emit("🗑️ Removing existing Frigate directory...")
                shutil.rmtree(self.target_dir)
                self.progress.emit("✅ Existing directory removed")
            
            # Clone repository
            self.progress.emit(f"🔄 Cloning {self.repo_url}...")
            self.progress.emit("⏳ This may take 1-3 minutes depending on your connection...")
            
            result = subprocess.run(
                ['git', 'clone', self.repo_url, self.target_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                self.progress.emit("✅ Repository cloned successfully!")
                self.finished.emit(True)
            else:
                self.progress.emit(f"❌ Clone failed: {result.stderr}")
                self.finished.emit(False)
                
        except subprocess.TimeoutExpired:
            self.progress.emit("❌ Clone timed out after 5 minutes")
            self.finished.emit(False)
        except Exception as e:
            self.progress.emit(f"❌ Error: {str(e)}")
            self.finished.emit(False)

# ============================================================================
# FRIGATE INSTALL WIDGET (Section 2)
# ============================================================================
class FrigateInstallWidget(QWidget):
    """Widget for cloning and building Frigate"""
    
    status_changed = Signal(str)
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.frigate_dir = os.path.join(script_dir, "frigate")
        self.clone_worker = None
        self.build_worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)  # Increased spacing for breathing room
        
        # ===== Step 1: Frigate Repository =====
        repo_section = QWidget()
        repo_section_layout = QVBoxLayout(repo_section)
        repo_section_layout.setContentsMargins(0, 0, 0, 0)
        repo_section_layout.setSpacing(15)
        
        # Section header
        repo_header = QLabel("📂 Frigate Repository")
        repo_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        repo_section_layout.addWidget(repo_header)
        
        # Repository path display - compact info box
        repo_info_box = QWidget()
        repo_info_layout = QVBoxLayout(repo_info_box)
        repo_info_layout.setContentsMargins(12, 12, 12, 12)
        repo_info_layout.setSpacing(8)
        repo_info_box.setStyleSheet(f"""
            QWidget {{
                background: #f7fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }}
        """)
        
        self.repo_path_label = QLabel(f"<b>Repository Path:</b> {self.frigate_dir}")
        self.repo_path_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                font-family: 'Courier New', monospace;
                background: transparent;
            }}
        """)
        self.repo_path_label.setWordWrap(True)
        repo_info_layout.addWidget(self.repo_path_label)
        
        repo_section_layout.addWidget(repo_info_box)
        
        # Status display (outside the info box, with content-width background)
        status_container = QHBoxLayout()
        status_container.setContentsMargins(0, 8, 0, 0)
        
        self.repo_status_label = QLabel("Status: 🔍 Checking...")
        self.repo_status_label.setWordWrap(False)
        self.repo_status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.repo_status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 500;
                background: transparent;
            }}
        """)
        status_container.addWidget(self.repo_status_label)
        status_container.addStretch()
        repo_section_layout.addLayout(status_container)
        
        # Action buttons - larger
        repo_buttons = QHBoxLayout()
        repo_buttons.setSpacing(12)
        
        self.check_repo_btn = QPushButton("🔍 Check Status")
        self.check_repo_btn.clicked.connect(self.check_repo_status)
        self.check_repo_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.check_repo_btn.setMinimumHeight(48)
        self.check_repo_btn.setMinimumWidth(160)
        
        self.update_repo_btn = QPushButton("🔄 Update to Latest")
        self.update_repo_btn.clicked.connect(self.update_repository)
        self.update_repo_btn.setStyleSheet(self.get_button_style(SUCCESS_COLOR))
        self.update_repo_btn.setVisible(False)
        self.update_repo_btn.setToolTip("Pull latest updates from GitHub (keeps existing config)")
        self.update_repo_btn.setMinimumHeight(48)
        self.update_repo_btn.setMinimumWidth(180)
        
        self.clone_repo_btn = QPushButton("📥 Fresh Clone")
        self.clone_repo_btn.clicked.connect(self.clone_fresh_repository)
        self.clone_repo_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        self.clone_repo_btn.setToolTip("Clone fresh repository with default config and version.py")
        self.clone_repo_btn.setMinimumHeight(48)
        self.clone_repo_btn.setMinimumWidth(160)
        
        repo_buttons.addWidget(self.check_repo_btn)
        repo_buttons.addWidget(self.update_repo_btn)
        repo_buttons.addWidget(self.clone_repo_btn)
        repo_buttons.addStretch()
        
        repo_section_layout.addLayout(repo_buttons)
        
        layout.addWidget(repo_section)
        
        # Elegant divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider1)
        
        # ===== Step 2: Next Steps =====
        next_step_section = QWidget()
        next_step_section_layout = QVBoxLayout(next_step_section)
        next_step_section_layout.setContentsMargins(0, 0, 0, 0)
        next_step_section_layout.setSpacing(15)
        
        # Section header
        next_step_header = QLabel("👉 Next Steps")
        next_step_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        next_step_section_layout.addWidget(next_step_header)
        
        # Info box with next steps
        build_note_label = QLabel(
            "✅ <b>Repository cloned successfully!</b><br><br>"
            "📝 <b>Step 1:</b> Go to <b>Configure Frigate</b> (Section 3) to add your cameras to the config file.<br><br>"
            "🔨 <b>Step 2:</b> After configuring cameras, go to <b>Launch & Monitor</b> (Section 4) to build the Docker image.<br><br>"
        )
        build_note_label.setWordWrap(True)
        build_note_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                padding: 15px;
                background: #f0f9ff;
                border: 2px solid #60a5fa;
                border-radius: 8px;
                line-height: 1.6;
            }}
        """)
        next_step_section_layout.addWidget(build_note_label)
        
        layout.addWidget(next_step_section)
        
        # Elegant divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider2)
        
        # ===== Step 3: Operation Log =====
        log_section = QWidget()
        log_section_layout = QVBoxLayout(log_section)
        log_section_layout.setContentsMargins(0, 0, 0, 0)
        log_section_layout.setSpacing(15)
        
        # Section header
        log_header = QLabel("📋 Operation Log")
        log_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        log_section_layout.addWidget(log_header)
        
        # Log output
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
        log_section_layout.addWidget(self.log_output)
        
        layout.addWidget(log_section)
        
        layout.addStretch()
        
        # Initial check
        QTimer.singleShot(100, self.check_repo_status)
        
    def create_subsection(self, title, description):
        """Create a styled subsection container"""
        group = QGroupBox()
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {CARD_BG};
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
                margin-top: 10px;
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        group_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                margin-bottom: 10px;
            }}
        """)
        group_layout.addWidget(desc_label)
        
        return group
        
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
        else:
            hover_color = color
            pressed_color = color
            
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {hover_color});
                color: white;
                border: none;
                padding: 10px 20px;
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
            QPushButton:disabled {{
                background: #cbd5e0;
                color: #a0aec0;
            }}
        """
        
    def check_repo_status(self):
        """Check if Frigate repository is cloned"""
        self.log_output.append("🔍 Checking repository status...")
        
        if os.path.exists(self.frigate_dir) and os.path.exists(os.path.join(self.frigate_dir, ".git")):
            # Get current branch
            try:
                result = subprocess.run(
                    ['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                    cwd=self.frigate_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                branch = result.stdout.strip() if result.returncode == 0 else "unknown"
                
                # Get current commit hash
                commit_result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    cwd=self.frigate_dir,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                commit_hash = commit_result.stdout.strip() if commit_result.returncode == 0 else "unknown"
                
                self.repo_status_label.setText(f"Status: ✅ Repository Found ({branch} @ {commit_hash})")
                self.repo_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: {TEXT_PRIMARY};
                        font-size: 16px;
                        font-weight: 500;
                        padding: 12px 16px;
                        background: #f0fdf4;
                        border: 1px solid #86efac;
                        border-radius: 8px;
                    }}
                """)
                # Show both Update and Fresh Clone buttons when repo exists
                self.update_repo_btn.setVisible(True)
                self.clone_repo_btn.setText("📥 Fresh Clone")
                self.log_output.append(f"✅ Repository found on branch: {branch} (commit: {commit_hash})")
                
                # Emit completed status since repository is found
                self.status_changed.emit(STATUS_COMPLETED)
                
            except Exception as e:
                self.log_output.append(f"⚠ Error checking repository: {str(e)}")
        else:
            self.repo_status_label.setText("Status: ❌ Repository Not Found")
            self.repo_status_label.setStyleSheet(f"""
                QLabel {{
                    color: {TEXT_PRIMARY};
                    font-size: 16px;
                    font-weight: 500;
                    padding: 12px 16px;
                    background: #fef2f2;
                    border: 1px solid #fca5a5;
                    border-radius: 8px;
                }}
            """)
            # Show only Fresh Clone button when repo doesn't exist
            self.update_repo_btn.setVisible(False)
            self.clone_repo_btn.setText("📥 Clone Repository")
            self.log_output.append("❌ Frigate repository not found")
            
            # Emit not started status since repository is not found
            self.status_changed.emit(STATUS_NOT_STARTED)
            
    def clone_fresh_repository(self):
        """Clone a fresh Frigate repository with config and version.py"""
        # Ask for confirmation if repo already exists
        if os.path.exists(self.frigate_dir):
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self,
                "Confirm Fresh Clone",
                "This will remove the existing Frigate directory and clone a fresh copy.\n\n"
                "⚠️ Warning: This will delete:\n"
                "  • Existing repository\n"
                "  • Local changes\n"
                "  • Current config (backup recommended)\n\n"
                "Continue with fresh clone?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                self.log_output.append("❌ Fresh clone cancelled by user")
                return
        
        self.log_output.append("📥 Starting fresh repository clone...")
        self.clone_repo_btn.setEnabled(False)
        self.update_repo_btn.setEnabled(False)
        self.check_repo_btn.setEnabled(False)
        self.clone_repo_btn.setText("🔄 Cloning...")
        
        # Create and start worker thread
        self.clone_worker = GitCloneWorker(
            'https://github.com/blakeblackshear/frigate.git',
            self.frigate_dir,
            remove_existing=os.path.exists(self.frigate_dir)
        )
        self.clone_worker.progress.connect(self.log_output.append)
        self.clone_worker.finished.connect(self.on_clone_finished)
        self.clone_worker.start()
    
    def on_clone_finished(self, success):
        """Handle clone completion"""
        # Re-enable buttons
        self.clone_repo_btn.setEnabled(True)
        self.update_repo_btn.setEnabled(True)
        self.check_repo_btn.setEnabled(True)
        self.clone_repo_btn.setText("📥 Fresh Clone")
        
        if success:
            # Create config directory and version.py
            self.create_config_and_version()
            self.check_repo_status()
        
        self.clone_worker = None
    
    def create_config_and_version(self):
        """Create config directory, version.py, and default config.yaml"""
        try:
            # Create config directory
            config_dir = os.path.join(self.frigate_dir, 'config')
            if not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
                self.log_output.append("📁 Created config directory")
            
            # Create version.py file in frigate/frigate/version.py
            version_dir = os.path.join(self.frigate_dir, 'frigate')
            version_file_path = os.path.join(version_dir, 'version.py')
            
            # Ensure frigate subdirectory exists
            if not os.path.exists(version_dir):
                os.makedirs(version_dir, exist_ok=True)
                self.log_output.append("📁 Created frigate subdirectory")
            
            # Create version.py with the specific version
            version_content = 'VERSION = "0.16.0-2458f667"\n'
            
            with open(version_file_path, 'w') as f:
                f.write(version_content)
            
            self.log_output.append("📝 Created version.py with version: 0.16.0-2458f667")
            
            # Create default config.yaml
            config_file_path = os.path.join(config_dir, 'config.yaml')
            
            if not os.path.exists(config_file_path):
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
        - path: rtsp://username:password@camera_ip:554/stream
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
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    f.write(default_config)
                
                self.log_output.append("📝 Created default config.yaml file")
                self.log_output.append(f"   📁 Location: {config_file_path}")
            else:
                self.log_output.append("ℹ️ Config file already exists, skipping creation")
                
        except Exception as e:
            self.log_output.append(f"⚠️ Error creating config/version files: {str(e)}")
            
    def update_repository(self):
        """Update the Frigate repository"""
        self.log_output.append("🔄 Updating repository...")
        self.update_repo_btn.setEnabled(False)
        self.clone_repo_btn.setEnabled(False)
        self.check_repo_btn.setEnabled(False)
        self.update_repo_btn.setText("🔄 Updating...")
        
        try:
            # First, check for local changes
            status_result = subprocess.run(
                ['git', 'status', '--porcelain'],
                cwd=self.frigate_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if status_result.stdout.strip():
                self.log_output.append("⚠️ Local changes detected in repository")
                self.log_output.append("💾 Stashing local changes...")
                stash_result = subprocess.run(
                    ['git', 'stash'],
                    cwd=self.frigate_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if stash_result.returncode == 0:
                    self.log_output.append("✅ Local changes stashed")
            
            # Get current branch
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=self.frigate_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            current_branch = branch_result.stdout.strip()
            
            if not current_branch:
                self.log_output.append("⚠️ Repository in detached HEAD state")
                current_branch = "main"  # Default to main
            
            self.log_output.append(f"📍 Current branch: {current_branch}")
            
            # Fetch latest changes
            self.log_output.append("📡 Fetching latest changes from remote...")
            fetch_result = subprocess.run(
                ['git', 'fetch', 'origin', current_branch],
                cwd=self.frigate_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if fetch_result.returncode != 0:
                self.log_output.append(f"❌ Fetch failed: {fetch_result.stderr}")
                self.update_repo_btn.setEnabled(True)
                self.clone_repo_btn.setEnabled(True)
                self.check_repo_btn.setEnabled(True)
                self.update_repo_btn.setText("🔄 Update/Pull")
                return
            
            # Check if there are updates available
            rev_list_result = subprocess.run(
                ['git', 'rev-list', '--count', f'HEAD..origin/{current_branch}'],
                cwd=self.frigate_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            commits_behind = rev_list_result.stdout.strip()
            
            if commits_behind == "0":
                self.log_output.append("✅ Repository is already up to date!")
                self.log_output.append("ℹ️ You have the latest version")
                self.update_repo_btn.setEnabled(True)
                self.clone_repo_btn.setEnabled(True)
                self.check_repo_btn.setEnabled(True)
                self.update_repo_btn.setText("🔄 Update/Pull")
                return
            else:
                self.log_output.append(f"📥 {commits_behind} new commit(s) available")
                
                # Show what's new
                log_result = subprocess.run(
                    ['git', 'log', '--oneline', '--decorate', f'HEAD..origin/{current_branch}', '-5'],
                    cwd=self.frigate_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if log_result.stdout.strip():
                    self.log_output.append("📋 Recent changes:")
                    for line in log_result.stdout.strip().split('\n')[:5]:
                        self.log_output.append(f"  • {line}")
            
            # Pull latest changes
            self.log_output.append(f"⬇️ Pulling latest changes for branch: {current_branch}")
            pull_result = subprocess.run(
                ['git', 'pull', 'origin', current_branch],
                cwd=self.frigate_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if pull_result.returncode == 0:
                self.log_output.append("✅ Repository updated successfully!")
                if pull_result.stdout.strip() and "Already up to date" not in pull_result.stdout:
                    self.log_output.append(pull_result.stdout)
                
                # Show current commit
                commit_result = subprocess.run(
                    ['git', 'log', '-1', '--oneline'],
                    cwd=self.frigate_dir,
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                if commit_result.stdout.strip():
                    self.log_output.append(f"📍 Current commit: {commit_result.stdout.strip()}")
            else:
                self.log_output.append(f"❌ Update failed: {pull_result.stderr}")
                
        except subprocess.TimeoutExpired:
            self.log_output.append("❌ Operation timed out")
        except Exception as e:
            self.log_output.append(f"❌ Error: {str(e)}")
        finally:
            self.update_repo_btn.setEnabled(True)
            self.clone_repo_btn.setEnabled(True)
            self.check_repo_btn.setEnabled(True)
            self.update_repo_btn.setText("🔄 Update/Pull")
            # Refresh status
            QTimer.singleShot(100, self.check_repo_status)
            
    def build_image(self):
        """Build the Docker image"""
        self.log_output.append("🔨 Starting Docker image build...")
        self.build_btn.setEnabled(False)
        self.build_btn.setText("🔄 Building...")
        
        # Build command
        build_script = os.path.join(self.frigate_dir, "docker", "memryx", "build.sh")
        
        if not os.path.exists(build_script):
            self.log_output.append(f"❌ Build script not found: {build_script}")
            self.build_btn.setEnabled(True)
            self.build_btn.setText("🔨 Build Image")
            return
            
        try:
            self.log_output.append("🔄 Running build script...")
            process = subprocess.Popen(
                ['bash', build_script],
                cwd=self.frigate_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            # Stream output
            for line in process.stdout:
                self.log_output.append(line.strip())
                
            process.wait()
            
            if process.returncode == 0:
                self.log_output.append("🎉 Build completed successfully!")
                self.check_build_status()
            else:
                self.log_output.append(f"❌ Build failed with code {process.returncode}")
                
        except Exception as e:
            self.log_output.append(f"❌ Error: {str(e)}")
        finally:
            self.build_btn.setEnabled(True)
            self.build_btn.setText("🔨 Build Image")
            
    def rebuild_image(self):
        """Rebuild the Docker image (with --no-cache)"""
        reply = QMessageBox.question(
            self, "Rebuild Image",
            "This will rebuild the Docker image from scratch.\n\n"
            "This may take a long time. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.build_image()
            
    def view_build_logs(self):
        """View previous build logs"""
        self.log_output.append("📋 Build logs are displayed above during build process")


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
        """Initialize the UI components with clean, professional design"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(25)
        
        # Section header with icon
        header = QLabel("⚙️ Configuration Options")
        header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 10px;
            }}
        """)
        layout.addWidget(header)
        
        # Subtitle
        subtitle = QLabel("Choose how you want to configure Frigate")
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 15px;
            }}
        """)
        layout.addWidget(subtitle)
        
        # Three configuration methods in a clean horizontal layout
        methods_container = QWidget()
        methods_layout = QHBoxLayout(methods_container)
        methods_layout.setSpacing(20)
        methods_layout.setContentsMargins(0, 0, 0, 0)
        
        # Method 1: Simple Camera Configuration
        method1 = QWidget()
        method1_layout = QVBoxLayout(method1)
        method1_layout.setSpacing(8)
        method1_layout.setContentsMargins(0, 0, 0, 0)
        
        method1_header = QLabel("📹  Simple Camera Configuration")
        method1_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        method1_layout.addWidget(method1_header)
        
        method1_desc = QLabel("Quick setup for adding cameras with default settings")
        method1_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        method1_desc.setWordWrap(True)
        method1_layout.addWidget(method1_desc)
        
        self.camera_btn = QPushButton("Open Camera Config")
        self.camera_btn.clicked.connect(self.open_camera_gui)
        self.camera_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        self.camera_btn.setMinimumHeight(38)
        method1_layout.addWidget(self.camera_btn)
        
        methods_layout.addWidget(method1)
        
        # Vertical divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.VLine)
        divider1.setStyleSheet(f"background: {BORDER_COLOR}; max-width: 1px;")
        methods_layout.addWidget(divider1)
        
        # Method 2: Advanced Configuration Editor
        method2 = QWidget()
        method2_layout = QVBoxLayout(method2)
        method2_layout.setSpacing(8)
        method2_layout.setContentsMargins(0, 0, 0, 0)
        
        method2_header = QLabel("🔧  Advanced Configuration Editor")
        method2_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        method2_layout.addWidget(method2_header)
        
        method2_desc = QLabel("Full-featured GUI for detectors, models, cameras, and all options")
        method2_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        method2_desc.setWordWrap(True)
        method2_layout.addWidget(method2_desc)
        
        self.advanced_btn = QPushButton("Open Advanced Editor")
        self.advanced_btn.clicked.connect(self.open_advanced_config)
        self.advanced_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.advanced_btn.setMinimumHeight(38)
        method2_layout.addWidget(self.advanced_btn)
        
        methods_layout.addWidget(method2)
        
        # Vertical divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.VLine)
        divider2.setStyleSheet(f"background: {BORDER_COLOR}; max-width: 1px;")
        methods_layout.addWidget(divider2)
        
        # Method 3: Manual YAML Editor
        method3 = QWidget()
        method3_layout = QVBoxLayout(method3)
        method3_layout.setSpacing(8)
        method3_layout.setContentsMargins(0, 0, 0, 0)
        
        method3_header = QLabel("📝  Manual YAML Editor")
        method3_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        method3_layout.addWidget(method3_header)
        
        method3_desc = QLabel("Direct text editing of config.yaml (for advanced users)")
        method3_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        method3_desc.setWordWrap(True)
        method3_layout.addWidget(method3_desc)
        
        self.manual_btn = QPushButton("Open YAML Editor")
        self.manual_btn.clicked.connect(self.open_manual_editor)
        self.manual_btn.setStyleSheet(self.get_button_style(WARNING_COLOR))
        self.manual_btn.setMinimumHeight(38)
        method3_layout.addWidget(self.manual_btn)
        
        methods_layout.addWidget(method3)
        
        layout.addWidget(methods_container)
        
        # Spacer
        layout.addSpacing(25)
        
        # Advanced settings note (before FFmpeg section)
        advanced_note_container = QHBoxLayout()
        advanced_note_container.setContentsMargins(0, 0, 0, 0)
        
        advanced_note = QLabel(
            "💡 <b>Advanced Settings:</b> For more advanced zone settings, notifications, and other options, "
            "start Frigate first (Section 4), then access the web interface at "
            '<a href="http://localhost:5000/settings" style="color: #4a90a4; text-decoration: none;"><b>http://localhost:5000/settings</b></a>'
        )
        advanced_note.setOpenExternalLinks(True)
        advanced_note.setTextInteractionFlags(Qt.TextBrowserInteraction)
        advanced_note.setWordWrap(False)
        advanced_note.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        advanced_note.setStyleSheet("""
            QLabel {
                color: #1e40af;
                font-size: 14px;
                padding: 12px 16px;
                background: #eff6ff;
                border-left: 3px solid #60a5fa;
                border-radius: 8px;
            }
        """)
        advanced_note_container.addWidget(advanced_note)
        advanced_note_container.addStretch()
        layout.addLayout(advanced_note_container)
        
        # Spacer
        layout.addSpacing(25)
        
        # Divider before FFmpeg section
        divider_ffmpeg = QFrame()
        divider_ffmpeg.setFrameShape(QFrame.HLine)
        divider_ffmpeg.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px;")
        layout.addWidget(divider_ffmpeg)
        
        # Spacer
        layout.addSpacing(10)
        
        # FFmpeg Hardware Acceleration (separate optional feature)
        ffmpeg_section = QWidget()
        ffmpeg_layout = QVBoxLayout(ffmpeg_section)
        ffmpeg_layout.setContentsMargins(0, 0, 0, 0)
        ffmpeg_layout.setSpacing(10)
        
        ffmpeg_header = QLabel("⚡  FFmpeg Hardware Acceleration (Intel & AMD VAAPI)")
        ffmpeg_header.setStyleSheet(f"color: {TEXT_PRIMARY}; font-size: 14px; font-weight: 600;")
        ffmpeg_layout.addWidget(ffmpeg_header)
        
        ffmpeg_desc = QLabel("Install VA-API drivers for hardware-accelerated video decoding (Intel/AMD Systems.)")
        ffmpeg_desc.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 14px;")
        ffmpeg_desc.setWordWrap(True)
        ffmpeg_layout.addWidget(ffmpeg_desc)
        
        # Hardware compatibility warning (inline, yellow background only on text)
        compat_warning_container = QHBoxLayout()
        compat_warning_container.setContentsMargins(0, 0, 0, 0)
        
        warning_text = QLabel("⚠️  <b>Hardware Compatibility:</b> This feature uses VA-API and is only supported on <b>Intel and AMD Systems</b>. For NVIDIA or other hardware, see the documentation below.")
        warning_text.setStyleSheet("""
            QLabel {
                color: #92400e;
                font-size: 14px;
                background: #fef3c7;
                padding: 10px 15px;
                border-radius: 6px;
                border-left: 4px solid #f59e0b;
            }
        """)
        warning_text.setWordWrap(False)
        warning_text.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        
        compat_warning_container.addWidget(warning_text)
        compat_warning_container.addStretch()
        ffmpeg_layout.addLayout(compat_warning_container)
        
        # Status and button in horizontal layout
        ffmpeg_controls = QWidget()
        ffmpeg_controls_layout = QHBoxLayout(ffmpeg_controls)
        ffmpeg_controls_layout.setContentsMargins(0, 0, 0, 0)
        ffmpeg_controls_layout.setSpacing(15)
        
        # Status label
        self.ffmpeg_status_label = QLabel("Status: Checking...")
        self.ffmpeg_status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                padding: 6px 12px;
                background: #f7fafc;
                border-radius: 4px;
            }}
        """)
        ffmpeg_controls_layout.addWidget(self.ffmpeg_status_label)
        
        # Install button
        self.ffmpeg_install_btn = QPushButton("Install VA-API Drivers")
        self.ffmpeg_install_btn.clicked.connect(self.install_ffmpeg_packages)
        self.ffmpeg_install_btn.setStyleSheet(self.get_button_style("#8b5cf6"))
        self.ffmpeg_install_btn.setMinimumHeight(38)
        self.ffmpeg_install_btn.setMinimumWidth(180)
        ffmpeg_controls_layout.addWidget(self.ffmpeg_install_btn)
        
        # Documentation link button
        self.ffmpeg_docs_btn = QPushButton("📖 View Documentation")
        self.ffmpeg_docs_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://docs.frigate.video/configuration/ffmpeg_presets/")))
        self.ffmpeg_docs_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.ffmpeg_docs_btn.setMinimumHeight(38)
        self.ffmpeg_docs_btn.setMinimumWidth(180)
        ffmpeg_controls_layout.addWidget(self.ffmpeg_docs_btn)
        
        ffmpeg_controls_layout.addStretch()
        ffmpeg_layout.addWidget(ffmpeg_controls)
        
        layout.addWidget(ffmpeg_section)
        
        # Spacer
        layout.addSpacing(20)
        
        # Info section (clean design with left accent bar)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        info_widget.setStyleSheet(f"""
            QWidget {{
                background: #f7fafc;
                border-radius: 8px;
                border-left: 4px solid {PRIMARY_COLOR};
            }}
        """)
        
        # Config file path with clear label
        config_path_header = QLabel("Configuration File:")
        config_path_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                background: transparent;
            }}
        """)
        info_layout.addWidget(config_path_header)
        
        self.config_info_label = QLabel(f"{self.config_file}")
        self.config_info_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                font-family: 'Courier New', monospace;
                background: transparent;
                margin-top: 4px;
            }}
        """)
        self.config_info_label.setWordWrap(True)
        info_layout.addWidget(self.config_info_label)
        
        self.camera_summary_label = QLabel("📹 Configured Cameras: Checking...")
        self.camera_summary_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 16px;
                background: transparent;
            }}
        """)
        info_layout.addWidget(self.camera_summary_label)
        
        layout.addWidget(info_widget)
        
        layout.addStretch()
        
        # Initial checks
        QTimer.singleShot(100, self.check_camera_config)
        QTimer.singleShot(200, self.check_ffmpeg_status)
    
    def create_subsection(self, title, description):
        """Create a styled subsection container"""
        group = QGroupBox()
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {CARD_BG};
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
                margin-top: 10px;
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        group_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                margin-bottom: 10px;
            }}
        """)
        group_layout.addWidget(desc_label)
        
        return group
        
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
                    camera_names = list(config['cameras'].keys())
                    
                    self.camera_summary_label.setText(
                        f"Configured Cameras: {camera_count}\n" +
                        "\n".join([f"  • {name}" for name in camera_names[:5]]) +
                        (f"\n  ... and {camera_count - 5} more" if camera_count > 5 else "")
                    )
                    self.status_changed.emit(STATUS_COMPLETED)
                else:
                    self.camera_summary_label.setText("Configured Cameras: 0 (No cameras configured)")
            else:
                self.camera_summary_label.setText("Configured Cameras: Config file not found")
                
        except Exception as e:
            self.camera_summary_label.setText(f"Error reading config: {str(e)}")
            
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


# ============================================================================
# LOG STREAMING WORKER
# ============================================================================
class LogStreamWorker(QThread):
    """Background worker for streaming Docker container logs"""
    log_line = Signal(str)
    
    def __init__(self, container_name='frigate'):
        super().__init__()
        self.container_name = container_name
        self._stop_requested = False
        self.process = None
        
    def run(self):
        """Stream container logs"""
        try:
            self.process = subprocess.Popen(
                ['docker', 'logs', '-f', self.container_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            for line in self.process.stdout:
                if self._stop_requested:
                    break
                if line:
                    self.log_line.emit(line.rstrip())
                    
        except Exception as e:
            self.log_line.emit(f"❌ Log streaming error: {str(e)}")
        finally:
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    
    def stop(self):
        """Stop log streaming"""
        self._stop_requested = True
        if self.process:
            self.process.terminate()
            

# ============================================================================
# LAUNCH & MONITOR WIDGET (Section 4)
# ============================================================================  
class LaunchMonitorWidget(QWidget):
    """Widget for launching and monitoring Frigate"""
    
    status_changed = Signal(str)
    
    def __init__(self, script_dir, parent=None):
        super().__init__(parent)
        self.script_dir = script_dir
        self.frigate_dir = os.path.join(script_dir, "frigate")
        self.is_running = False
        self.status_timer = None
        self.log_worker = None
        self.setup_ui()
        
    def setup_ui(self):
        """Initialize the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(30)  # Increased spacing for breathing room
        
        # ===== Step 1: Build Docker Image =====
        build_section = QWidget()
        build_section_layout = QVBoxLayout(build_section)
        build_section_layout.setContentsMargins(0, 0, 0, 0)
        build_section_layout.setSpacing(15)
        
        # Section header with icon
        build_header = QLabel("🐳 Build Docker Image")
        build_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        build_section_layout.addWidget(build_header)
        
        # Important note - soft blue (content-width)
        build_note_container = QHBoxLayout()
        build_note_container.setContentsMargins(0, 0, 0, 0)
        
        build_note = QLabel(
            "💡 <b>Step 1:</b> Build the Docker image before starting Frigate. "
            "<b>Rebuild</b> if you modified any Frigate files.<br>"
            "⚠️ <i>Start Frigate only after the build button is re-enabled</i>"
        )
        build_note.setWordWrap(False)
        build_note.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        build_note.setStyleSheet(f"""
            QLabel {{
                color: #1e40af;
                font-size: 16px;
                padding: 12px 16px;
                background: #eff6ff;
                border-left: 3px solid #60a5fa;
                border-radius: 8px;
                line-height: 1.5;
            }}
        """)
        build_note_container.addWidget(build_note)
        build_note_container.addStretch()
        build_section_layout.addLayout(build_note_container)
        
        # Build status - content-width
        build_status_container = QHBoxLayout()
        build_status_container.setContentsMargins(0, 0, 0, 0)
        
        self.build_status_label = QLabel("Docker image: 🔍 frigate:latest (Ready)")
        self.build_status_label.setWordWrap(False)
        self.build_status_label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.build_status_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 500;
                padding: 14px 16px;
                background: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 8px;
            }}
        """)
        build_status_container.addWidget(self.build_status_label)
        build_status_container.addStretch()
        build_section_layout.addLayout(build_status_container)
        
        # Build buttons - more spaced out
        build_buttons = QHBoxLayout()
        build_buttons.setSpacing(12)
        
        self.build_btn = QPushButton("🔨 Build Image")
        self.build_btn.clicked.connect(self.build_image)
        self.build_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        self.build_btn.setMinimumHeight(48)
        self.build_btn.setMinimumWidth(160)
        
        self.stop_build_btn = QPushButton("⏹️ Stop")
        self.stop_build_btn.clicked.connect(self.stop_build)
        self.stop_build_btn.setStyleSheet(f"""
            QPushButton {{
                background: #6b7280;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #4b5563;
            }}
            QPushButton:pressed {{
                background: #374151;
            }}
        """)
        self.stop_build_btn.setMinimumHeight(48)
        self.stop_build_btn.setMinimumWidth(120)
        self.stop_build_btn.setVisible(False)
        
        self.delete_image_btn = QPushButton("🗑️ Delete Image")
        self.delete_image_btn.clicked.connect(self.delete_image)
        self.delete_image_btn.setStyleSheet(self.get_button_style(ERROR_COLOR))
        self.delete_image_btn.setMinimumHeight(48)
        self.delete_image_btn.setMinimumWidth(160)
        
        build_buttons.addWidget(self.build_btn)
        build_buttons.addWidget(self.stop_build_btn)
        build_buttons.addWidget(self.delete_image_btn)
        build_buttons.addStretch()
        
        build_section_layout.addLayout(build_buttons)
        
        layout.addWidget(build_section)
        
        # Elegant divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.HLine)
        divider1.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider1)
        
        # ===== Step 2: Control Frigate Service =====
        control_section = QWidget()
        control_section_layout = QVBoxLayout(control_section)
        control_section_layout.setContentsMargins(0, 0, 0, 0)
        control_section_layout.setSpacing(15)
        
        # Section header
        control_header = QLabel("⚙️ Control Frigate Service")
        control_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        control_section_layout.addWidget(control_header)
        
        # Workflow guidance note - content-width
        workflow_note_container = QHBoxLayout()
        workflow_note_container.setContentsMargins(0, 0, 0, 0)
        
        workflow_note = QLabel(
            "📝 <b>Step 2:</b> After building, click <b>'▶ Start'</b> to launch Frigate. "
            "Then <b>click '📹 Live View'</b> button below to access the monitoring site, or scroll down to view live logs."
        )
        workflow_note.setWordWrap(False)
        workflow_note.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        workflow_note.setStyleSheet(f"""
            QLabel {{
                color: #047857;
                font-size: 16px;
                padding: 12px 16px;
                background: #d1fae5;
                border-left: 3px solid #34d399;
                border-radius: 8px;
                line-height: 1.5;
            }}
        """)
        workflow_note_container.addWidget(workflow_note)
        workflow_note_container.addStretch()
        control_section_layout.addLayout(workflow_note_container)
        
        # Important note - content-width
        control_note_container = QHBoxLayout()
        control_note_container.setContentsMargins(0, 0, 0, 0)
        
        control_note = QLabel(
            "💡 <b>Restart required:</b> If you change config.yaml (cameras, settings), restart Frigate to apply changes."
        )
        control_note.setWordWrap(False)
        control_note.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        control_note.setStyleSheet(f"""
            QLabel {{
                color: #1e40af;
                font-size: 16px;
                padding: 12px 16px;
                background: #eff6ff;
                border-left: 3px solid #60a5fa;
                border-radius: 8px;
                line-height: 1.5;
            }}
        """)
        control_note_container.addWidget(control_note)
        control_note_container.addStretch()
        control_section_layout.addLayout(control_note_container)
        
        # Status display - content-width
        status_container = QHBoxLayout()
        status_container.setContentsMargins(0, 0, 0, 0)
        
        self.status_display = QLabel("Status: 🔴 Stopped")
        self.status_display.setWordWrap(False)
        self.status_display.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        self.status_display.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 14px;
                font-weight: 600;
                padding: 16px 20px;
                background: #fee2e2;
                border: 1px solid #fca5a5;
                border-radius: 8px;
            }}
        """)
        status_container.addWidget(self.status_display)
        status_container.addStretch()
        control_section_layout.addLayout(status_container)
        
        # Control buttons - larger and more spaced
        control_buttons = QHBoxLayout()
        control_buttons.setSpacing(12)
        
        self.start_btn = QPushButton("▶ Start")
        self.start_btn.clicked.connect(self.start_frigate)
        self.start_btn.setStyleSheet(self.get_button_style(SUCCESS_COLOR))
        self.start_btn.setMinimumHeight(48)
        self.start_btn.setMinimumWidth(140)
        
        self.stop_btn = QPushButton("⏹ Stop")
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
        
        control_buttons.addWidget(self.start_btn)
        control_buttons.addWidget(self.stop_btn)
        control_buttons.addWidget(self.restart_btn)
        control_buttons.addStretch()
        
        control_section_layout.addLayout(control_buttons)
        
        layout.addWidget(control_section)
        
        # Elegant divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.HLine)
        divider2.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider2)
        
        # ===== Step 3: Access Frigate =====
        access_section = QWidget()
        access_section_layout = QVBoxLayout(access_section)
        access_section_layout.setContentsMargins(0, 0, 0, 0)
        access_section_layout.setSpacing(15)
        
        # Section header
        access_header = QLabel("🌐 Access Frigate")
        access_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        access_section_layout.addWidget(access_header)
        
        # Quick access buttons - larger
        access_buttons = QHBoxLayout()
        access_buttons.setSpacing(12)
        
        self.live_view_btn = QPushButton("📹 Live View")
        self.live_view_btn.clicked.connect(lambda: self.open_web_ui("/cameras"))
        self.live_view_btn.setStyleSheet(self.get_button_style(PRIMARY_COLOR))
        self.live_view_btn.setMinimumHeight(48)
        self.live_view_btn.setMinimumWidth(160)
        
        self.events_btn = QPushButton("📊 Events")
        self.events_btn.clicked.connect(lambda: self.open_web_ui("/events"))
        self.events_btn.setStyleSheet(self.get_button_style(INFO_COLOR))
        self.events_btn.setMinimumHeight(48)
        self.events_btn.setMinimumWidth(160)
        
        access_buttons.addWidget(self.live_view_btn)
        access_buttons.addWidget(self.events_btn)
        access_buttons.addStretch()
        
        access_section_layout.addLayout(access_buttons)
        
        # URL display - more prominent
        self.url_label = QLabel("🌐 http://localhost:5000")
        self.url_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-family: 'Courier New', monospace;
                font-weight: 500;
                padding: 14px 16px;
                background: #f0fdf4;
                border: 1px solid #86efac;
                border-radius: 8px;
            }}
        """)
        access_section_layout.addWidget(self.url_label)
        
        layout.addWidget(access_section)
        
        # Elegant divider before logs
        divider3 = QFrame()
        divider3.setFrameShape(QFrame.HLine)
        divider3.setStyleSheet(f"background: {BORDER_COLOR}; max-height: 1px; margin: 20px 0;")
        layout.addWidget(divider3)
        
        # ===== Build Logs (Moved to End) =====
        logs_section = QWidget()
        logs_section_layout = QVBoxLayout(logs_section)
        logs_section_layout.setContentsMargins(0, 0, 0, 0)
        logs_section_layout.setSpacing(12)
        
        # Logs header
        logs_header = QLabel("📋 Live Logs")
        logs_header.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: 600;
            }}
        """)
        logs_section_layout.addWidget(logs_header)
        
        # Logs guidance note - content-width
        logs_note_container = QHBoxLayout()
        logs_note_container.setContentsMargins(0, 0, 0, 0)
        
        logs_note = QLabel(
            "📺 <b>Step 3:</b> View real-time logs here after starting Frigate. "
            "Watch for startup messages and any errors."
        )
        logs_note.setWordWrap(False)
        logs_note.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Preferred)
        logs_note.setStyleSheet(f"""
            QLabel {{
                color: #7c3aed;
                font-size: 16px;
                padding: 12px 16px;
                background: #f3e8ff;
                border-left: 3px solid #a78bfa;
                border-radius: 8px;
                line-height: 1.5;
            }}
        """)
        logs_note_container.addWidget(logs_note)
        logs_note_container.addStretch()
        logs_section_layout.addLayout(logs_note_container)
        
        # Build logs with better styling
        self.logs_output = QTextEdit()
        self.logs_output.setReadOnly(True)
        self.logs_output.setMinimumHeight(150)
        self.logs_output.setMaximumHeight(250)
        self.logs_output.setStyleSheet(f"""
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
        logs_section_layout.addWidget(self.logs_output)
        
        layout.addWidget(logs_section)
        
        layout.addStretch()
        
        # Start status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self.check_status)
        self.status_timer.start(5000)  # Check every 5 seconds
        
        # Initial checks
        QTimer.singleShot(100, self.check_status)
        QTimer.singleShot(200, self.check_build_status)
        
    def create_subsection(self, title, description):
        """Create a styled subsection container"""
        group = QGroupBox()
        group.setStyleSheet(f"""
            QGroupBox {{
                background: {CARD_BG};
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 15px;
                margin-top: 10px;
            }}
        """)
        
        group_layout = QVBoxLayout(group)
        
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_PRIMARY};
                font-size: 16px;
                font-weight: bold;
            }}
        """)
        group_layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet(f"""
            QLabel {{
                color: {TEXT_SECONDARY};
                font-size: 14px;
                margin-bottom: 10px;
            }}
        """)
        group_layout.addWidget(desc_label)
        
        return group
        
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
        else:
            hover_color = color
            pressed_color = color
            
        return f"""
            QPushButton {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {color}, stop:1 {hover_color});
                color: white;
                border: none;
                padding: 10px 20px;
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
            QPushButton:disabled {{
                background: #cbd5e0;
                color: #a0aec0;
            }}
        """
        
    def check_status(self):
        """Check Frigate container status"""
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', 'name=frigate', '--format', '{{.Status}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                self.is_running = True
                self.status_display.setText(f"Status: 🟢 Running\n{result.stdout.strip()}")
                self.status_display.setStyleSheet(f"""
                    QLabel {{
                        color: #065f46;
                        font-size: 16px;
                        font-weight: 600;
                        padding: 15px;
                        background: #ecfdf5;
                        border-radius: 6px;
                        border: 1px solid #a7f3d0;
                    }}
                """)
                
                # Only update button states if no docker operation is in progress
                has_active_operation = False
                if self.parent() and hasattr(self.parent(), 'docker_worker') and self.parent().docker_worker is not None:
                    has_active_operation = self.parent().docker_worker.isRunning()
                
                if not has_active_operation:
                    self.start_btn.setEnabled(False)
                    self.stop_btn.setEnabled(True)
                    self.restart_btn.setEnabled(True)
                    self.status_changed.emit(STATUS_COMPLETED)
                    
                # Start log streaming if not already streaming
                if not self.log_worker or not self.log_worker.isRunning():
                    QTimer.singleShot(500, self.start_log_streaming)
            else:
                self.is_running = False
                self.status_display.setText("Status: 🔴 Stopped")
                self.status_display.setStyleSheet(f"""
                    QLabel {{
                        color: #991b1b;
                        font-size: 16px;
                        font-weight: 600;
                        padding: 15px;
                        background: #fef2f2;
                        border-radius: 6px;
                        border: 1px solid #fecaca;
                    }}
                """)
                
                # Only enable Start button if image exists AND no docker operation is in progress
                # Check if parent (launcher) has an active docker worker
                has_active_operation = False
                if self.parent() and hasattr(self.parent(), 'docker_worker') and self.parent().docker_worker is not None:
                    has_active_operation = self.parent().docker_worker.isRunning()
                
                if not has_active_operation:
                    # Only enable Start button if image exists
                    image_check = subprocess.run(
                        ['docker', 'images', '-q', 'frigate:latest'],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    self.start_btn.setEnabled(bool(image_check.stdout.strip()))
                    self.stop_btn.setEnabled(False)
                    self.restart_btn.setEnabled(False)
                # If operation is in progress, don't change button states
                
        except Exception as e:
            self.status_display.setText(f"Status: ❓ Error: {str(e)}")
            
    def refresh_status(self):
        """Refresh system status - removed from UI"""
        pass
            
    def check_build_status(self):
        """Check if Docker image is built"""
        try:
            result = subprocess.run(
                ['docker', 'images', '-q', 'frigate:latest'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.stdout.strip():
                self.build_status_label.setText("Docker Image: ✅ frigate:latest (Ready)")
                self.build_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: #065f46;
                        font-size: 16px;
                        font-weight: 600;
                        padding: 10px;
                        background: #ecfdf5;
                        border-radius: 6px;
                        border: 1px solid #a7f3d0;
                    }}
                """)
                self.build_btn.setText("🔨 Rebuild Image")
                self.logs_output.append("✅ Docker image 'frigate:latest' found")
                
                # Enable Start button when image exists
                if hasattr(self, 'start_btn'):
                    self.start_btn.setEnabled(True)
            else:
                self.build_status_label.setText("Docker Image: ❌ Not Built")
                self.build_status_label.setStyleSheet(f"""
                    QLabel {{
                        color: #991b1b;
                        font-size: 16px;
                        font-weight: 600;
                        padding: 10px;
                        background: #fef2f2;
                        border-radius: 6px;
                        border: 1px solid #fecaca;
                    }}
                """)
                self.build_btn.setText("🔨 Build Image")
                self.logs_output.append("⚠ Docker image not built yet")
                
                # Disable Start button when no image exists
                if hasattr(self, 'start_btn'):
                    self.start_btn.setEnabled(False)
                
        except Exception as e:
            self.logs_output.append(f"⚠ Error checking Docker image: {str(e)}")
    
    def build_image(self):
        """Build the Frigate Docker image"""
        self.logs_output.append("\n🔨 ====== Starting Docker Image Build ======")
        self.logs_output.append("⏰ This may take 10-15 minutes...")
        self.build_btn.setEnabled(False)
        self.build_btn.setText("🔄 Building...")
        self.stop_build_btn.setVisible(True)  # Show stop button
        self.delete_image_btn.setEnabled(False)
        
        # Disable Start/Stop/Restart buttons during build
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(False)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(False)
        if hasattr(self, 'restart_btn'):
            self.restart_btn.setEnabled(False)
        
        # Check if repository exists
        if not os.path.exists(self.frigate_dir):
            self.logs_output.append("❌ Error: Frigate repository not found!")
            self.logs_output.append("💡 Please clone the repository first in the 'Install Frigate' section")
            self.build_btn.setEnabled(True)
            self.build_btn.setText("🔨 Build Image")
            self.stop_build_btn.setVisible(False)  # Hide stop button
            self.delete_image_btn.setEnabled(True)
            # Re-enable control buttons
            if hasattr(self, 'start_btn'):
                self.start_btn.setEnabled(True)
            if hasattr(self, 'stop_btn'):
                self.stop_btn.setEnabled(True)
            if hasattr(self, 'restart_btn'):
                self.restart_btn.setEnabled(True)
            self.check_build_status()
            return
        
        # Use DockerWorker to build the image
        from frigate_launcher import DockerWorker
        self.docker_worker = DockerWorker(self.script_dir, action='build')
        self.docker_worker.progress.connect(self.logs_output.append)
        self.docker_worker.finished.connect(self.on_build_finished)
        self.docker_worker.start()
    
    def on_build_finished(self, success):
        """Handle build completion"""
        self.build_btn.setEnabled(True)
        self.build_btn.setText("🔨 Build Image")
        self.stop_build_btn.setVisible(False)  # Hide stop button
        self.delete_image_btn.setEnabled(True)
        
        # Re-enable Start/Stop/Restart buttons
        if hasattr(self, 'start_btn'):
            self.start_btn.setEnabled(True)
        if hasattr(self, 'stop_btn'):
            self.stop_btn.setEnabled(True)
        if hasattr(self, 'restart_btn'):
            self.restart_btn.setEnabled(True)
        
        if success:
            self.logs_output.append("\n🎉 Build completed successfully!")
            self.check_build_status()
        else:
            self.logs_output.append("\n❌ Build failed - check the log above for details")
            self.check_build_status()
    
    def stop_build(self):
        """Stop the Docker build process"""
        if hasattr(self, 'docker_worker') and self.docker_worker.isRunning():
            reply = QMessageBox.question(
                self, "Stop Build",
                "⚠️ Are you sure you want to stop the Docker build process?\n\n"
                "The build will be interrupted and you'll need to start over.\n\n"
                "💡 If the build appears stuck:\n"
                "   • Stop the build using this button\n"
                "   • Wait for the process to fully terminate\n"
                "   • Check your internet connection\n"
                "   • Try building again\n"
                "   • If it keeps failing, check the logs for errors",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.logs_output.append("\n⏹️ Stopping build process...")
                self.docker_worker.stop()
                self.docker_worker.wait()  # Wait for thread to finish
                
                self.logs_output.append("⏹️ Build process stopped by user")
                self.build_btn.setEnabled(True)
                self.build_btn.setText("🔨 Build Image")
                self.stop_build_btn.setVisible(False)
                self.delete_image_btn.setEnabled(True)
                
                # Re-enable control buttons
                if hasattr(self, 'start_btn'):
                    self.start_btn.setEnabled(True)
                if hasattr(self, 'stop_btn'):
                    self.stop_btn.setEnabled(True)
                if hasattr(self, 'restart_btn'):
                    self.restart_btn.setEnabled(True)
                
                self.check_build_status()
    
    def delete_image(self):
        """Delete the Frigate Docker image"""
        reply = QMessageBox.question(
            self, "Delete Frigate Image",
            "⚠️ This will delete the Frigate Docker image.\n\n"
            "You will need to rebuild the image before you can start Frigate again.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.logs_output.append("\n�️ ====== Deleting Frigate Docker Image ======")
            self.delete_image_btn.setEnabled(False)
            self.delete_image_btn.setText("🔄 Deleting...")
            
            try:
                # Check if image exists
                result = subprocess.run(
                    ['docker', 'images', '-q', 'frigate'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if not result.stdout.strip():
                    self.logs_output.append("ℹ️ Frigate image not found - nothing to delete")
                    self.delete_image_btn.setEnabled(True)
                    self.delete_image_btn.setText("🗑️ Delete Image")
                    return
                
                # Delete the image
                self.logs_output.append("🗑️ Deleting Frigate Docker image...")
                result = subprocess.run(
                    ['docker', 'rmi', 'frigate'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    self.logs_output.append("✅ Frigate image deleted successfully!")
                    self.logs_output.append("💡 You will need to rebuild the image before starting Frigate")
                else:
                    self.logs_output.append(f"❌ Failed to delete image: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                self.logs_output.append("❌ Delete operation timed out")
            except Exception as e:
                self.logs_output.append(f"❌ Error deleting image: {str(e)}")
            finally:
                self.delete_image_btn.setEnabled(True)
                self.delete_image_btn.setText("🗑️ Delete Image")
                self.check_build_status()
            
    def start_frigate(self):
        """Start Frigate container"""
        self.logs_output.append("\n▶️ ====== Starting Frigate ======")
        self.start_btn.setEnabled(False)
        self.start_btn.setText("🔄 Starting...")
        
        # Use DockerWorker to start the container
        from frigate_launcher import DockerWorker
        self.docker_worker = DockerWorker(self.script_dir, action='start')
        self.docker_worker.progress.connect(self.logs_output.append)
        self.docker_worker.finished.connect(self.on_start_finished)
        self.docker_worker.start()
    
    def on_start_finished(self, success):
        """Handle start completion"""
        self.start_btn.setEnabled(True)
        self.start_btn.setText("▶ Start Frigate")
        
        if success:
            QTimer.singleShot(2000, self.check_status)
            # Start streaming logs
            self.start_log_streaming()
        else:
            QTimer.singleShot(1000, self.check_status)
            
    def stop_frigate(self):
        """Stop Frigate container"""
        self.logs_output.append("\n⏹️ ====== Stopping Frigate ======")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setText("🔄 Stopping...")
        
        # Use DockerWorker to stop the container
        from frigate_launcher import DockerWorker
        self.docker_worker = DockerWorker(self.script_dir, action='stop')
        self.docker_worker.progress.connect(self.logs_output.append)
        self.docker_worker.finished.connect(self.on_stop_finished)
        self.docker_worker.start()
    
    def on_stop_finished(self, success):
        """Handle stop completion"""
        self.stop_btn.setEnabled(True)
        self.stop_btn.setText("⏹ Stop Frigate")
        
        # Stop log streaming
        self.stop_log_streaming()
        
        QTimer.singleShot(2000, self.check_status)
            
    def restart_frigate(self):
        """Restart Frigate container"""
        self.logs_output.append("\n🔄 ====== Restarting Frigate ======")
        self.restart_btn.setEnabled(False)
        self.restart_btn.setText("🔄 Restarting...")
        
        # Stop log streaming before restart
        self.stop_log_streaming()
        
        # Use DockerWorker to restart the container
        from frigate_launcher import DockerWorker
        self.docker_worker = DockerWorker(self.script_dir, action='restart')
        self.docker_worker.progress.connect(self.logs_output.append)
        self.docker_worker.finished.connect(self.on_restart_finished)
        self.docker_worker.start()
    
    def on_restart_finished(self, success):
        """Handle restart completion"""
        self.restart_btn.setEnabled(True)
        self.restart_btn.setText("🔄 Restart")
        
        QTimer.singleShot(2000, self.check_status)
        
        # Restart log streaming
        if success:
            self.start_log_streaming()
    
    def start_log_streaming(self):
        """Start streaming Docker container logs"""
        # Stop any existing log stream first
        self.stop_log_streaming()
        
        self.logs_output.append("\n📋 ====== Streaming Frigate Logs ======")
        
        # Start log worker
        self.log_worker = LogStreamWorker(container_name='frigate')
        self.log_worker.log_line.connect(self.logs_output.append)
        self.log_worker.start()
    
    def stop_log_streaming(self):
        """Stop streaming Docker container logs"""
        if self.log_worker and self.log_worker.isRunning():
            self.log_worker.stop()
            self.log_worker.wait(2000)  # Wait up to 2 seconds
            self.log_worker = None
        
    def open_web_ui(self, path=""):
        """Open Frigate web UI in browser"""
        url = f"http://localhost:5000{path}"
        webbrowser.open(url)
        self.logs_output.append(f"🌐 Opening {url} in browser...")
        
    def open_shell(self):
        """Open shell in Frigate container"""
        QMessageBox.information(
            self, "Container Shell",
            "To open a shell in the Frigate container, run:\n\n"
            "docker exec -it frigate /bin/bash"
        )
        
    def view_stats(self):
        """View Docker stats"""
        self.refresh_status()
        
    def inspect_container(self):
        """Inspect Frigate container"""
        try:
            result = subprocess.run(
                ['docker', 'inspect', 'frigate'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            self.logs_output.append("🔍 Container Inspection:")
            self.logs_output.append(result.stdout[:2000])  # First 2000 chars
            
        except Exception as e:
            self.logs_output.append(f"❌ Inspection failed: {str(e)}")
            
    def cleanup_resources(self):
        """Clean up Docker resources"""
        reply = QMessageBox.question(
            self, "Clean Up Resources",
            "This will remove stopped containers and unused images.\n\n"
            "Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                subprocess.run(['docker', 'system', 'prune', '-f'], check=True, timeout=60)
                self.logs_output.append("✅ Cleanup completed!")
            except Exception as e:
                self.logs_output.append(f"❌ Cleanup failed: {str(e)}")


# Required import to prevent circular dependency
import time
