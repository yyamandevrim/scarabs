"""Download attributed real videos; no synthetic footage is included here."""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def main():
    directory=ROOT/'media';directory.mkdir(exist_ok=True)
    for item in json.loads((ROOT/'footage.json').read_text()):
        path=directory/item['filename']
        if path.is_file() and item['sha256'] and digest(path)==item['sha256']:
            print(f"Verified {path.name}");continue
        temporary=path.with_suffix(path.suffix+'.part')
        request=urllib.request.Request(item['url'],headers={'User-Agent':'ForestStationHackathon/0.1 (offline research prototype)'})
        try:
            with urllib.request.urlopen(request,timeout=120) as response,temporary.open('wb') as output:
                shutil.copyfileobj(response,output)
            actual=digest(temporary)
            if item['sha256'] and actual!=item['sha256']:
                raise RuntimeError(f"Hash mismatch for {item['filename']}")
            temporary.replace(path)
            print(f"{path.name}: {item['author']}; {item['license']}; SHA256 {actual}")
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
    print('Media stays local and gitignored. Attribution and licences: footage.json')

if __name__=='__main__':
    main()
