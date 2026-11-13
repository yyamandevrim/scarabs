"""Run the live API for 2 presets × 3 heights × 2 resolutions, saving all numbers."""
import argparse,json,sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import httpx
from forest_placement.models import PRESETS
from forest_placement.engine import analyze

def main():
    p=argparse.ArgumentParser();p.add_argument('--url',default='http://127.0.0.1:8787');p.add_argument('--fresh',action='store_true',help='Recompute in-process first, then verify the live API cache');args=p.parse_args()
    output=[]
    with httpx.Client(timeout=180) as client:
        for resolution in ['coarse','detailed']:
            for preset in PRESETS:
                for height in [500,600,700]:
                    c=preset.model_copy(update=dict(height=height,resolution=resolution))
                    if args.fresh:analyze(c,use_cache=False)
                    started=time.perf_counter();response=client.post(args.url+'/api/analyze',json=c.model_dump());response.raise_for_status();r=response.json()
                    output.append(dict(name=c.name,height=height,resolution=resolution,seconds=r['computed_seconds'],api_seconds=round(time.perf_counter()-started,4),metrics=r['metrics'],pairs=r['pair_comparison'],reference=r['reference']['metrics'],heading_sensitivity=r['heading_sensitivity'],id=r['id']))
                    print(c.name,resolution,height,r['computed_seconds'],r['metrics']['canopy_smoke'],flush=True)
    path=Path(__file__).resolve().parents[1]/'benchmark-results.json';path.write_text(json.dumps(output,ensure_ascii=False,indent=2));print('Saved',path)
if __name__=='__main__':main()
