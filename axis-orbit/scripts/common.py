"""Shared helpers: load orbit.json, resolve {metric_id} placeholders, brand tokens."""
import json
import re
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent
PLACEHOLDER = re.compile(r"\{(\w+)\}")

COLORS = {
    "healthygreen": "#39B54A",
    "freshgreen": "#8DC63F",
    "trustturquoise": "#00A79D",
    "seafoam": "#74C7A7",
    "strengthblue": "#003C4C",
    "white": "#ffffff",
}


def load(article_dir):
    article = Path(article_dir).resolve()
    orbit = json.loads((article / "orbit.json").read_text())
    metrics = {m["id"]: m["value"] for m in orbit["metrics"]}
    return article, orbit, metrics


def resolve(obj, metrics):
    """Replace {id} with the locked metric value, recursively. Minus signs become U+2212."""
    if isinstance(obj, str):
        return PLACEHOLDER.sub(lambda k: metrics[k.group(1)].replace("-", "−") if metrics[k.group(1)].startswith("-") else metrics[k.group(1)], obj)
    if isinstance(obj, list):
        return [resolve(x, metrics) for x in obj]
    if isinstance(obj, dict):
        return {k: resolve(v, metrics) for k, v in obj.items()}
    return obj


def num(s):
    """'1,234' -> 1234.0, '5.7%' -> 5.7, '9.08x' -> 9.08, '−58.8%' -> -58.8"""
    s = str(s).replace("−", "-")
    m = re.search(r"-?\d[\d,]*(?:\.\d+)?", s)
    return float(m.group(0).replace(",", "")) if m else 0.0


def color(name):
    return COLORS.get(name, name)
