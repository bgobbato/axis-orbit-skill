"""Validate, then build page, SVGs, share cards and video. Stops at the first failure.

  python3 run_all.py <article_dir>            # everything
  python3 run_all.py <article_dir> --no-video # skip the slow video render
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent


def run(script, *args):
    r = subprocess.run([sys.executable, str(HERE / script), *args])
    if r.returncode:
        sys.exit(f"stopped: {script} failed")


if __name__ == "__main__":
    art = sys.argv[1]
    run("validate.py", art)
    run("build_page.py", art)
    run("render_cards.py", art)
    if "--no-video" not in sys.argv:
        run("render_video.py", art)
    print(f"done: {Path(art).resolve() / 'out' / 'page'}")
