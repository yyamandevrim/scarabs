"""Run the actual browser presentation rules, including legacy API responses."""
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_browser_metric_contract():
    subprocess.run(['node', '--test', str(ROOT / 'tests/ui_metrics.cjs')], check=True, cwd=ROOT)
