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
    QProgressBar, QFileDialog, QMessageBox, QSpinBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QFont, QDesktopServices, QAction

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from wikidich_ebook import (
    download_n_make_ebook_wikidich,
    check_if_updated,
    get_toc,
    download_truyen,
    make_ebook,
    __version__
)
from wikidich_ebook.updater import check_for_updates


class WorkerThread(QThread):
    """Worker thread for downloading and creating ebook."""

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int)  # Progress percentage (0-100)

    def __init__(self, url, output_folder, operation_mode='full', start_chapter=0,
                 volume_structure='auto', manual_pages=None):
        super().__init__()
        self.url = url
        self.output_folder = output_folder
        self.operation_mode = operation_mode
        self.start_chapter = start_chapter
        self.volume_structure = volume_structure
        self.manual_pages = manual_pages

    def run(self):
        """Execute the download and ebook creation."""
        import sys
        from io import StringIO

        old_stdout = sys.stdout
        sys.stdout = StringIO()

        # Parse volume structure
        volume_structure_value = None
        if self.volume_structure == 'yes':
            volume_structure_value = True
        elif self.volume_structure == 'no':
            volume_structure_value = False

        # Parse manual pages
        page_list = None
        is_manual = False
        if self.manual_pages:
            try:
                page_list = [int(p.strip()) for p in self.manual_pages.split(',')]
                is_manual = True
            except:
                pass

        try:
            # Change to output folder
            if self.output_folder:
                os.chdir(self.output_folder)

            self.progress_signal.emit(5)

            if self.operation_mode == 'check':
                self.status_signal.emit("Checking for updates...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Check for Updates\n")
                self.log_signal.emit("="*60 + "\n\n")

                self.progress_signal.emit(20)
                is_updated, folder = check_if_updated(self.url)
                self.progress_signal.emit(100)

                if is_updated:
                    self.log_signal.emit(f"\n✓ Updates detected! Folder: {folder}\n")
                    self.finished_signal.emit(True, f"Updates detected! Folder: {folder}")
                else:
                    self.log_signal.emit(f"\n✓ No updates. Folder: {folder}\n")
                    self.finished_signal.emit(True, f"No updates. Folder: {folder}")

            elif self.operation_mode == 'toc':
                self.status_signal.emit("Extracting Table of Contents...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Extract Table of Contents\n")
                self.log_signal.emit("="*60 + "\n\n")

                self.progress_signal.emit(15)
                is_updated, folder = check_if_updated(self.url)
                self.progress_signal.emit(30)

                get_toc(
                    self.url,
                    folder,
                    check_pagination=(page_list is not None),
                    page_list=page_list,
                    is_manual=is_manual
                )
                self.progress_signal.emit(100)

                self.log_signal.emit("\n✓ TOC extracted successfully!\n")
                self.finished_signal.emit(True, "TOC extracted successfully!")

            elif self.operation_mode == 'download':
                self.status_signal.emit("Downloading chapters...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Download Chapters\n")
                self.log_signal.emit("="*60 + "\n\n")

                self.progress_signal.emit(10)
                is_updated, folder = check_if_updated(self.url)
                self.progress_signal.emit(20)

                # Note: download_truyen shows its own progress in logs
                download_truyen(folder, self.start_chapter)
                self.progress_signal.emit(100)

                self.log_signal.emit("\n✓ Chapters downloaded successfully!\n")
                self.finished_signal.emit(True, "Chapters downloaded successfully!")

            elif self.operation_mode == 'epub':
                self.status_signal.emit("Creating EPUB...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Create EPUB\n")
                self.log_signal.emit("="*60 + "\n\n")

                self.progress_signal.emit(10)
                is_updated, folder = check_if_updated(self.url)
                self.progress_signal.emit(25)

                make_ebook(folder, self.start_chapter, volume_structure_value)
                self.progress_signal.emit(100)

                self.log_signal.emit("\n✓ EPUB created successfully!\n")
                self.finished_signal.emit(True, "EPUB created successfully!")

            else:  # full workflow
                self.status_signal.emit("Downloading and creating EPUB...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Full Workflow (Download & Create EPUB)\n")
                self.log_signal.emit("="*60 + "\n\n")

                self.progress_signal.emit(10)
                self.status_signal.emit("Checking for updates...")

                # Full workflow - emit progress at key milestones
                # The actual download_n_make_ebook_wikidich will show detailed logs
                download_n_make_ebook_wikidich(
                    url_toc=self.url,
                    latest_chapter_read=self.start_chapter,
                    use_volume_structure=volume_structure_value
                )

                self.progress_signal.emit(100)
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("✓ SUCCESS! EPUB created successfully!\n")
                self.log_signal.emit("="*60 + "\n\n")
                self.finished_signal.emit(True, "EPUB created successfully!")

            # Get stdout output
            output = sys.stdout.getvalue()
            if output:
                self.log_signal.emit(output)

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

        # Options Group
        options_group = QGroupBox("⚙️ Options")
        options_group.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        options_layout = QVBoxLayout()
        options_group.setLayout(options_layout)

        # Row 1: Operation Mode and Start Chapter
        row1 = QHBoxLayout()

        # Operation Mode
        mode_layout = QVBoxLayout()
        mode_label = QLabel("Operation:")
        mode_label.setFont(QFont("Arial", 10))
        mode_layout.addWidget(mode_label)

        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Full Workflow",
            "Check for Updates",
            "Extract TOC Only",
            "Download Chapters Only",
            "Create EPUB Only"
        ])
        self.operation_combo.setFont(QFont("Arial", 10))
        self.operation_combo.setMinimumHeight(30)
        self.operation_combo.currentTextChanged.connect(self.update_action_button_text)
        mode_layout.addWidget(self.operation_combo)
        row1.addLayout(mode_layout)

        # Start Chapter
        chapter_layout = QVBoxLayout()
        chapter_label = QLabel("Start Chapter:")
        chapter_label.setFont(QFont("Arial", 10))
        chapter_layout.addWidget(chapter_label)

        self.start_chapter_spin = QSpinBox()
        self.start_chapter_spin.setMinimum(0)
        self.start_chapter_spin.setMaximum(9999)
        self.start_chapter_spin.setValue(0)
        self.start_chapter_spin.setFont(QFont("Arial", 10))
        self.start_chapter_spin.setMinimumHeight(30)
        self.start_chapter_spin.setToolTip("Chapter number to start from (0 = from beginning)")
        chapter_layout.addWidget(self.start_chapter_spin)
        row1.addLayout(chapter_layout)

        options_layout.addLayout(row1)

        # Row 2: Volume Structure and Manual Pages
        row2 = QHBoxLayout()

        # Volume Structure
        volume_layout = QVBoxLayout()
        volume_label = QLabel("Volume Structure:")
        volume_label.setFont(QFont("Arial", 10))
        volume_layout.addWidget(volume_label)

        self.volume_combo = QComboBox()
        self.volume_combo.addItems(["Auto-detect", "Force Yes", "Force No"])
        self.volume_combo.setFont(QFont("Arial", 10))
        self.volume_combo.setMinimumHeight(30)
        self.volume_combo.setToolTip("Use volume structure in EPUB TOC")
        volume_layout.addWidget(self.volume_combo)
        row2.addLayout(volume_layout)

        # Manual Pages
        pages_layout = QVBoxLayout()
        pages_label = QLabel("Manual Pages (optional):")
        pages_label.setFont(QFont("Arial", 10))
        pages_layout.addWidget(pages_label)

        self.manual_pages_input = QLineEdit()
        self.manual_pages_input.setPlaceholderText("e.g., 1,2,3,4,5")
        self.manual_pages_input.setFont(QFont("Arial", 10))
        self.manual_pages_input.setMinimumHeight(30)
        self.manual_pages_input.setToolTip("Comma-separated page numbers for manual pagination")
        pages_layout.addWidget(self.manual_pages_input)
        row2.addLayout(pages_layout)

        options_layout.addLayout(row2)

        main_layout.addWidget(options_group)

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
        self.progress.setTextVisible(True)  # Show percentage
        self.progress.setMinimumHeight(25)
        self.progress.setFormat("%p%")  # Show percentage with % sign
        self.progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 4px;
                background-color: #ecf0f1;
                text-align: center;
                color: #2c3e50;
                font-weight: bold;
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

    def update_action_button_text(self, operation_text):
        """Update action button text based on selected operation."""
        button_texts = {
            "Full Workflow": "📥 Download & Create EPUB",
            "Check for Updates": "🔍 Check for Updates",
            "Extract TOC Only": "📑 Extract Table of Contents",
            "Download Chapters Only": "⬇️ Download Chapters",
            "Create EPUB Only": "📚 Create EPUB"
        }
        self.download_btn.setText(button_texts.get(operation_text, "📥 Download & Create EPUB"))

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

        # Get operation mode
        operation_map = {
            "Full Workflow": "full",
            "Check for Updates": "check",
            "Extract TOC Only": "toc",
            "Download Chapters Only": "download",
            "Create EPUB Only": "epub"
        }
        operation_mode = operation_map.get(
            self.operation_combo.currentText(),
            "full"
        )

        # Get start chapter
        start_chapter = self.start_chapter_spin.value()

        # Get volume structure
        volume_map = {
            "Auto-detect": "auto",
            "Force Yes": "yes",
            "Force No": "no"
        }
        volume_structure = volume_map.get(
            self.volume_combo.currentText(),
            "auto"
        )

        # Get manual pages
        manual_pages = self.manual_pages_input.text().strip() or None

        # Disable button
        self.download_btn.setEnabled(False)

        # Reset progress bar to show percentage
        self.progress.setRange(0, 100)
        self.progress.setValue(0)

        # Clear log
        self.log_text.clear()

        # Create and start worker thread
        self.worker = WorkerThread(
            url,
            self.current_folder,
            operation_mode=operation_mode,
            start_chapter=start_chapter,
            volume_structure=volume_structure,
            manual_pages=manual_pages
        )
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.download_finished)
        self.worker.status_signal.connect(self.update_status)
        self.worker.progress_signal.connect(self.update_progress)
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

    def update_progress(self, value):
        """Update progress bar value (thread-safe)."""
        self.progress.setValue(value)

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
