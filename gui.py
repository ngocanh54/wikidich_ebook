#!/usr/bin/env python3
"""
PyQt6 GUI interface for Wikidich Ebook Creator.
"""
import sys
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QGroupBox,
    QRadioButton, QButtonGroup, QProgressBar, QFileDialog,
    QMessageBox, QSpinBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QFont, QIcon

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from wikidich_ebook import (
    download_n_make_ebook_wikidich,
    check_if_updated,
    get_toc,
    download_truyen,
    make_ebook
)


class WorkerThread(QThread):
    """Worker thread for running ebook operations."""

    # Signals for thread-safe communication
    log_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(bool)  # True = start, False = stop
    finished_signal = pyqtSignal(bool, str)  # success, message
    status_signal = pyqtSignal(str)

    def __init__(self, action_type, url, start_chapter, volume_structure, output_folder):
        super().__init__()
        self.action_type = action_type
        self.url = url
        self.start_chapter = start_chapter
        self.volume_structure = volume_structure
        self.output_folder = output_folder

    def run(self):
        """Execute the action in background thread."""
        import os
        import sys
        from io import StringIO

        # Redirect stdout to capture prints
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Change directory if output folder specified
            if self.output_folder:
                os.chdir(self.output_folder)

            self.status_signal.emit(f"Running {self.action_type}...")

            if self.action_type == "full":
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Starting full workflow: Download & Create EPUB\n")
                self.log_signal.emit("="*60 + "\n\n")

                download_n_make_ebook_wikidich(
                    self.url,
                    self.start_chapter,
                    self.volume_structure
                )

                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("✓ SUCCESS! EPUB created successfully!\n")
                self.log_signal.emit("="*60 + "\n\n")
                self.finished_signal.emit(True, "EPUB created successfully!")

            elif self.action_type == "check":
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Checking for updates...\n")
                self.log_signal.emit("="*60 + "\n\n")

                is_updated, folder = check_if_updated(self.url)

                if is_updated:
                    msg = f"✓ Updates detected!\nFolder: {folder}"
                else:
                    msg = f"✓ No updates.\nFolder: {folder}"

                self.log_signal.emit(f"\n{msg}\n")
                self.finished_signal.emit(True, msg)

            elif self.action_type == "toc":
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Extracting table of contents...\n")
                self.log_signal.emit("="*60 + "\n\n")

                is_updated, folder = check_if_updated(self.url)
                get_toc(self.url, folder)

                self.log_signal.emit("\n✓ TOC extracted successfully!\n")
                self.finished_signal.emit(True, "Table of contents extracted!")

            elif self.action_type == "download":
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Downloading chapters...\n")
                self.log_signal.emit("="*60 + "\n\n")

                is_updated, folder = check_if_updated(self.url)
                download_truyen(folder, self.start_chapter)

                self.log_signal.emit("\n✓ Chapters downloaded successfully!\n")
                self.finished_signal.emit(True, "Chapters downloaded!")

            elif self.action_type == "epub":
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Creating EPUB...\n")
                self.log_signal.emit("="*60 + "\n\n")

                is_updated, folder = check_if_updated(self.url)
                make_ebook(folder, self.start_chapter, self.volume_structure)

                self.log_signal.emit("\n✓ EPUB created successfully!\n")
                self.finished_signal.emit(True, "EPUB created!")

            # Get any output that was printed
            output = sys.stdout.getvalue()
            if output:
                self.log_signal.emit(output)

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_signal.emit(f"\n❌ {error_msg}\n")
            self.finished_signal.emit(False, error_msg)

        finally:
            sys.stdout = old_stdout
            self.progress_signal.emit(False)
            self.status_signal.emit("Ready")


