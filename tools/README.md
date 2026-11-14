# IronShard artifact handoff

Run from the repository root. Source files and small manifests are suitable for git; model/data/media bytes stay at their existing ignored paths. No credentials are read from files or command-line arguments. Nothing has been uploaded.

## Review and upload

```sh
cd placement
uv sync --frozen --group deploy --python 3.12
cd ..
placement/.venv/bin/python tools/upload_artifacts.py --dry-run
```

The dry run needs neither boto3 nor credentials/network. It checks local bytes against `tools/artifacts-manifest.json`, lists paths, sizes and SHA-256, and explains exclusions. `--write-manifest --dry-run` regenerates the small manifest after deliberate data preparation; review its diff before uploading. Changed model/clip checksums are rejected rather than silently accepted.

Provide these in the owner's environment (for example through a password manager's environment injection), **never in a repository file**:

```text
IRONSHARD_ENDPOINT        HTTPS S3-compatible endpoint
IRONSHARD_BUCKET          existing bucket name
IRONSHARD_ACCESS_KEY_ID   write key for upload, read key for restore
IRONSHARD_SECRET_ACCESS_KEY
IRONSHARD_REGION          optional, default us-east-1
IRONSHARD_PREFIX          optional, default junction-2026
IRONSHARD_SESSION_TOKEN   optional
```

With those variables exported, the exact upload command is:

```sh
placement/.venv/bin/python tools/upload_artifacts.py
```

The script uses S3 Signature V4 and path-style addressing. It uploads the 13 allowlisted objects, then the manifest, preserving SHA-256 and licence object metadata. It does not create buckets or change ACLs. The bucket owner must arrange judge read access (public object GET or read-only credentials) in IronShard. Endpoint compatibility and public-read policy have **not** been tested against a real account.

## Restore a fresh clone

Install the placement deploy dependency group as above, export the endpoint/bucket and read credentials, then:

```sh
placement/.venv/bin/python tools/restore_artifacts.py --dry-run
placement/.venv/bin/python tools/restore_artifacts.py
```

The committed manifest is the trust anchor: the restore script never substitutes a remote manifest. Objects are streamed with a size limit to temporary files, verified against SHA-256 and size, and renamed atomically. Already matching files are left alone. Differing local files require explicit `--overwrite`. Arbitrary paths, symlinks, unreviewed runtime files and oversized objects are rejected. Credentials are never printed, and SDK exceptions are redacted to their type.

The existing station default expects the excluded fog clip. A **smoke + cloud recorded-clip demo config** is provided in this directory so bucket-only restores work without editing the station:

```bash
cd station
uv sync --locked --python 3.11
# Bash: choose a private station panel secret before starting the demo.
read -rs -p 'Station secret: ' ACORN_PANEL_SECRET; export ACORN_PANEL_SECRET; echo
uv run --offline --frozen forest-station --config ../tools/station-bucket-demo.toml serve --port 8080
```

The panel and all data APIs require authentication. Without the server secret, data routes return 503. Open the local panel and sign in, or use this block in a second **Bash** terminal in `station/`, loading the same secret. On macOS zsh use `read -s 'ACORN_PANEL_SECRET?Station secret: '; export ACORN_PANEL_SECRET; echo` instead of the Bash `read` line. Disable shell tracing before entering secrets.

```bash
ACORN_BASE_URL=http://127.0.0.1:8080
read -rs -p 'Station secret: ' ACORN_PANEL_SECRET; export ACORN_PANEL_SECRET; echo
ACORN_COOKIE_JAR=$(mktemp); chmod 600 "$ACORN_COOKIE_JAR"
trap 'rm -f "$ACORN_COOKIE_JAR"' EXIT
uv run --offline --frozen python -c 'import json,os; print(json.dumps({"secret":os.environ["ACORN_PANEL_SECRET"]}))' | \
  curl --fail-with-body -sS -c "$ACORN_COOKIE_JAR" -X POST "$ACORN_BASE_URL/api/auth/login" \
    -H 'Content-Type: application/json' --data-binary @-
curl --fail-with-body -sS -b "$ACORN_COOKIE_JAR" "$ACORN_BASE_URL/api/status"
rm -f "$ACORN_COOKIE_JAR"
```

The secret stays in the environment and reaches login via stdin; never put it in a command argument or repository file. Keep the private cookie jar only for the checks you need. **Server restart invalidates it:** log in again after every restart (401); repeated failed logins may require a five-minute wait (429). HTTP errors fail the curl command. See [station authentication](../station/README.md#communication) and the [demo runbook](../DEMO.md) for the same flow. This is a recorded-clip/local simulation demo; it does not validate hardware, real LoRa or AP setup.

No station feed is linked or proxied by the placement website. This alternative config retains two active inputs and all alarm defaults.

## Licence review

See [ARTIFACT-NOTICES.md](licenses/ARTIFACT-NOTICES.md) and the per-artifact source, author, licence and change fields in [artifacts-manifest.json](artifacts-manifest.json).

- NLS / Syke / Luke prepared rasters and derived offline map images: **CC BY 4.0**, redistribution permitted with attribution/change notices.
- Pyronear YOLO11s ONNX: **AGPL-3.0**, redistribution permitted subject to licence and corresponding-source obligations; full licence and upstream editable-weight/training-source references accompany the manifest. A complete corresponding-source archive was not independently assembled or audited.
- Original smoke, cloud and glare clips: **CC BY-SA 4.0 / 3.0 / 2.0** respectively, with authors and share-alike notices retained.
- **Excluded fog.webm:** uploader asserts CC BY-SA 4.0, but Commons' external licence review remains pending. This is unresolved provenance, not an identified prohibition. All other reviewed datasets/clips permit redistribution under their terms.
- Raw download caches, operator events/evidence, databases and local configs are excluded. Browser map code remains in git under its vendored Leaflet BSD notice.

The scripts were run only with `--dry-run`. No real upload/download or IronShard account interaction was performed.
