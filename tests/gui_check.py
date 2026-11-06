"""Offscreen GUI state check: idle, running, partial, success, error, light/dark. Run: make gui-check"""
import sys, os
sys.path.insert(0, os.getcwd())
os.environ["QT_QPA_PLATFORM"]="offscreen"
from unittest import mock
from PyQt6.QtWidgets import QApplication, QMessageBox
import gui
app=QApplication([]); app.setStyle("Fusion")
with mock.patch.object(gui,"check_for_updates",return_value=None):
    w=gui.WikidichEbookGUI()
w.show()
import tempfile
out=sys.argv[1] if len(sys.argv)>1 else tempfile.mkdtemp()
w.grab().save(f"{out}/idle.png")
w.progress.setRange(0,100); w.update_progress(40,100); w.append_log("Downloading chapter 40")
w.grab().save(f"{out}/running.png")
for name in ("information","warning","critical"):
    setattr(QMessageBox,name,staticmethod(lambda *a,**k:None))
w.download_finished(True,"Partial download: 40 of 100 chapters")
assert w.banner.isVisible() and w.progress.value()==40
w.grab().save(f"{out}/partial.png")
w.download_finished(True,"Done"); assert w.progress.value()==100
w.download_finished(False,"boom"); assert w.progress.value()==0
w.operation_combo.setCurrentText("Extract TOC Only"); assert "Table" in w.download_btn.text()
w.apply_theme(); w.setStyleSheet(gui.build_stylesheet(dark=True)); w.grab().save(f"{out}/dark.png")
w.url_input.setText("https://wikicv.org/truyen/x"); assert w.validate_inputs()
assert "&&" in w.download_btn.text() or "Table" in w.download_btn.text()
# resize, and start/quit flow with a fake running worker
for size in ((760, 560), (1400, 900)):
    w.resize(*size); app.processEvents(); assert w.log_text.isVisible()
class FakeWorker:
    terminated = False
    def isRunning(self): return True
    def terminate(self): FakeWorker.terminated = True
    def wait(self): pass
w.worker = FakeWorker()
from PyQt6.QtGui import QCloseEvent
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.No)
ev = QCloseEvent(); w.closeEvent(ev); assert not ev.isAccepted() and not FakeWorker.terminated
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
ev = QCloseEvent(); w.closeEvent(ev); assert ev.isAccepted() and FakeWorker.terminated
w.worker = None
# Create EPUB Only: URL not needed, pick a downloaded book from the save location
import json as _json
bookroot = tempfile.mkdtemp()
bdir = os.path.join(bookroot, "my-book"); os.makedirs(bdir)
open(os.path.join(bdir, "info.json"), "w", encoding="utf-8").write(_json.dumps({"title": "My Book"}))
open(os.path.join(bdir, "toc.csv"), "w", encoding="utf-8").write("chapter_number,chapter_name,url,volume_name\n1,a,u,\n2,b,u,\n")
open(os.path.join(bdir, "chap_0001.html"), "w", encoding="utf-8").write("x")
w.current_folder = bookroot
w.operation_combo.setCurrentText("Create EPUB Only"); app.processEvents()
assert not w.url_input.isEnabled() and w.book_combo.isVisible()
assert w.book_combo.count() == 1 and w.book_combo.currentData() == bdir, w.book_combo.currentText()
assert "1/2" in w.book_combo.currentText()
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.No)
assert w.validate_inputs() is False          # partially downloaded: user declines
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
assert w.validate_inputs() is True           # no URL typed, still valid
w.current_folder = tempfile.mkdtemp(); w.refresh_books()
QMessageBox.warning = staticmethod(lambda *a, **k: None)
assert w.validate_inputs() is False          # empty location: nothing to build
# Download Chapters Only uses the same picker, without the partial-download prompt
w.current_folder = bookroot
w.operation_combo.setCurrentText("Download Chapters Only"); app.processEvents()
assert not w.url_input.isEnabled() and w.book_combo.isVisible() and w.book_combo.currentData() == bdir
QMessageBox.question = staticmethod(lambda *a, **k: (_ for _ in ()).throw(AssertionError("asked")))
assert w.validate_inputs() is True
w.operation_combo.setCurrentText("Full Workflow"); app.processEvents()
assert w.url_input.isEnabled() and not w.book_combo.isVisible()

# theme switch (offscreen ignores the system scheme, so pass it explicitly)
w.apply_theme(True); assert w._dark is True and "#1B1626" in w.styleSheet()
w.apply_theme(False); assert w._dark is False and "#FBF8FF" in w.styleSheet()

# real WorkerThread against a dead local URL (no site traffic): must end via download_finished
import tempfile
seen = []
orig = w.download_finished
w.download_finished = lambda ok, msg: (seen.append((ok, msg)), orig(ok, msg))
w.current_folder = tempfile.mkdtemp()
w.url_input.setText("http://127.0.0.1:9/truyen/none")
w.operation_combo.setCurrentText("Extract TOC Only")
QMessageBox.question = staticmethod(lambda *a, **k: QMessageBox.StandardButton.Yes)
w.start_download()
assert not w.download_btn.isEnabled()
import time
t = time.time()
while w.worker is not None and time.time() - t < 90:
    app.processEvents(); time.sleep(0.1)
assert w.worker is None and seen and w.download_btn.isEnabled(), seen
print("worker failure path ended:", seen[0][0], seen[0][1][:80])
print("GUI states OK")
