#!/usr/bin/env bash
#
# Dependency compatibility check.
#
# Builds a throwaway uv venv for one Python version, installs the requirements, and runs:
#   1. install        pip resolve + install succeeds
#   2. import         every wikidich_ebook module imports
#   3. gui_import     gui.py imports (QT_QPA_PLATFORM=offscreen)
#   4. offline        tests/offline_check.py (parser, scraper, make_ebook on fixtures)
#   5. live_toc       optional: main.py URL --toc-only      (needs --live URL)
#   6. live_full      optional: full download + EPUB build  (needs --full URL)
# The project .venv is never touched. The PyInstaller build is not run here; see ANN-13.
#
# Usage:
#   scripts/compat_check.sh --python 3.13 [options]
#
# Options:
#   --python X.Y        Python version for the venv (default: 3.12)
#   --latest            Ignore version specifiers in requirements and install the newest of everything
#   --pin SPEC          Extra constraint, repeatable (e.g. --pin ebooklib==0.20). Use to bisect.
#   --with-build        Also install the non-"-r" lines of requirements-build.txt (pyinstaller)
#   --live URL          Run a live --toc-only against this novel URL
#   --full URL          Run a full download + EPUB build for this URL (use a SMALL novel)
#   --out FILE          Append a one-line markdown result row to FILE
#   --keep              Keep the venv and work dir afterwards (printed at the end)
#
# Exit code is non-zero if any step failed.

set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_VERSION="3.12"
LATEST=0
WITH_BUILD=0
LIVE_URL=""
FULL_URL=""
OUT_FILE=""
KEEP=0
PINS=()

while [ $# -gt 0 ]; do
    case "$1" in
        --python)      PY_VERSION="$2"; shift 2 ;;
        --latest)      LATEST=1; shift ;;
        --pin)         PINS+=("$2"); shift 2 ;;
        --with-build)  WITH_BUILD=1; shift ;;
        --live)        LIVE_URL="$2"; shift 2 ;;
        --full)        FULL_URL="$2"; shift 2 ;;
        --out)         OUT_FILE="$2"; shift 2 ;;
        --keep)        KEEP=1; shift ;;
        -h|--help)     sed -n '2,31p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "Unknown option: $1" >&2; exit 2 ;;
    esac
done

command -v uv >/dev/null || { echo "uv is required (brew install uv)" >&2; exit 2; }

WORK="$(mktemp -d "${TMPDIR:-/tmp}/wikidich_compat.XXXXXX")"
ENV_DIR="$WORK/venv"
PY="$ENV_DIR/bin/python"
cleanup() {
    if [ "$KEEP" -eq 1 ]; then
        echo "Kept: $WORK"
    else
        rm -rf "$WORK"
    fi
}
trap cleanup EXIT

# Keep only package names (strip ==, >=, etc.) when testing "latest"
loosen() { grep -vE '^\s*(#|-r|$)' "$1" | sed -E 's/[[:space:]]*(==|>=|<=|~=|!=|<|>).*$//'; }
plain()  { grep -vE '^\s*(#|-r|$)' "$1"; }

REQ="$WORK/requirements.txt"
: > "$REQ"
if [ "$LATEST" -eq 1 ]; then
    loosen "$ROOT/requirements.txt" >> "$REQ"
    [ "$WITH_BUILD" -eq 1 ] && loosen "$ROOT/requirements-build.txt" >> "$REQ"
else
    plain "$ROOT/requirements.txt" >> "$REQ"
    [ "$WITH_BUILD" -eq 1 ] && plain "$ROOT/requirements-build.txt" >> "$REQ"
fi

CONSTRAINTS="$WORK/constraints.txt"
: > "$CONSTRAINTS"
for p in ${PINS[@]+"${PINS[@]}"}; do echo "$p" >> "$CONSTRAINTS"; done

