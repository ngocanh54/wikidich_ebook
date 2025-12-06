#!/usr/bin/env python3
"""
Simple PyQt6 GUI interface for Wikidich Ebook Creator.
Just URL input and folder selection.
"""
import sys
import os
from pathlib import Path
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit,
    QProgressBar, QFileDialog, QMessageBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices, QAction

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from wikidich_ebook import download_n_make_ebook_wikidich, __version__
from wikidich_ebook.updater import check_for_updates


class WorkerThread(QThread):
    """Worker thread for downloading and creating ebook."""

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    status_signal = pyqtSignal(str)

    def __init__(self, url, output_folder):
        super().__init__()
        self.url = url
        self.output_folder = output_folder

    def run(self):
        """Execute the download and ebook creation."""
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Change to output folder
            if self.output_folder:
                os.chdir(self.output_folder)

            self.status_signal.emit("Downloading and creating EPUB...")
            self.log_signal.emit("\n" + "="*60 + "\n")
            self.log_signal.emit("Starting: Download & Create EPUB\n")
            self.log_signal.emit("="*60 + "\n\n")

            # Run the full workflow
            download_n_make_ebook_wikidich(
                url_toc=self.url,
                latest_chapter_read=0,
                use_volume_structure=None  # Auto-detect
            )

            self.log_signal.emit("\n" + "="*60 + "\n")
            self.log_signal.emit("✓ SUCCESS! EPUB created successfully!\n")
            self.log_signal.emit("="*60 + "\n\n")

            # Get stdout output
            output = sys.stdout.getvalue()
            if output:
                self.log_signal.emit(output)

            self.finished_signal.emit(True, "EPUB created successfully!")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_signal.emit(f"\n❌ {error_msg}\n")
            self.finished_signal.emit(False, error_msg)

        finally:
            sys.stdout = old_stdout
            self.status_signal.emit("Ready")


