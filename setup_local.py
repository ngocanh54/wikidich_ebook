#!/usr/bin/env python3
"""
Local setup script for Wikidich Ebook Creator.
Checks system requirements and helps set up the environment.
"""
import sys
import subprocess
import platform
import shutil
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def print_success(text):
    """Print success message."""
    print(f"✓ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"⚠️  {text}")


def check_python_version():
    """Check if Python version is 3.7 or higher."""
    print_header("Checking Python Version")
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")

    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print_error("Python 3.7 or higher is required!")
        print("\nPlease upgrade Python:")
        print("  Download from: https://www.python.org/downloads/")
        return False

    print_success("Python version is compatible")
    return True


def check_uv():
    """Check if uv is installed."""
    print_header("Checking uv")

    if shutil.which("uv"):
        result = subprocess.check_output(["uv", "--version"], text=True).strip()
        print_success(f"uv is installed: {result}")
        return True

    print_warning("uv not found — will fall back to pip.")
    print("\nTo install uv (recommended):")
    print("  brew install uv          # macOS")
    print("  pip install uv           # any platform")
    return False


def install_dependencies():
    """Install Python dependencies from requirements.txt."""
    print_header("Installing Python Dependencies")

    requirements_file = Path(__file__).parent / "requirements.txt"

    if not requirements_file.exists():
        print_error("requirements.txt not found!")
        return False

    try:
        print("Installing packages from requirements.txt...")
        print("This may take a few minutes...\n")

        use_uv = bool(shutil.which("uv"))
        if use_uv:
            subprocess.check_call(["uv", "pip", "install", "-r", str(requirements_file)])
        else:
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "-r", str(requirements_file), "--upgrade"
            ])

        print()
        print_success("All dependencies installed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print_error(f"Failed to install dependencies: {e}")
        print("\nYou can try installing manually:")
        print("  uv pip install -r requirements.txt")
        return False


def test_playwright():
    """Install Playwright's bundled Chromium and verify it launches."""
    print_header("Setting Up Playwright Chromium")

    try:
        print("Installing Playwright's bundled Chromium browser...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])

        print("Verifying Playwright launches correctly...")
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()

        print()
        print_success("Playwright setup successful!")
        print("  No separate Chrome installation needed — Playwright bundles its own Chromium.")
        return True

    except Exception as e:
        print_error(f"Playwright setup failed: {e}")
        print("\nTry manually: playwright install chromium")
        return False


def test_pyqt6():
    """Test if PyQt6 is installed correctly."""
    print_header("Testing PyQt6")

    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QT_VERSION_STR

        print(f"PyQt6 version: {QT_VERSION_STR}")
        print_success("PyQt6 is installed correctly!")
        return True

    except ImportError as e:
        print_error(f"PyQt6 import failed: {e}")
        print("\nTry reinstalling PyQt6:")
        print(f"  {sys.executable} -m pip install --upgrade PyQt6")
        return False


def show_virtual_env_info():
    """Show information about virtual environments."""
    print_header("Virtual Environment (Recommended)")

    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print_success("Already running in a virtual environment!")
        return True
    else:
        print_warning("Not running in a virtual environment")
        print("\nIt's recommended to use a virtual environment to avoid conflicts.")
        print("\nTo create and use a virtual environment:\n")

        system = platform.system()
        if system == "Windows":
            print("  1. Create: python -m venv venv")
            print("  2. Activate: venv\\Scripts\\activate")
        else:
            print("  1. Create: uv venv .venv")
            print("  2. Activate: source .venv/bin/activate")

        print("  3. Run this script again: python setup_local.py")

        response = input("\nContinue without virtual environment? (y/n): ")
        return response.lower() == 'y'


def show_usage():
    """Show usage instructions."""
    print_header("Setup Complete!")

    print("✓ Your environment is ready to use Wikidich Ebook Creator!\n")
    print("You can now run the application:\n")

    print("1. GUI Interface (Recommended):")
    print("   python gui.py\n")

    print("2. Command Line Interface:")
    print("   python main.py \"https://truyenwikidich.net/truyen/your-novel-url\"\n")

    print("3. Python API:")
    print("   from wikidich_ebook import download_n_make_ebook_wikidich")
    print("   download_n_make_ebook_wikidich(url_toc=\"...\", latest_chapter_read=0)\n")

    print("="*70)
    print("For more information, see README.md")
    print("="*70 + "\n")


def main():
    """Main setup function."""
    print("\n" + "="*70)
    print("  Wikidich Ebook Creator - Local Environment Setup")
    print("="*70)

    all_checks_passed = True

    # Check virtual environment
    if not show_virtual_env_info():
        print("\nSetup cancelled. Please set up a virtual environment first.")
        return

    # Run system checks
    all_checks_passed &= check_python_version()
    check_uv()  # informational only, not required

    if not all_checks_passed:
        print("\n" + "="*70)
        print_error("Some system requirements are missing!")
        print("="*70)
        print("\nPlease fix the issues above and run this script again.")
        sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        print("\n" + "="*70)
        print_error("Dependency installation failed!")
        print("="*70)
        sys.exit(1)

    # Test components
    test_playwright()  # This is optional, don't fail if it doesn't work
    test_pyqt6()

    # Show usage
    show_usage()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
        sys.exit(0)
