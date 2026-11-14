/* Surface finish and the offline-filtered studio. No hardware is added here. */
import {CompressedCubeTexture,RGBAFormat,HalfFloatType,LinearMipmapLinearFilter,LinearFilter,LinearSRGBColorSpace,CanvasTexture,SRGBColorSpace} from 'three';
export async function loadStudio(){
 const response=await fetch('/static/hardware/studio-cube.bin.gz');if(!response.ok)throw Error('Studio asset unavailable');
 const buffer=await new Response(response.body.pipeThrough(new DecompressionStream('gzip'))).arrayBuffer(),values=new Uint16Array(buffer);
 const images=Array.from({length:6},()=>({width:32,height:32,mipmaps:[]}));let offset=0;
 for(const size of [32,16,8])for(const image of images){const count=size*size*4;image.mipmaps.push({width:size,height:size,data:values.subarray(offset,offset+count)});offset+=count;}
 const texture=new CompressedCubeTexture(images,RGBAFormat,HalfFloatType);texture.colorSpace=LinearSRGBColorSpace;texture.minFilter=LinearMipmapLinearFilter;texture.magFilter=LinearFilter;texture.isPMREMTexture=true;texture.needsUpdate=true;return texture;
}
export function podFinish(){
 const colour=document.createElement('canvas'),height=document.createElement('canvas');colour.width=colour.height=height.width=height.height=256;
 const colourContext=colour.getContext('2d'),heightContext=height.getContext('2d'),c=colourContext.createImageData(256,256),h=heightContext.createImageData(256,256);let seed=273;
 for(let y=0;y<256;y++)for(let x=0;x<256;x++){
  const i=(y*256+x)*4,r=Math.hypot(x-127.5,y-127.5)/256;seed=(seed*1664525+1013904223)>>>0;
  const seam=Math.exp(-Math.pow((r-.473)/.0022,2)),grain=seed%7;
  const value=249-grain-seam*28,bevel=Math.max(0,Math.min(1,(.5-r)/.025));
  c.data.set([value,value+1,value,255],i);const v=130+bevel*28-seam*14+grain*.25;h.data.set([v,v,v,255],i);
 }
 colourContext.putImageData(c,0,0);heightContext.putImageData(h,0,0);
 const map=new CanvasTexture(colour),bump=new CanvasTexture(height);map.colorSpace=SRGBColorSpace;return{map,bump};
}
export async function printTexture(){
 const source=new Image();source.src='/static/brand/acorn-wordmark-white.svg';await source.decode();
 const canvas=document.createElement('canvas');canvas.width=512;canvas.height=166;const context=canvas.getContext('2d');context.drawImage(source,0,0,512,166);context.globalCompositeOperation='source-in';context.fillStyle='#394342';context.fillRect(0,0,512,166);
 const texture=new CanvasTexture(canvas);texture.colorSpace=SRGBColorSpace;return texture;
}
export function lensNormal(){
 const canvas=document.createElement('canvas');canvas.width=canvas.height=128;const context=canvas.getContext('2d'),pixels=context.createImageData(128,128);
 for(let y=0;y<128;y++)for(let x=0;x<128;x++){
  const nx=(x/127-.5)*.84,ny=(y/127-.5)*.84,nz=Math.sqrt(Math.max(0,1-nx*nx-ny*ny)),i=(y*128+x)*4;
  pixels.data.set([(nx*.5+.5)*255,(ny*.5+.5)*255,(nz*.5+.5)*255,255],i);
 }
 context.putImageData(pixels,0,0);return new CanvasTexture(canvas);
}