class WikidichEbookGUI(QMainWindow):
    """Simple GUI window for Wikidich Ebook Creator."""

    def __init__(self):
        super().__init__()
        self.worker = None
        self.current_folder = str(Path.home())  # Default to home directory
        self.init_ui()

        # Check for updates on startup
        QThread.msleep(500)  # Small delay
        self.check_for_updates_silently()

    def init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"Wikidich Ebook Creator v{__version__}")
        self.setGeometry(100, 100, 900, 600)

        # Menu bar
        menubar = self.menuBar()
        help_menu = menubar.addMenu("Help")

        check_update_action = QAction("Check for Updates", self)
        check_update_action.triggered.connect(self.check_for_updates)
        help_menu.addAction(check_update_action)

        help_menu.addSeparator()

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("📚 Wikidich Ebook Creator")
        title.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #2c3e50; padding: 15px;")
        main_layout.addWidget(title)

        # Subtitle
        subtitle = QLabel("Download Vietnamese web novels as EPUB ebooks")
        subtitle.setFont(QFont("Arial", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #7f8c8d; padding-bottom: 10px;")
        main_layout.addWidget(subtitle)

        # URL Input
        url_label = QLabel("📖 Book URL (Table of Contents):")
        url_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Paste URL here: https://truyenwikidich.net/truyen/...")
        self.url_input.setFont(QFont("Arial", 11))
        self.url_input.setMinimumHeight(35)
        main_layout.addWidget(self.url_input)

        # Folder Selection
        folder_label = QLabel("📁 Save Location:")
        folder_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        main_layout.addWidget(folder_label)

        folder_layout = QHBoxLayout()
        self.folder_display = QLineEdit()
        self.folder_display.setReadOnly(True)
        self.folder_display.setText(self.current_folder)
        self.folder_display.setFont(QFont("Arial", 10))
        self.folder_display.setMinimumHeight(35)
        folder_layout.addWidget(self.folder_display)

        browse_btn = QPushButton("Browse...")
        browse_btn.setFont(QFont("Arial", 10))
        browse_btn.setMinimumHeight(35)
        browse_btn.setMinimumWidth(100)
        browse_btn.clicked.connect(self.browse_folder)
        browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #bdc3c7;
            }
        """)
        folder_layout.addWidget(browse_btn)
        main_layout.addLayout(folder_layout)

        # Action Button
        self.download_btn = QPushButton("📥 Download & Create EPUB")
        self.download_btn.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        self.download_btn.setMinimumHeight(50)
        self.download_btn.clicked.connect(self.start_download)
        self.download_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 12px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
        """)
        main_layout.addWidget(self.download_btn)

        # Progress Bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setMinimumHeight(8)
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #ecf0f1;
            }
            QProgressBar::chunk {
                border-radius: 4px;
                background-color: #3498db;
            }
        """)
        main_layout.addWidget(self.progress)

        # Log Output
        log_label = QLabel("📝 Progress Log:")
        log_label.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Courier", 9))
        self.log_text.setPlaceholderText("Logs will appear here...")
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 1px solid #34495e;
                border-radius: 4px;
                padding: 10px;
            }
        """)
        main_layout.addWidget(self.log_text)

        # Status Bar
        self.status_label = QLabel("Ready")
        self.status_label.setFont(QFont("Arial", 10))
        self.statusBar().addWidget(self.status_label)

    def browse_folder(self):
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Save Location",
            self.current_folder
        )
        if folder:
            self.current_folder = folder
            self.folder_display.setText(folder)

    def validate_inputs(self):
        """Validate user inputs."""
        url = self.url_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a book URL")
            return False

        if not url.startswith("http"):
            QMessageBox.warning(self, "Invalid URL", "URL must start with http:// or https://")
            return False

        if "truyenwikidich.net" not in url:
            reply = QMessageBox.question(
                self,
                "Confirm URL",
                "This doesn't look like a truyenwikidich.net URL.\nContinue anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return False

        return True

    def start_download(self):
        """Start the download and ebook creation."""
        if not self.validate_inputs():
            return

        url = self.url_input.text().strip()

        # Disable button
        self.download_btn.setEnabled(False)

        # Start indeterminate progress
        self.progress.setRange(0, 0)

        # Clear log
        self.log_text.clear()

        # Create and start worker thread
        self.worker = WorkerThread(url, self.current_folder)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.download_finished)
        self.worker.status_signal.connect(self.update_status)
        self.worker.start()

    def append_log(self, text):
        """Append text to log (thread-safe)."""
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def update_status(self, status):
        """Update status bar text."""
        self.status_label.setText(status)

    def download_finished(self, success, message):
        """Handle download completion."""
        self.download_btn.setEnabled(True)
        self.progress.setRange(0, 100)
        self.progress.setValue(100 if success else 0)

        if success:
            QMessageBox.information(
                self,
                "Success! 🎉",
                f"{message}\n\nLocation: {self.current_folder}"
            )
        else:
            QMessageBox.critical(self, "Error", message)

        self.worker = None

    def check_for_updates_silently(self):
        """Check for updates without showing dialog if up to date."""
        try:
            update_info = check_for_updates()
            if update_info and update_info['available']:
                # Only show if update is available
                self.show_update_notification(update_info)
        except:
            pass  # Silently fail

    def check_for_updates(self):
        """Check for application updates (manual)."""
        self.status_label.setText("Checking for updates...")

        try:
            update_info = check_for_updates()

            if not update_info:
                QMessageBox.information(
                    self,
                    "Update Check",
                    "Unable to check for updates.\nPlease try again later."
                )
                self.status_label.setText("Ready")
                return

            if update_info['available']:
                self.show_update_notification(update_info)
            else:
                QMessageBox.information(
                    self,
                    "No Updates",
                    f"✓ You're running the latest version!\n\nVersion: {update_info['current_version']}"
                )

            self.status_label.setText("Ready")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to check for updates:\n{str(e)}")
            self.status_label.setText("Ready")

    def show_update_notification(self, update_info):
        """Show update notification dialog."""
        reply = QMessageBox.question(
            self,
            "Update Available! 🎉",
            f"A new version is available!\n\n"
            f"Current: {update_info['current_version']}\n"
            f"Latest: {update_info['latest_version']}\n\n"
            f"Would you like to download it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            QDesktopServices.openUrl(QUrl(update_info['download_url']))

    def show_about(self):
        """Show about dialog."""
        about_text = f"""
        <h2>Wikidich Ebook Creator</h2>
        <p><b>Version:</b> {__version__}</p>
        <p>Download Vietnamese web novels from truyenwikidich.net<br>
        and convert them into offline EPUB ebooks.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>Automated web scraping</li>
            <li>Professional EPUB generation</li>
            <li>Volume support & auto-detect</li>
            <li>Smart updates & resume capability</li>
        </ul>
        <p><b>GitHub:</b> <a href="https://github.com/ngocanh54/wikidich_ebook">ngocanh54/wikidich_ebook</a></p>
        <p style="color: #7f8c8d;">© 2024 - For personal use only</p>
        """

        QMessageBox.about(self, "About Wikidich Ebook Creator", about_text)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Quit",
                "Download is in progress.\nDo you want to quit anyway?",
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
    app.setStyle("Fusion")  # Modern look

    window = WikidichEbookGUI()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
