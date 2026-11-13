"""Which machine produced the measured timings, so the panel can say so."""
from functools import lru_cache
from pathlib import Path
import platform
import subprocess

DEVICE_TREE_MODELS = (Path("/proc/device-tree/model"), Path("/sys/firmware/devicetree/base/model"))


def _cpu_model():
    system = platform.system()
    try:
        if system == "Darwin":
            out = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"], capture_output=True, text=True, timeout=2)
            if out.returncode == 0 and out.stdout.strip():
                return out.stdout.strip()
        elif system == "Linux":
            for line in Path("/proc/cpuinfo").read_text(errors="replace").splitlines():
                key, _, value = line.partition(":")
                if key.strip().lower() in ("model name", "hardware") and value.strip():
                    return value.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    return platform.processor() or None


def _board_model():
    for path in DEVICE_TREE_MODELS:
        try:
            return path.read_bytes().rstrip(b"\0").decode(errors="replace").strip() or None
        except OSError:
            continue
    return None


def describe(system, machine, release, cpu, board):
    # Matched on the Linux device-tree model string. The exact UNO Q string has not
    # been read from a real board; "UNO Q" is expected to appear in it.
    is_uno_q = bool(board and "uno q" in board.lower())
    os_name = {"Darwin": "macOS", "Linux": "Linux"}.get(system, system)
    if system == "Darwin":
        release = platform.mac_ver()[0] or release
    what = board or cpu or machine or "bilinmeyen makine"
    label = f"Ölçüm bu cihazda: {what} · {os_name} {release} · {machine}"
    label += " · Arduino UNO Q" if is_uno_q else " · UNO Q değil"
    return {"system": os_name, "os_release": release, "architecture": machine, "cpu_model": cpu,
            "board_model": board, "is_uno_q": is_uno_q, "label": label}


@lru_cache(maxsize=1)
def machine_identity():
    """Static description of this host. No host name or user name is included."""
    return describe(platform.system(), platform.machine(), platform.release(), _cpu_model(), _board_model())
