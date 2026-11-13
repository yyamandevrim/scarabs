"""One running station per data directory; maintenance commands check it."""
import fcntl
import os
from pathlib import Path

LOCK_NAME = "station.lock"


class DataDirBusy(RuntimeError):
    pass


def acquire(data_dir):
    """Hold an exclusive advisory lock for the life of the server process."""
    path = Path(data_dir) / LOCK_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    handle = open(path, "a+")
    try:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        handle.close()
        raise DataDirBusy(f"Another station process is using {Path(data_dir)}; stop it first")
    handle.seek(0)
    handle.truncate()
    handle.write(str(os.getpid()))
    handle.flush()
    return handle


def release(handle):
    if handle is not None:
        try:
            fcntl.flock(handle, fcntl.LOCK_UN)
        finally:
            handle.close()


def in_use(data_dir):
    path = Path(data_dir) / LOCK_NAME
    if not path.exists():
        return False
    with open(path, "a+") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return True
        fcntl.flock(handle, fcntl.LOCK_UN)
    return False
