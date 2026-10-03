"""Validate, then build deck, page, SVGs, share cards and video. Stops at the first failure.

  python3 run_all.py <article_dir>               # everything
  python3 run_all.py <article_dir> --no-video    # skip the slow video render
  python3 run_all.py <article_dir> --no-deck     # skip the PowerPoint deck
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def run(cmd):
    r = subprocess.run(cmd)
    if r.returncode:
        sys.exit(f"stopped: {' '.join(map(str, cmd[:2]))} failed")


def py(script, *args):
    run([sys.executable, str(HERE / script), *args])


if __name__ == "__main__":
    art = sys.argv[1]
    py("validate.py", art)
    if "--no-deck" not in sys.argv:
        py("deck_data.py", art)
        run(["node", str(HERE / "build_deck.js"), art])
        py("finish_deck.py", art)
        py("preview_deck.py", art)
    py("build_page.py", art)
    py("render_cards.py", art)
    if "--no-video" not in sys.argv:
        py("render_video.py", art)
    print(f"done: {Path(art).resolve() / 'out'}")
