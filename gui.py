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
    QProgressBar, QFileDialog, QMessageBox, QSpinBox, QComboBox, QFrame, QGridLayout
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QAction

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from wikidich_ebook import (
    DownloadCancelled,
    download_n_make_ebook_wikidich,
    check_if_updated,
    get_toc,
    download_truyen,
    make_ebook,
    find_book_folders,
    __version__
)
from wikidich_ebook.updater import check_for_updates
from wikidich_ebook.gui_style import build_stylesheet


# Modes that work from an already-extracted book folder instead of a URL
BOOK_FOLDER_MODES = ("Download Chapters Only", "Create EPUB Only")


class LogStream:
    """Custom stream that emits output in real-time to the log signal."""

    def __init__(self, log_signal):
        self.log_signal = log_signal

    def write(self, text):
        if text.strip():  # Only emit non-empty text
            self.log_signal.emit(text)

    def flush(self):
        pass  # Required for file-like object


class WorkerThread(QThread):
    """Worker thread for downloading and creating ebook."""

    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    status_signal = pyqtSignal(str)
    progress_signal = pyqtSignal(int, int)  # (current, total) for chapter downloads

    def __init__(self, url, output_folder, operation_mode='full', start_chapter=0,
                 volume_structure='auto', manual_pages=None, book_folder=None):
        super().__init__()
        self.book_folder = book_folder  # Download Chapters Only / Create EPUB Only: existing book folder, no URL needed
        self.url = url
        self.output_folder = output_folder
        self.operation_mode = operation_mode
        self.start_chapter = start_chapter
        self.volume_structure = volume_structure
        self.manual_pages = manual_pages
        self._stop_requested = False

    def request_stop(self):
        """Ask the download to stop after the current chapter (saved chapters are kept)."""
        self._stop_requested = True

    def should_stop(self):
        return self._stop_requested

    def progress_callback(self, current, total):
        """Callback for chapter download progress."""
        self.progress_signal.emit(current, total)

    def run(self):
        """Execute the download and ebook creation."""
        import sys
        import re

        # Redirect stdout and stderr to our custom stream for real-time logging
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = LogStream(self.log_signal)
        sys.stderr = LogStream(self.log_signal)

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
            except ValueError:
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                self.finished_signal.emit(
                    False,
                    f"Invalid Manual Pages value: '{self.manual_pages}'. "
                    "Expected comma-separated page numbers (e.g. '1,2,3')."
                )
                return

        try:
            # Change to output folder
            if self.output_folder:
                os.chdir(self.output_folder)

            if self.operation_mode == 'check':
                self.status_signal.emit("Checking for updates...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Check for Updates\n")
                self.log_signal.emit("="*60 + "\n\n")

                is_updated, folder = check_if_updated(self.url)

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

                is_updated, folder = check_if_updated(self.url)

                get_toc(
                    self.url,
                    folder,
                    check_pagination=(page_list is not None),
                    page_list=page_list,
                    is_manual=is_manual
                )

                self.log_signal.emit("\n✓ TOC extracted successfully!\n")
                self.finished_signal.emit(True, "TOC extracted successfully!")

            elif self.operation_mode == 'download':
                self.status_signal.emit("Downloading chapters...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Download Chapters\n")
                self.log_signal.emit("="*60 + "\n\n")

                if not self.book_folder:
                    raise ValueError("Choose a book first (its TOC must already be extracted).")

                # Pass progress callback for GUI progress bar
                num_fail = download_truyen(self.book_folder, self.start_chapter, self.progress_callback,
                                          self.should_stop)

                if num_fail and num_fail > 0:
                    self.log_signal.emit(f"\n⚠️ Partial download: {num_fail} chapter(s) could not be downloaded due to IP restriction.\n")
                    self.finished_signal.emit(True, f"Partial download complete — {num_fail} chapter(s) were skipped due to IP rate limiting.\n\nYou can run Download Chapters again later to resume.")
                else:
                    self.log_signal.emit("\n✓ Chapters downloaded successfully!\n")
                    self.finished_signal.emit(True, "Chapters downloaded successfully!")

            elif self.operation_mode == 'epub':
                self.status_signal.emit("Creating EPUB...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Create EPUB\n")
                self.log_signal.emit("="*60 + "\n\n")

                if not self.book_folder:
                    raise ValueError("Choose a downloaded book first.")

                make_ebook(self.book_folder, self.start_chapter, volume_structure_value)

                self.log_signal.emit("\n✓ EPUB created successfully!\n")
                self.finished_signal.emit(True, "EPUB created successfully!")

            else:  # full workflow
                self.status_signal.emit("Downloading and creating EPUB...")
                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("Operation: Full Workflow (Download && Create EPUB)\n")
                self.log_signal.emit("="*60 + "\n\n")

                # Full workflow - pass progress callback for GUI progress bar
                download_n_make_ebook_wikidich(
                    url_toc=self.url,
                    latest_chapter_read=self.start_chapter,
                    use_volume_structure=volume_structure_value,
                    progress_callback=self.progress_callback,
                    should_stop=self.should_stop
                )

                self.log_signal.emit("\n" + "="*60 + "\n")
                self.log_signal.emit("✓ SUCCESS! EPUB created successfully!\n")
                self.log_signal.emit("="*60 + "\n\n")
                self.finished_signal.emit(True, "EPUB created successfully!")

        except DownloadCancelled:
            self.log_signal.emit("\n⏹️ Stopped. Chapters downloaded so far are kept; run it again to resume.\n")
            self.finished_signal.emit(True, "Stopped by user")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.log_signal.emit(f"\n❌ {error_msg}\n")
            self.finished_signal.emit(False, error_msg)

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
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
        """Initialize the user interface (sidebar layout, styled by gui_style)."""
        self.setWindowTitle(f"Wikidich Ebook Creator v{__version__}")
        self.setGeometry(100, 100, 1000, 700)

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

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        content = QWidget()
        content.setObjectName("content")
        root_layout.addWidget(content, 1)
        main_layout = QVBoxLayout(content)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(28, 24, 28, 20)

        title = QLabel("Download a novel")
        title.setObjectName("pageTitle")
        main_layout.addWidget(title)
        subtitle = QLabel("Paste a link, pick a folder, and get an EPUB for offline reading.")
        subtitle.setObjectName("pageSub")
        main_layout.addWidget(subtitle)

        # Partial-download banner (hidden until a partial result arrives)
        self.banner = QLabel()
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        self.banner.hide()
        main_layout.addWidget(self.banner)

        # URL
        main_layout.addWidget(self._field_label("Book URL (table of contents page)"))
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://wikicv.org/truyen/...")
        main_layout.addWidget(self.url_input)

        # Save location
        main_layout.addWidget(self._field_label("Save location"))
        folder_layout = QHBoxLayout()
        self.folder_display = QLineEdit()
        self.folder_display.setReadOnly(True)
        self.folder_display.setText(self.current_folder)
        folder_layout.addWidget(self.folder_display)
        browse_btn = QPushButton("Browse…")
        browse_btn.setObjectName("secondary")
        browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        browse_btn.clicked.connect(self.browse_folder)
        folder_layout.addWidget(browse_btn)
        main_layout.addLayout(folder_layout)

        # Book picker (Download Chapters Only / Create EPUB Only: no URL needed)
        self.book_label = self._field_label("Book in the save location (needs its TOC extracted)")
        self.book_combo = QComboBox()
        self.book_label.hide()
        self.book_combo.hide()
        main_layout.addWidget(self.book_label)
        main_layout.addWidget(self.book_combo)

        # Options card
        card = QFrame()
        card.setObjectName("card")
        grid = QGridLayout(card)
        grid.setContentsMargins(18, 14, 18, 16)
        grid.setHorizontalSpacing(14)
        grid.setVerticalSpacing(6)

        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Full Workflow",
            "Check for Updates",
            "Extract TOC Only",
            "Download Chapters Only",
            "Create EPUB Only"
        ])
        self.operation_combo.currentTextChanged.connect(self.update_action_button_text)
        self.operation_combo.currentTextChanged.connect(self.update_mode_ui)

        self.start_chapter_spin = QSpinBox()
        self.start_chapter_spin.setMinimum(0)
        self.start_chapter_spin.setMaximum(9999)
        self.start_chapter_spin.setValue(0)
        # Native arrows render as a broken box under the custom stylesheet; typing and the wheel still work
        self.start_chapter_spin.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        self.start_chapter_spin.setToolTip("Chapter number to start from (0 = from beginning)")

        self.volume_combo = QComboBox()
        self.volume_combo.addItems(["Auto-detect", "Force Yes", "Force No"])
        self.volume_combo.setToolTip("Use volume structure in EPUB TOC")

        self.manual_pages_input = QLineEdit()
        self.manual_pages_input.setPlaceholderText("e.g., 1,2,3,4,5")
        self.manual_pages_input.setToolTip("Comma-separated page numbers for manual pagination")

        for col, (text, widget) in enumerate([
            ("Operation", self.operation_combo),
            ("Start chapter", self.start_chapter_spin),
        ]):
            grid.addWidget(self._field_label(text), 0, col)
            grid.addWidget(widget, 1, col)
        for col, (text, widget) in enumerate([
            ("Volume structure", self.volume_combo),
            ("Manual pages (optional)", self.manual_pages_input),
        ]):
            grid.addWidget(self._field_label(text), 2, col)
            grid.addWidget(widget, 3, col)
        main_layout.addWidget(card)

        # Action button
        self.download_btn = QPushButton("📥 Download && Create EPUB")
        self.download_btn.setObjectName("primary")
        self.download_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.download_btn.clicked.connect(self.start_download)
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setObjectName("stop")
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setToolTip("Stop after the current chapter; chapters already downloaded are kept")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_download)
        action_row = QHBoxLayout()
        action_row.setSpacing(10)
        action_row.addWidget(self.download_btn, 1)
        action_row.addWidget(self.stop_btn)
        main_layout.addLayout(action_row)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setTextVisible(True)
        self.progress.setFormat("%p%")
        main_layout.addWidget(self.progress)

        # Log
        self.log_text = QTextEdit()
        self.log_text.setObjectName("log")
        self.log_text.setReadOnly(True)
        self.log_text.setPlaceholderText("Logs will appear here...")
        main_layout.addWidget(self.log_text, 1)

        self.clear_log_btn = QPushButton("Clear log")
        self.clear_log_btn.setObjectName("secondary")
        self.clear_log_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_log_btn.clicked.connect(self.log_text.clear)
        log_row = QHBoxLayout()
        log_row.addStretch(1)
        log_row.addWidget(self.clear_log_btn)
        main_layout.addLayout(log_row)

        # Status bar
        self.status_label = QLabel("Ready")
        self.statusBar().addWidget(self.status_label)

        self.apply_theme()
        QApplication.styleHints().colorSchemeChanged.connect(lambda _scheme: self.apply_theme())

    def _field_label(self, text):
        label = QLabel(text)
        label.setObjectName("fieldLabel")
        return label

    def _build_sidebar(self):
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(200)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(16, 22, 16, 16)
        layout.setSpacing(8)

        brand = QLabel("📚 Wikidich")
        brand.setObjectName("brand")
        layout.addWidget(brand)
        version = QLabel(f"Ebook Creator v{__version__}")
        version.setObjectName("version")
        layout.addWidget(version)
        layout.addSpacing(14)

        current = QPushButton("New download")
        current.setObjectName("navActive")
        layout.addWidget(current)

        library = QPushButton("Library  ·  Soon")
        library.setObjectName("navSoon")
        library.setEnabled(False)
        layout.addWidget(library)

        layout.addStretch(1)
        return side

    def apply_theme(self, dark=None):
        """Apply the stylesheet matching the system light/dark setting (or `dark` if given)."""
        if dark is None:
            dark = QApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        if dark == getattr(self, "_dark", None):
            return  # unchanged
        self._dark = dark
        self.setStyleSheet(build_stylesheet(dark=dark))

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
            self.refresh_books()

    def needs_book_folder(self):
        return self.operation_combo.currentText() in BOOK_FOLDER_MODES

    def update_mode_ui(self, _text=None):
        """Download Chapters Only and Create EPUB Only work from a book folder, so they swap the URL for a book picker."""
        epub_only = self.needs_book_folder()
        self.url_input.setEnabled(not epub_only)
        self.url_input.setPlaceholderText(
            "Not needed for this operation: pick a book from the save location below"
            if epub_only else "https://wikicv.org/truyen/..."
        )
        self.book_label.setVisible(epub_only)
        self.book_combo.setVisible(epub_only)
        self.manual_pages_input.setEnabled(not epub_only)
        if epub_only:
            self.refresh_books()

    def refresh_books(self):
        """List the downloaded books found in the save location."""
        self.book_combo.clear()
        books = find_book_folders(self.current_folder)
        for b in books:
            self.book_combo.addItem(
                f"{b['title']}  ({b['downloaded']}/{b['total']} chapters downloaded)", b['path']
            )
            self.book_combo.setItemData(self.book_combo.count() - 1, (b['downloaded'], b['total']),
                                        Qt.ItemDataRole.UserRole + 1)
        if not books:
            self.book_combo.addItem("No book with an extracted TOC found in this folder")
            self.book_combo.setItemData(0, None)

    def update_action_button_text(self, operation_text):
        """Update action button text based on selected operation."""
        button_texts = {
            "Full Workflow": "📥 Download && Create EPUB",
            "Check for Updates": "🔍 Check for Updates",
            "Extract TOC Only": "📑 Extract Table of Contents",
            "Download Chapters Only": "⬇️ Download Chapters",
            "Create EPUB Only": "📚 Create EPUB"
        }
        self.download_btn.setText(button_texts.get(operation_text, "📥 Download && Create EPUB"))

    def validate_inputs(self):
        """Validate user inputs."""
        if self.needs_book_folder():
            if not self.book_combo.currentData():
                QMessageBox.warning(
                    self, "No book selected",
                    "No book with an extracted TOC found in the save location.\n"
                    "Pick the folder that contains your book folders (or the book folder itself)."
                )
                return False
            counts = self.book_combo.currentData(Qt.ItemDataRole.UserRole + 1)
            if self.operation_combo.currentText() == "Create EPUB Only" and counts and counts[0] < counts[1]:
                reply = QMessageBox.question(
                    self, "Book not fully downloaded",
                    f"Only {counts[0]} of {counts[1]} chapters are downloaded.\n"
                    "Create the EPUB from the chapters you have?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                return reply == QMessageBox.StandardButton.Yes
            return True

        url = self.url_input.text().strip()

        if not url:
            QMessageBox.warning(self, "Missing URL", "Please enter a book URL")
            return False

        if not url.startswith("http"):
            QMessageBox.warning(self, "Invalid URL", "URL must start with http:// or https://")
            return False

        if "/truyen/" not in url:
            reply = QMessageBox.question(
                self,
                "Confirm URL",
                "This doesn't look like a book page (no /truyen/ in the link).\n"
                "Copy the link from your browser's address bar while viewing the book.\n\n"
                "Continue anyway?",
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
        book_folder = self.book_combo.currentData() if self.needs_book_folder() else None

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

        # Disable start, enable stop
        self.download_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.banner.hide()

        # Set progress bar to indeterminate mode (animated) during execution
        self.progress.setRange(0, 0)

        # Clear log
        self.log_text.clear()

        # Create and start worker thread
        self.worker = WorkerThread(
            url,
            self.current_folder,
            operation_mode=operation_mode,
            start_chapter=start_chapter,
            volume_structure=volume_structure,
            manual_pages=manual_pages,
            book_folder=book_folder
        )
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.download_finished)
        self.worker.status_signal.connect(self.update_status)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.start()

    def stop_download(self):
        """Ask the worker to stop after the current chapter."""
        if self.worker and self.worker.isRunning():
            self.worker.request_stop()
            self.stop_btn.setEnabled(False)
            self.update_status("Stopping after the current chapter...")
            self.append_log("\n⏹️ Stop requested, finishing the current chapter...\n")

    def append_log(self, text):
        """Append text to log (thread-safe)."""
        self.log_text.append(text)
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def update_status(self, status):
        """Update status bar text."""
        self.status_label.setText(status)

    def update_progress(self, current, total):
        """Update progress bar with chapter download progress."""
        if total > 0:
            # Set progress bar to determinate mode
            self.progress.setRange(0, total)
            self.progress.setValue(current)
            # Update format to show "X/Total chapters"
            self.progress.setFormat(f"{current}/{total} chapters (%p%)")
        else:
            # Reset to indeterminate mode
            self.progress.setRange(0, 0)
            self.progress.setFormat("%p%")

    def download_finished(self, success, message):
        """Handle download completion."""
        self.download_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

        if success and message == "Stopped by user":
            # Keep the progress bar where it stopped; no popup, the log says what happened
            self.worker = None
            return

        is_partial = success and message.startswith("Partial download")
        if is_partial:
            # Leave progress bar at its last real value (e.g. 805/1208)
            pass
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(100 if success else 0)
            self.progress.setFormat("%p%")

        if is_partial:
            self.banner.setText(message)
            self.banner.show()
            QMessageBox.warning(
                self,
                "Partial Download",
                f"{message}\n\nLocation: {self.current_folder}"
            )
        elif success:
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
        <p>Download Vietnamese web novels from wikicv.org and similar sites<br>
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
