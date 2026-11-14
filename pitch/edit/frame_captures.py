#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pillow>=11,<13"]
# ///
"""Encode timestamped viewport JPEGs and add original, logo-free device frames.

Recordings are local/ignored. No screen content is painted, stretched or invented.
"""
import json,subprocess,argparse
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'pitch/captures/en'
DEST=ROOT/'pitch/captures/mockups/clips'
def run(*args):subprocess.run(list(map(str,args)),check=True)
def encode(folder):
 meta=json.loads((folder/'clock.json').read_text());c=meta['clock'];lines=[]
 for i,row in enumerate(c):
  with Image.open(folder/row['file']) as im:im.verify()
  dt=(c[i+1]['t']-row['t']) if i+1<len(c) else .1
  lines.extend([f"file '{row['file']}'",f'duration {dt:.6f}'])
 lines.append(f"file '{c[-1]['file']}'");lst=folder/'frames.txt';lst.write_text('\n'.join(lines)+'\n')
 out=BASE/(folder.name+'.mp4');run('ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',lst,'-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2,fps=30','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',out);return out

def frame(src,kind):
 DEST.mkdir(parents=True,exist_ok=True);work=BASE/'frames';work.mkdir(exist_ok=True)
 im=Image.new('RGB',(1920,1080),'#090e13');d=ImageDraw.Draw(im)
 if kind!='phone':d.rectangle((0,1010,1920,1080),fill='#0f161d')
 if kind=='phone':
  d.rounded_rectangle((714,36,1206,1044),radius=68,fill='#33404a',outline='#6b757c',width=3)
  d.rounded_rectangle((720,42,1200,1038),radius=62,fill='#06090b')
  x,y,w,h=738,66,444,964
  d.rounded_rectangle((704,230,714,340),radius=4,fill='#4c5861');d.rounded_rectangle((1206,265,1215,385),radius=4,fill='#4c5861')
 else:
  d.rounded_rectangle((280,16,1640,796),radius=22,fill='#323d46',outline='#71808a',width=2)
  d.rounded_rectangle((286,22,1634,790),radius=18,fill='#050709');x,y,w,h=300,42,1320,742
  d.polygon([(220,796),(1700,796),(1740,824),(180,824)],fill='#64727d');d.rounded_rectangle((180,816,1740,834),radius=10,fill='#35414a')
  d.polygon([(830,796),(1090,796),(1070,810),(850,810)],fill='#202c35')
 bg=work/(kind+'-frame.png');im.save(bg)
 mask=Image.new('L',(w,h),0);md=ImageDraw.Draw(mask);md.rounded_rectangle((0,0,w-1,h-1),radius=38 if kind=='phone' else 6,fill=255);maskfile=work/(kind+'-mask.png');mask.save(maskfile)
 out=DEST/(src.stem+'-mockup.mp4')
 focus='crop=1178:820:0:1420,pad=1178:2556:0:150:color=0x090e13,' if src.stem=='C8-phone' else ''
 run('ffmpeg','-v','error','-y','-filter_complex_threads','1','-loop','1','-i',bg,'-i',src,'-loop','1','-i',maskfile,'-filter_complex',f'[1:v]{focus}scale={w}:{h}:force_original_aspect_ratio=decrease:flags=lanczos,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x090e13,format=rgba[pixels];[pixels][2:v]alphamerge=shortest=1[s];[0:v][s]overlay={x}:{y}:shortest=1,fps=30[v]','-map','[v]','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',out)
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--only');a=p.parse_args()
 for folder in sorted((BASE/'_raw').iterdir()):
  if not (folder/'clock.json').exists() or a.only and a.only!=folder.name:continue
  src=encode(folder);print(frame(src,'phone' if 'phone' in folder.name else 'laptop'),flush=True)
