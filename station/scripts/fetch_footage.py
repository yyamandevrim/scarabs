"""Download attributed real videos; no synthetic footage is included here."""
import hashlib
import json
from pathlib import Path
import shutil
import urllib.request
import urllib.error
import time
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import sys

ROOT=Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def download(url, temporary, attempts=5):
    """Serial requests with bounded retries; respect Wikimedia's Retry-After."""
    request=urllib.request.Request(url,headers={'User-Agent':'ACORN/0.2 (https://github.com/yyamandevrim/scarabs; offline research prototype)'})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request,timeout=120) as response,temporary.open('wb') as output:
                shutil.copyfileobj(response,output)
            return
        except urllib.error.HTTPError as exc:
            temporary.unlink(missing_ok=True)
            if exc.code not in (429,503) or attempt==attempts-1:
                raise
            delay=30*2**attempt
            retry=(exc.headers or {}).get('Retry-After')
            if retry:
                try:
                    requested=float(retry) if retry.strip().isdigit() else (parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds()
                    delay=max(delay,requested)
                except (ValueError,TypeError,OverflowError):
                    pass
            print(f'HTTP {exc.code}; waiting {delay:g}s before retry {attempt+2}/{attempts}',file=sys.stderr,flush=True)
            time.sleep(delay)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise


def main():
    directory=ROOT/'media';directory.mkdir(exist_ok=True)
    for item in json.loads((ROOT/'footage.json').read_text()):
        path=directory/item['filename']
        if path.is_file() and item['sha256'] and digest(path)==item['sha256']:
            print(f"Verified {path.name}");continue
        temporary=path.with_suffix(path.suffix+'.part')
        try:
            download(item['url'],temporary)
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