RESULTS=()
FAILED=0
record() { # name status
    RESULTS+=("$1=$2")
    [ "$2" = "FAIL" ] && FAILED=1
    printf '  %-12s %s\n' "$1" "$2"
}
run_step() { # name command...
    local name="$1"; shift
    echo "── $name"
    if "$@"; then record "$name" PASS; else record "$name" FAIL; fi
}

echo "Python $PY_VERSION | latest=$LATEST | pins=${PINS[*]:-none} | work=$WORK"

install_deps() {
    uv venv --python "$PY_VERSION" "$ENV_DIR" >/dev/null || return 1
    uv pip install --python "$PY" -r "$REQ" -c "$CONSTRAINTS" || return 1
}
run_step install install_deps

if [ "${RESULTS[0]}" != "install=PASS" ]; then
    echo "Install failed; skipping remaining steps."
else
    import_modules() {
        (cd "$WORK" && "$PY" -c "
import sys; sys.path.insert(0, '$ROOT')
import wikidich_ebook, wikidich_ebook.workflow, wikidich_ebook.parser, wikidich_ebook.scraper
import wikidich_ebook.downloader, wikidich_ebook.epub_builder, wikidich_ebook.utils, wikidich_ebook.updater
print('wikidich_ebook', wikidich_ebook.__version__)")
    }
    run_step import import_modules

    gui_import() {
        (cd "$WORK" && QT_QPA_PLATFORM=offscreen "$PY" -c "
import sys; sys.path.insert(0, '$ROOT')
import gui; print('gui imported')")
    }
    run_step gui_import gui_import

    offline_check() {
        (cd "$WORK" && QT_QPA_PLATFORM=offscreen "$PY" "$ROOT/tests/offline_check.py" --json "$WORK/offline.json")
    }
    run_step offline offline_check

    if [ -n "$LIVE_URL" ] || [ -n "$FULL_URL" ]; then
        # Browser binaries are versioned with the playwright package
        echo "── playwright install chromium"
        "$ENV_DIR/bin/playwright" install chromium || echo "  (browser install failed; live steps may fail)"
    fi

    if [ -n "$LIVE_URL" ]; then
        live_toc() { (mkdir -p "$WORK/live_toc" && cd "$WORK/live_toc" && "$PY" "$ROOT/main.py" "$LIVE_URL" --toc-only); }
        run_step live_toc live_toc
    else
        RESULTS+=("live_toc=SKIP")
    fi

    if [ -n "$FULL_URL" ]; then
        live_full() {
            mkdir -p "$WORK/live_full" && cd "$WORK/live_full" || return 1
            "$PY" "$ROOT/main.py" "$FULL_URL" || return 1
            ls ./*.epub >/dev/null 2>&1 || { echo "no EPUB produced"; return 1; }
            "$PY" -c "
import glob, zipfile
for p in glob.glob('*.epub'):
    assert zipfile.ZipFile(p).testzip() is None, p
    print('valid zip:', p)"
        }
        run_step live_full live_full
    else
        RESULTS+=("live_full=SKIP")
    fi
fi

echo
echo "Installed versions:"
uv pip list --python "$PY" 2>/dev/null | grep -iE '^(beautifulsoup4|lxml|ebooklib|pandas|numpy|requests|unidecode|playwright|pyqt6|packaging|pyinstaller)[[:space:]]' || true

SUMMARY="python=$PY_VERSION latest=$LATEST pins=${PINS[*]:-none} ${RESULTS[*]}"
echo
echo "RESULT $SUMMARY"
if [ -n "$OUT_FILE" ]; then
    VERS="$(uv pip list --python "$PY" 2>/dev/null | grep -iE '^(beautifulsoup4|lxml|ebooklib|pandas|playwright|pyqt6|pyinstaller)[[:space:]]' | awk '{printf "%s %s; ", $1, $2}')"
    echo "| $PY_VERSION | $([ "$LATEST" -eq 1 ] && echo latest || echo file) | ${PINS[*]:-none} | ${RESULTS[*]} | $VERS |" >> "$OUT_FILE"
fi

exit "$FAILED"
