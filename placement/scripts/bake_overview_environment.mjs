/** Offline only: capture/filter the studio into a 32px-face, three-level half-float cube.
 * Copy into the temporary npm toolchain. Arguments: CHROMIUM_BINARY REPO.
 */
import {build} from 'esbuild';
import {chromium} from 'playwright';
import fs from 'node:fs';import path from 'node:path';import {gzipSync} from 'node:zlib';
const [executablePath,root]=process.argv.slice(2);
const source=`import {WebGLRenderer,PMREMGenerator,DataUtils} from 'three';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
const renderer=new WebGLRenderer({antialias:false});renderer.setSize(32,32);
const room=new RoomEnvironment(),generator=new PMREMGenerator(renderer);
// The production generator defaults to 256. This offline bake deliberately targets 32.
generator._setSize=()=>{generator._cubeSize=32;};
const target=generator.fromScene(room,.025,.1,100,{size:32}),gl=renderer.getContext();
const frames=renderer.properties.get(target).__webglFramebuffer,values=[];
for(let level=0;level<3;level++){const size=32>>level;for(let face=0;face<6;face++){
 gl.bindFramebuffer(gl.FRAMEBUFFER,frames[face][level]);const pixels=new Float32Array(size*size*4);gl.readPixels(0,0,size,size,gl.RGBA,gl.FLOAT,pixels);
 for(const value of pixels)values.push(DataUtils.toHalfFloat(Math.round(value*256)/256));
}}
window.baked=values;target.dispose();generator.dispose();room.dispose();renderer.dispose();`;
const bundled=await build({stdin:{contents:source,resolveDir:import.meta.dirname},bundle:true,format:'iife',write:false,minify:true});
const browser=await chromium.launch({executablePath,headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});const page=await browser.newPage();
page.on('pageerror',e=>{throw e;});await page.setContent('<canvas></canvas>');await page.addScriptTag({content:bundled.outputFiles[0].text});await page.waitForFunction(()=>window.baked);
const values=await page.evaluate(()=>window.baked);await browser.close();
const bytes=gzipSync(Buffer.from(new Uint16Array(values).buffer),{level:9});if(bytes.length>25*1024)throw Error('Environment exceeds 25 KiB');
fs.writeFileSync(path.join(root,'placement/static/hardware/studio-cube.bin.gz'),bytes);console.log({halfFloatValues:values.length,bytes:bytes.length});
