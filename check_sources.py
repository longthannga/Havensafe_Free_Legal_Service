"""Monthly check: did any organization change its hours on its website?

This does NOT try to parse hours. For each source page it keeps only the
lines that mention a weekday or a time, and saves them to
data/snapshots/<id>.txt. The GitHub Action then opens a pull request if any
snapshot changed, so a person can read the diff and update data/hours.json.

That way a website redesign can never silently put wrong hours on the sheet.
"""
import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).parent
SNAPSHOT_DIR = ROOT / "data" / "snapshots"
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")
}

DAY_RE = re.compile(r"\b(mon|tues?|wed(nes)?|thu(rs)?|fri|sat(ur)?|sun)(day)?s?\b", re.I)
TIME_RE = re.compile(r"\b\d{1,2}(:\d{2})?\s*(a\.?m\.?|p\.?m\.?)|\bnoon\b|\bclosed\b", re.I)


def hours_lines(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript", "nav", "header", "footer"]):
        tag.decompose()

    lines = []
    for line in soup.get_text("\n").splitlines():
        line = " ".join(line.replace("\xa0", " ").split())
        if line and (DAY_RE.search(line) or TIME_RE.search(line)):
            if not lines or lines[-1] != line:
                lines.append(line)
    return lines


def main():
    hours = json.loads((ROOT / "data" / "hours.json").read_text(encoding="utf-8"))
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    problems = 0

    for org in hours["organizations"]:
        out = SNAPSHOT_DIR / f"{org['id']}.txt"
        try:
            resp = requests.get(org["source_url"], headers=HEADERS, timeout=30)
            resp.raise_for_status()
            lines = hours_lines(resp.content)
            if not lines:
                lines = ["NO HOURS FOUND - the page layout may have changed or moved"]
                problems += 1
        except Exception as e:  # keep going so one bad site doesn't hide the others
            lines = [f"FETCH FAILED - {type(e).__name__}: {e}"]
            problems += 1

        header = f"# {org['name']}\n# {org['source_url']}\n"
        out.write_text(header + "\n".join(lines) + "\n", encoding="utf-8")
        print(f"{org['id']}: {len(lines)} line(s)")

    print(f"{problems} source(s) need attention" if problems else "All sources fetched")
    return 0


if __name__ == "__main__":
    sys.exit(main())
