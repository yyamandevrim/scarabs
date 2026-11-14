// Copy this script into the temporary npm toolchain, then pass the repository root.
import {build} from 'esbuild';
import path from 'node:path';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
const root=path.resolve(process.argv[2]||'.');
const outfile=path.join(root,'placement/static/vendor/landing-3d.js');
await build({entryPoints:[path.join(root,'placement/static/landing-model.js')],bundle:true,format:'esm',minify:true,target:['es2020'],outfile,nodePaths:[path.join(import.meta.dirname,'node_modules')],legalComments:'eof'});
console.log(JSON.stringify({bytes:fs.statSync(outfile).size,gzip:gzipSync(fs.readFileSync(outfile)).length}));
