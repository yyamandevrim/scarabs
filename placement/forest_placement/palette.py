"""Map category colours come from the same local tokens as the browser legend."""
from pathlib import Path
import re

TOKENS=Path(__file__).resolve().parents[1]/'static/tokens.css'
def map_color(category,alpha):
    match=re.search(r'--map-'+re.escape(category)+r':\s*#([0-9a-fA-F]{6})\s*;',TOKENS.read_text())
    if match is None:raise ValueError('Missing map colour token: '+category)
    color=match.group(1)
    return [int(color[i:i+2],16) for i in (0,2,4)]+[alpha]
