#!/usr/bin/env python3
"""Pinned artifact inventory and S3 transport. Dry runs never import boto3 or use a network.

Credentials, endpoint, bucket and prefix are accepted ONLY from environment.
Use upload_artifacts.py and restore_artifacts.py as the entry points.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'tools/artifacts-manifest.json'
MODEL_REV='de398b5192b2c1d5f8963aef56bf8df1f13c159e'
MODEL_SOURCE='https://huggingface.co/pyronear/yolov11s/tree/'+MODEL_REV
MODEL_SHA='5c17b5f917b3cd61bafd15b808cbe3c3b03e054e2e9f09ca72f6309d53d8e76b'
PREPARED=('coarse.npz','detailed.npz','metadata.json','map.json','background.png','forest.png','water.png')
LICENCES=('PYRONEAR-AGPL-3.0.txt','ARTIFACT-NOTICES.md')
CLIPS=('smoke.ogv','cloud.webm','glare.webm')
ALLOWED={*(f'placement/data/prepared/{p}' for p in PREPARED),*(f'station/media/{p}' for p in CLIPS),'station/models/smoke.onnx',*(f'tools/licenses/{p}' for p in LICENCES)}

def sha256(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def local_path(root,path):
    if path not in ALLOWED or PurePosixPath(path).is_absolute() or '..' in PurePosixPath(path).parts:
        raise ValueError(f'Artifact path not allowlisted: {path}')
    full=root/path
    if not full.resolve().is_relative_to(root.resolve()):raise ValueError('Artifact escapes repository (symlink).')
    if any(p.is_symlink() for p in (full,*full.parents)):
        raise ValueError('Symlinks are not accepted in artifact paths.')
    return full

def inventory(root=ROOT):
    metadata=json.loads((root/'placement/data/prepared/metadata.json').read_text())
    clips=json.loads((root/'station/footage.json').read_text())
    entries=[]
    def add(path,source,licence,**extra):
        full=local_path(root,path)
        if not full.is_file():raise FileNotFoundError(f'Missing artifact: {path}')
        entries.append(dict(path=path,size=full.stat().st_size,sha256=sha256(full),source=source,licence=licence,**extra))
    for name in PREPARED:
        add('placement/data/prepared/'+name,metadata['sources'],'CC-BY-4.0',
            attribution='National Land Survey of Finland Elevation model 10 m (2019); Syke CORINE Land Cover 2024; Natural Resources Institute Finland (Luke) MS-NFI 2023.',
            changes='Clipped/reprojected/aggregated EPSG:3067 rasters; PNGs are derived Web Mercator map images. See metadata.json and placement/README.md.')
    add('station/models/smoke.onnx',MODEL_SOURCE,'AGPL-3.0-only',attribution='Pyronear YOLO11s, Tenacious Tiger v8.3.0; Ultralytics ancestry.',changes='Unmodified upstream ONNX export.',
        source_access=dict(weights=f'https://huggingface.co/pyronear/yolov11s/resolve/{MODEL_REV}/best.pt',manifest=f'https://huggingface.co/pyronear/yolov11s/raw/{MODEL_REV}/manifest.yaml',training='https://github.com/pyronear/pyro-train',framework='https://github.com/ultralytics/ultralytics'))
    if entries[-1]['sha256']!=MODEL_SHA:raise ValueError('Model differs from the reviewed pinned export.')
    for clip in clips:
        if clip['filename'] not in CLIPS:continue
        add('station/media/'+clip['filename'],clip['source'],clip['license'],attribution=clip['author'],licence_url=clip['license_url'],changes=clip['changes'])
        if entries[-1]['sha256']!=clip['sha256']:raise ValueError('Clip differs from its reviewed source: '+clip['filename'])
    for name in LICENCES:
        add('tools/licenses/'+name,MODEL_SOURCE if name.startswith('PYRONEAR') else 'Project attribution notice','AGPL-3.0-only' if name.startswith('PYRONEAR') else 'CC0-1.0')
    return dict(schema=1,reviewed_on='2026-11-13',artifacts=sorted(entries,key=lambda e:e['path']),excluded=[dict(path='station/media/fog.webm',reason='Uploader asserts CC BY-SA 4.0, but Commons external licence review remains pending; excluded until provenance verified.',source='https://commons.wikimedia.org/wiki/File:Fog_covering_mountain_time_lapse.webm'),dict(path='placement/data/raw/',reason='Rebuild cache; prepared data is sufficient.'),dict(path='station/data/',reason='Runtime events and operator decisions are not public test artifacts.')])

def load_manifest(path,root=ROOT):
    manifest=json.loads(path.read_text())
    if manifest.get('schema')!=1:raise ValueError('Unsupported manifest schema.')
    seen=set()
    for e in manifest['artifacts']:
        local_path(root,e['path'])
        if e['path'] in seen:raise ValueError('Duplicate artifact path.')
        seen.add(e['path'])
        if not re.fullmatch('[0-9a-f]{64}',e['sha256']):raise ValueError('Invalid SHA-256.')
        if not isinstance(e['size'],int) or not 0<=e['size']<=512*1024*1024:raise ValueError('Invalid artifact size.')
        if not e.get('source') or not e.get('licence'):raise ValueError('Provenance required.')
    if len(seen)>len(ALLOWED):raise ValueError('Too many artifacts.')
    return manifest

def transport():
    required=('IRONSHARD_ENDPOINT','IRONSHARD_BUCKET','IRONSHARD_ACCESS_KEY_ID','IRONSHARD_SECRET_ACCESS_KEY')
    missing=[key for key in required if not os.environ.get(key)]
    if missing:raise ValueError('Missing environment variables: '+', '.join(missing))
    from urllib.parse import urlparse
    endpoint=os.environ['IRONSHARD_ENDPOINT']
    parsed=urlparse(endpoint)
    if parsed.scheme!='https' or not parsed.netloc or parsed.username or parsed.password or parsed.query:
        raise ValueError('IRONSHARD_ENDPOINT must be an HTTPS endpoint without credentials or query parameters.')
    import boto3
    from botocore.config import Config
    client=boto3.client('s3',endpoint_url=endpoint,aws_access_key_id=os.environ['IRONSHARD_ACCESS_KEY_ID'],aws_secret_access_key=os.environ['IRONSHARD_SECRET_ACCESS_KEY'],aws_session_token=os.environ.get('IRONSHARD_SESSION_TOKEN'),region_name=os.environ.get('IRONSHARD_REGION','us-east-1'),config=Config(signature_version='s3v4',s3={'addressing_style':'path'},retries={'max_attempts':3}))
    prefix=os.environ.get('IRONSHARD_PREFIX','junction-2026').strip('/')
    if '..' in prefix.split('/'):raise ValueError('Invalid object prefix.')
    return client,os.environ['IRONSHARD_BUCKET'],prefix

def object_key(prefix,path):return '/'.join(x for x in (prefix,path) if x)

def main(mode,argv=None,root=ROOT):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dry-run',action='store_true',help='No credentials/network needed; list sizes and SHA-256.')
    parser.add_argument('--manifest',type=Path,default=root/'tools/artifacts-manifest.json')
    if mode=='upload':parser.add_argument('--write-manifest',action='store_true',help='Regenerate the small reviewed inventory before transport.')
    else:parser.add_argument('--overwrite',action='store_true',help='Replace differing local artifacts, atomically, only after verifying the download.')
    args=parser.parse_args(argv)
    if getattr(args,'write_manifest',False):
        args.manifest.write_text(json.dumps(inventory(root),ensure_ascii=False,indent=2)+'\n')
    manifest=load_manifest(args.manifest,root)
    total=0
    for entry in manifest['artifacts']:
        path=local_path(root,entry['path'])
        if mode=='upload' and (not path.is_file() or path.stat().st_size!=entry['size'] or sha256(path)!=entry['sha256']):raise ValueError('Artifact differs from manifest: '+entry['path'])
        total+=entry['size']
        print(f"{'WOULD UPLOAD' if mode=='upload' else 'WOULD RESTORE'}\t{entry['path']}\t{entry['size']} bytes\tsha256:{entry['sha256']}")
    for e in manifest.get('excluded',[]):print('EXCLUDED\t'+e['path']+'\t'+e['reason'])
    print(f'{len(manifest["artifacts"])} artifacts, {total} bytes; manifest included in upload.')
    if args.dry_run:return 0
    client,bucket,prefix=transport()
    for entry in manifest['artifacts']:
        path=local_path(root,entry['path']);key=object_key(prefix,entry['path'])
        if mode=='upload':
            with path.open('rb') as f:client.upload_fileobj(f,bucket,key,ExtraArgs={'Metadata':{'sha256':entry['sha256'],'licence':entry['licence']}})
            print('UPLOADED\t'+entry['path'])
        else:
            if path.exists():
                if path.stat().st_size==entry['size'] and sha256(path)==entry['sha256']:
                    print('VERIFIED LOCAL\t'+entry['path']);continue
                if not args.overwrite:raise ValueError('Local file differs; use --overwrite: '+entry['path'])
            path.parent.mkdir(parents=True,exist_ok=True)
            tmp=None
            try:
                with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.restore-',delete=False) as f:
                    tmp=Path(f.name)
                    # Stream with a byte cap; never trust an unbounded remote object.
                    body=client.get_object(Bucket=bucket,Key=key)['Body']
                    try:
                        count=0
                        for chunk in body.iter_chunks(chunk_size=1024*1024):
                            count+=len(chunk)
                            if count>entry['size']:raise ValueError('Remote object larger than pinned size.')
                            f.write(chunk)
                    finally:body.close()
                if tmp.stat().st_size!=entry['size'] or sha256(tmp)!=entry['sha256']:raise ValueError('Downloaded checksum/size mismatch: '+entry['path'])
                tmp.replace(path);print('RESTORED\t'+entry['path'])
            finally:
                if tmp:tmp.unlink(missing_ok=True)
    if mode=='upload':
        client.put_object(Bucket=bucket,Key=object_key(prefix,'tools/artifacts-manifest.json'),Body=args.manifest.read_bytes(),ContentType='application/json')
    return 0

def entry(mode):
    try:return main(mode)
    except Exception as e:
        # SDK exceptions can echo signed URLs/credentials. Print only local errors.
        if type(e) in (ValueError, FileNotFoundError):print(str(e),file=sys.stderr)
        else:print(f'{type(e).__name__}: artifact transfer failed; check endpoint, permissions and connectivity.',file=sys.stderr)
        return 1
