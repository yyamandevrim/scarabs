'use strict';
// Presentation only: category masks, underlying geometry and numeric results stay intact.
(function(root){
 function opaqueExtent(data,width,height){
  const top=Math.ceil(height*.06),bottom=Math.floor(height*.94);let left=0,right=width-1;
  for(let y=top;y<=bottom;y++){
   let a=0,b=width-1;while(a<width&&data[(y*width+a)*4+3]<250)a++;while(b>=0&&data[(y*width+b)*4+3]<250)b--;
   left=Math.max(left,a);right=Math.min(right,b);
  }
  if(left>=right)throw Error('No opaque map interior');
  return {left:(left+2)/width,right:(right-2)/width,top:top/height,bottom:bottom/height};
 }
 function recolor(data,source,display){
  const entries=Object.keys(source).map(key=>({key,rgb:source[key],out:display[key]}));
  for(let i=0;i<data.length;i+=4){if(!data[i+3])continue;const match=entries.find(e=>e.rgb.every((v,k)=>data[i+k]===v));if(!match)continue;
   for(let k=0;k<3;k++)data[i+k]=match.out[k];
   // Water is context. Forest targets are opaque enough to remain distinct from the base.
   if(match.key==='water')data[i+3]=38;else if(match.key==='visible')data[i+3]=245;
  }
  return data;
 }
 const cache=new Map();
 function load(url){return new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=reject;img.src=url;});}
 async function extent(url){const img=await load(url),canvas=document.createElement('canvas');canvas.width=img.width;canvas.height=img.height;const ctx=canvas.getContext('2d',{willReadFrequently:true});ctx.drawImage(img,0,0);return opaqueExtent(ctx.getImageData(0,0,img.width,img.height).data,img.width,img.height);}
 function image(url,source,display){
  if(cache.has(url))return cache.get(url);
  const pending=load(url).then(img=>{const canvas=document.createElement('canvas');canvas.width=img.width;canvas.height=img.height;const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0);const pixels=ctx.getImageData(0,0,img.width,img.height);recolor(pixels.data,source,display);ctx.putImageData(pixels,0,0);return canvas.toDataURL('image/png');}).catch(error=>{cache.delete(url);throw error;});
  cache.set(url,pending);if(cache.size>8)cache.delete(cache.keys().next().value);return pending;
 }
 const api={opaqueExtent,recolor,extent,image};root.MapDisplay=api;if(typeof module!=='undefined')module.exports=api;
})(globalThis);
