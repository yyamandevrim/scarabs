"""Fetch the pinned official Pyronear CPU export and verify both hashes."""
from pathlib import Path
import hashlib
import shutil
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
URL = "https://huggingface.co/pyronear/yolov11s/resolve/de398b5192b2c1d5f8963aef56bf8df1f13c159e/onnx_cpu.tar.gz"
ARCHIVE_SHA = "31b00117575defe6ef2212ac747f1c24b7605211850cd7cf43f11bfd8ca22a7c"
MODEL_SHA = "5c17b5f917b3cd61bafd15b808cbe3c3b03e054e2e9f09ca72f6309d53d8e76b"


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f,"sha256").hexdigest()


def main():
    directory = ROOT/"models"
    directory.mkdir(exist_ok=True)
    destination = directory/"smoke.onnx"
    if destination.exists() and digest(destination)==MODEL_SHA:
        print(f"Verified existing {destination}")
        return
    archive = directory/"export.tar.gz"
    request=urllib.request.Request(URL,headers={"User-Agent":"ForestStation/0.1"})
    with urllib.request.urlopen(request,timeout=120) as response, archive.open("wb") as output:
        shutil.copyfileobj(response,output)
    if digest(archive)!=ARCHIVE_SHA:
        archive.unlink()
        raise RuntimeError("Pyronear archive hash mismatch")
    temporary=directory/"smoke.onnx.part"
    # Read only the expected member, never extract archive paths.
    with tarfile.open(archive) as tar:
        with tar.extractfile("./best.onnx") as source, temporary.open("wb") as output:
            shutil.copyfileobj(source,output)
    if digest(temporary)!=MODEL_SHA:
        temporary.unlink()
        raise RuntimeError("Pyronear ONNX model hash mismatch")
    temporary.replace(destination)
    print(f"Downloaded {destination}\nSHA256 {MODEL_SHA}\nSource {URL}\nLicence AGPL-3.0")

if __name__=="__main__":
    main()
