"""B03 regression: the frontend must never inject server/user data as HTML.

Static check over every page script. (A browser-level check with a malicious history entry was also done
manually; see README "Testing".)"""
import re
from pathlib import Path

FRONTEND = Path(__file__).resolve().parent.parent / "frontend"


def _scripts():
    for path in FRONTEND.glob("*.js"):
        yield path.name, path.read_text()
    for path in FRONTEND.glob("*.html"):
        for block in re.findall(r"<script>(.*?)</script>", path.read_text(), re.DOTALL):
            yield path.name, block


def test_no_innerhtml_or_outerhtml_or_insertadjacenthtml():
    offenders = [(name, m.group()) for name, src in _scripts()
                 for m in re.finditer(r"\.(innerHTML|outerHTML)\s*[+]?=|insertAdjacentHTML|document\.write", src)]
    assert offenders == [], f"unsafe HTML sinks found: {offenders}"


def test_dead_dashboard_script_is_gone():
    assert not (FRONTEND / "dashboard.js").exists()
