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
print("GUI states OK")