class WikidichEbookGUI(QMainWindow):
    """Main GUI window for Wikidich Ebook Creator."""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle("Wikidich Ebook Creator")
        self.setGeometry(100, 100, 1000, 700)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("Wikidich Ebook Creator")
        title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 10px;")
        main_layout.addWidget(title)

        # URL Input Group
        url_group = QGroupBox("Book URL")
        url_layout = QVBoxLayout()
        url_layout.addWidget(QLabel("Table of Contents URL:"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://truyenwikidich.net/truyen/...")
        url_layout.addWidget(self.url_input)
        url_group.setLayout(url_layout)
        main_layout.addWidget(url_group)

        # Options Group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()

        # Start Chapter
        chapter_layout = QHBoxLayout()
        chapter_layout.addWidget(QLabel("Start from chapter:"))
        self.chapter_input = QSpinBox()
        self.chapter_input.setMinimum(0)
        self.chapter_input.setMaximum(99999)
        self.chapter_input.setValue(0)
        chapter_layout.addWidget(self.chapter_input)
        chapter_layout.addWidget(QLabel("(0 = from beginning)"))
        chapter_layout.addStretch()
        options_layout.addLayout(chapter_layout)

        # Volume Structure
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("Volume structure:"))
        self.volume_group = QButtonGroup()
        self.volume_auto = QRadioButton("Auto-detect")
        self.volume_yes = QRadioButton("Yes")
        self.volume_no = QRadioButton("No")
        self.volume_auto.setChecked(True)
        self.volume_group.addButton(self.volume_auto, 0)
        self.volume_group.addButton(self.volume_yes, 1)
        self.volume_group.addButton(self.volume_no, 2)
        volume_layout.addWidget(self.volume_auto)
        volume_layout.addWidget(self.volume_yes)
        volume_layout.addWidget(self.volume_no)
        volume_layout.addStretch()
        options_layout.addLayout(volume_layout)

        # Output Folder
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(QLabel("Output folder:"))
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Leave empty for auto-generated folder")
        folder_layout.addWidget(self.folder_input)
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        options_layout.addLayout(folder_layout)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Action Buttons
        button_layout = QHBoxLayout()

        self.full_btn = QPushButton("📚 Download & Create EPUB")
        self.full_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 10px;
                font-size: 13px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.full_btn.clicked.connect(lambda: self.run_action("full"))
        button_layout.addWidget(self.full_btn)

        self.check_btn = QPushButton("🔍 Check Updates")
        self.check_btn.clicked.connect(lambda: self.run_action("check"))
        button_layout.addWidget(self.check_btn)

        self.toc_btn = QPushButton("📋 Get TOC")
        self.toc_btn.clicked.connect(lambda: self.run_action("toc"))
        button_layout.addWidget(self.toc_btn)

        self.download_btn = QPushButton("⬇️ Download Chapters")
        self.download_btn.clicked.connect(lambda: self.run_action("download"))
        button_layout.addWidget(self.download_btn)

        self.epub_btn = QPushButton("📖 Create EPUB")
        self.epub_btn.clicked.connect(lambda: self.run_action("epub"))
        button_layout.addWidget(self.epub_btn)

        main_layout.addLayout(button_layout)

        # Control Buttons
        control_layout = QHBoxLayout()

        self.clear_btn = QPushButton("🗑️ Clear Log")
        self.clear_btn.clicked.connect(self.clear_log)
        control_layout.addWidget(self.clear_btn)

        control_layout.addStretch()

        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 8px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_action)
        control_layout.addWidget(self.stop_btn)

        main_layout.addLayout(control_layout)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        main_layout.addWidget(self.progress)

        # Log Output
        log_group = QGroupBox("Log Output")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)

        # Status Bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)

        # Apply stylesheet
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                padding: 8px;
                border-radius: 4px;
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
            }
            QPushButton:hover {
                background-color: #bdc3c7;
            }
            QPushButton:disabled {
                background-color: #ecf0f1;
                color: #95a5a6;
            }
        """)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
        if folder:
            self.folder_input.setText(folder)

    def clear_log(self):
        """Clear the log text."""
        self.log_text.clear()

    def validate_inputs(self):
        """Validate user inputs."""
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Please enter a book URL")
            return False

        if not url.startswith("http"):
            QMessageBox.warning(self, "Error", "URL must start with http:// or https://")
            return False

        return True

    def set_buttons_enabled(self, enabled):
        """Enable/disable action buttons."""
        self.full_btn.setEnabled(enabled)
        self.check_btn.setEnabled(enabled)
        self.toc_btn.setEnabled(enabled)
        self.download_btn.setEnabled(enabled)
        self.epub_btn.setEnabled(enabled)
        self.stop_btn.setEnabled(not enabled)

    def run_action(self, action_type):
        """Run the selected action in background thread."""
        if not self.validate_inputs():
            return

        url = self.url_input.text().strip()
        start_chapter = self.chapter_input.value()
        output_folder = self.folder_input.text().strip()

        # Get volume structure preference
        volume_structure = None
        if self.volume_yes.isChecked():
            volume_structure = True
        elif self.volume_no.isChecked():
            volume_structure = False

        # Disable buttons
        self.set_buttons_enabled(False)

        # Start progress bar
        self.progress.setRange(0, 0)  # Indeterminate progress

        # Create and start worker thread
        self.worker = WorkerThread(
            action_type, url, start_chapter, volume_structure, output_folder
        )
        self.worker.log_signal.connect(self.append_log)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.action_finished)
        self.worker.status_signal.connect(self.update_status)
        self.worker.start()

    def append_log(self, text):
        """Append text to log (thread-safe)."""
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def update_progress(self, running):
        """Update progress bar state."""
        if running:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(100)

    def update_status(self, status):
        """Update status bar text."""
        self.status_label.setText(status)

    def action_finished(self, success, message):
        """Handle action completion."""
        self.set_buttons_enabled(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100)

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)

        self.worker = None

    def stop_action(self):
        """Stop the running action."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Stop Operation",
                "Do you want to stop the current operation?\n"
                "Note: The operation will stop after the current step completes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                self.set_buttons_enabled(True)
                self.progress.setRange(0, 100)
                self.progress.setValue(0)
                self.update_status("Stopped")
                self.append_log("\n⚠️ Operation stopped by user\n")

    def closeEvent(self, event):
        """Handle window close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Quit",
                "An operation is running. Do you want to quit anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


def main():
    """Main entry point for GUI."""
    app = QApplication(sys.argv)
    app.setApplicationName("Wikidich Ebook Creator")

    window = WikidichEbookGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
