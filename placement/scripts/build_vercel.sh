#!/bin/sh
# Stage a self-contained Vercel bundle in placement/.vercel-build (git-ignored).
# Usage, from placement/:  sh scripts/build_vercel.sh && (cd .vercel-build && vercel deploy --prod)
# The bundle holds the app, the UI and the seven prepared map/raster files only.
# Runtime dependencies only: the map overlay writer needs rasterio; uvicorn, httpx and dev tools are left out.
set -eu
HERE=$(cd "$(dirname "$0")/.." && pwd)
OUT="$HERE/.vercel-build"
mkdir -p "$OUT"
# Keep .vercel (project link) between runs; replace everything else.
find "$OUT" -mindepth 1 -maxdepth 1 ! -name .vercel -exec rm -rf {} +
mkdir -p "$OUT/data/prepared"
for f in metadata.json coarse.npz detailed.npz map.json background.png forest.png water.png; do
  [ -f "$HERE/data/prepared/$f" ] || { echo "Missing prepared artifact: $f" >&2; exit 1; }
  cp "$HERE/data/prepared/$f" "$OUT/data/prepared/$f"
done
rsync -a --exclude __pycache__ --exclude '*.pyc' --exclude '*.nbc' --exclude '*.nbi' "$HERE/forest_placement" "$OUT/"
rsync -a --exclude .DS_Store "$HERE/static" "$OUT/"
cp "$HERE/brand.json" "$OUT/brand.json"
# Vercel's Python runtime has no system libexpat, which rasterio's GDAL needs.
# Take it from the official Debian 11 package (built against an older glibc than the runtime's).
EXPAT_DEB='libexpat1_2.2.10-2+deb11u5_amd64.deb'
EXPAT_SHA256='5744040c4735bcdd51238aebfa3e402b857244897f1007f61154982ebe5abbd7'
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -sfLo "$TMP/expat.deb" "https://deb.debian.org/debian/pool/main/e/expat/$EXPAT_DEB"
[ "$(shasum -a 256 "$TMP/expat.deb" | cut -d' ' -f1)" = "$EXPAT_SHA256" ] || { echo "libexpat package checksum mismatch" >&2; exit 1; }
(cd "$TMP" && ar x expat.deb && tar -xf data.tar.xz)
mkdir -p "$OUT/lib"
cp "$TMP/lib/x86_64-linux-gnu/libexpat.so.1.6.12" "$OUT/lib/libexpat.so.1"
printf '3.12\n' > "$OUT/.python-version"
cat > "$OUT/requirements.txt" <<'REQ'
numpy==2.5.4
numba==0.68.1
llvmlite==0.50.0
pyproj==3.8.0
rasterio==1.5.2
shapely==2.2.0
pillow==13.0.0
fastapi==0.162.7
starlette==1.10.0
pydantic==2.14.3
pydantic-core==2.50.4
REQ
cat > "$OUT/main.py" <<'PY'
"""Vercel entrypoint. The function filesystem is read-only except /tmp."""
import os

os.environ.setdefault('PLACEMENT_PRODUCTION', '1')
os.environ.setdefault('PLACEMENT_CACHE', '/tmp/placement-results')
os.environ.setdefault('NUMBA_CACHE_DIR', '/tmp/numba-cache')
os.environ.setdefault('NUMBA_CPU_NAME', 'generic')
# Vercel's edge sets X-Forwarded-For to the visitor address; the function is not reachable directly.
os.environ.setdefault('PLACEMENT_PROXY_HOPS', '1')

# Load the bundled libexpat first so rasterio's GDAL finds it by name.
import ctypes
from pathlib import Path
_expat = Path(__file__).resolve().parent / 'lib' / 'libexpat.so.1'
if _expat.is_file() and os.uname().sysname == 'Linux':
    ctypes.CDLL(str(_expat), mode=ctypes.RTLD_GLOBAL)

from forest_placement.api import app  # noqa: E402,F401
PY
cat > "$OUT/vercel.json" <<'JSON'
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "framework": "fastapi",
  "functions": { "main.py": { "maxDuration": 60 } }
}
JSON
echo "Staged: $OUT ($(du -sh "$OUT" | cut -f1))"
