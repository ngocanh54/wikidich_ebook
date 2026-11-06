"""Pastel, rounded stylesheet for the GUI (light and dark).

Kept out of gui.py so the window code stays about layout and behaviour.
Colours follow the approved sidebar design; objectName selectors are set in gui.py.
"""

ACCENT = "#6F4FE8"

LIGHT = {
    "bg": "#FBF8FF", "panel": "#FFFFFF", "side": "#F4EEFF", "text": "#2A2340",
    "muted": "#7A7392", "border": "#E4DCF5", "accent": ACCENT, "accent_hover": "#5C3DD1",
    "tint": "#F0EAFF", "warn_bg": "#FFE7DA", "warn_text": "#9A4A1E",
    "ok_bg": "#DFF6EC", "ok_text": "#1E6B4B", "log_bg": "#2B2236", "log_text": "#EDE7F7",
    "disabled": "#D8D1E8",
}

DARK = {
    "bg": "#1B1626", "panel": "#251F33", "side": "#211B2E", "text": "#EDE7F7",
    "muted": "#A59DBB", "border": "#3A3150", "accent": "#9B82FF", "accent_hover": "#B09CFF",
    "tint": "#2F2744", "warn_bg": "#4A2E22", "warn_text": "#FFC7A8",
    "ok_bg": "#1F3B31", "ok_text": "#9BE3C3", "log_bg": "#15111D", "log_text": "#EDE7F7",
    "disabled": "#3A3150",
}


def build_stylesheet(dark: bool = False) -> str:
    c = DARK if dark else LIGHT
    return f"""
    QMainWindow, QWidget#content {{ background: {c['bg']}; }}
    QWidget {{ color: {c['text']}; font-size: 13px; }}
    QWidget#sidebar {{ background: {c['side']}; border-right: 1px solid {c['border']}; }}
    QLabel#brand {{ font-size: 16px; font-weight: 700; }}
    QLabel#version {{ color: {c['muted']}; font-size: 11px; }}
    QPushButton#navActive {{
        background: {c['tint']}; color: {c['accent']}; border: none; border-radius: 14px;
        padding: 9px 14px; text-align: left; font-weight: 600;
    }}
    QPushButton#navSoon {{
        background: transparent; color: {c['muted']}; border: none; border-radius: 14px;
        padding: 9px 14px; text-align: left;
    }}
    QLabel#pageTitle {{ font-size: 24px; font-weight: 700; }}
    QLabel#pageSub {{ color: {c['muted']}; }}
    QLabel#fieldLabel {{ color: {c['muted']}; font-size: 12px; font-weight: 600; }}
    QLineEdit, QSpinBox, QComboBox {{
        background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 14px;
        padding: 8px 12px; min-height: 22px; selection-background-color: {c['accent']};
    }}
    QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{ border: 2px solid {c['accent']}; padding: 7px 11px; }}
    QLineEdit:read-only {{ color: {c['muted']}; }}
    QComboBox::drop-down {{ border: none; width: 24px; }}
    QComboBox QAbstractItemView {{
        background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 10px;
        selection-background-color: {c['tint']}; selection-color: {c['accent']}; outline: none;
    }}
    QPushButton#secondary {{
        background: {c['tint']}; color: {c['accent']}; border: none; border-radius: 16px;
        padding: 9px 18px; font-weight: 600;
    }}
    QPushButton#secondary:hover {{ background: {c['border']}; }}
    QPushButton#primary {{
        background: {c['accent']}; color: white; border: none; border-radius: 22px;
        padding: 13px 24px; font-size: 15px; font-weight: 700;
    }}
    QPushButton#primary:hover {{ background: {c['accent_hover']}; }}
    QPushButton#primary:disabled {{ background: {c['disabled']}; color: {c['muted']}; }}
    QFrame#card {{ background: {c['panel']}; border: 1px solid {c['border']}; border-radius: 22px; }}
    QLabel#banner {{
        background: {c['warn_bg']}; color: {c['warn_text']}; border-radius: 16px;
        padding: 10px 14px; font-weight: 600;
    }}
    QProgressBar {{
        background: {c['tint']}; border: none; border-radius: 12px; min-height: 24px;
        text-align: center; color: {c['text']}; font-weight: 600;
    }}
    QProgressBar::chunk {{ background: {c['accent']}; border-radius: 12px; }}
    QTextEdit#log {{
        background: {c['log_bg']}; color: {c['log_text']}; border: none; border-radius: 22px;
        padding: 12px; font-family: "JetBrains Mono", Menlo, monospace; font-size: 12px;
    }}
    QStatusBar {{ background: {c['bg']}; color: {c['muted']}; }}
    QStatusBar QLabel {{ color: {c['muted']}; }}
    QScrollBar:vertical {{ background: transparent; width: 10px; }}
    QScrollBar::handle:vertical {{ background: {c['border']}; border-radius: 5px; min-height: 24px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """
