"""Build a local article preview from separately supplied template and chart data.

No experiment, inference, network requests or deployment.
"""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--template", type=Path, required=True)
parser.add_argument("--data", type=Path, required=True)
parser.add_argument("--output", type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parent
html = args.template.read_text()
for marker in ("/* STYLE */", "/* DATA */", "/* SCRIPT */"):
    if html.count(marker) != 1:
        raise ValueError("Template must contain exactly one " + marker)
data = json.loads(args.data.read_text())
css = (root / "reference-style.css").read_text() + "\n" + (root / "article.css").read_text()
html = html.replace("/* STYLE */", css).replace("/* DATA */", json.dumps(data).replace("</", "<\\/"))
html = html.replace("/* SCRIPT */", (root / "article.js").read_text())
with args.output.open("x") as output:
    output.write(html)
