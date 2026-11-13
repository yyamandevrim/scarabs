const {test}=require('node:test');
const assert=require('node:assert/strict');
const d=require('../static/map-display.js');
test('display recolouring preserves masks and unrelated categories, with visible targets above water',()=>{
 const data=new Uint8ClampedArray([0,158,115,195,54,148,199,95,184,120,80,190,0,0,0,0]);
 d.recolor(data,{visible:[0,158,115],water:[54,148,199]},{visible:[90,239,176],water:[70,119,142]});
 assert.deepEqual([...data],[90,239,176,245,70,119,142,38,184,120,80,190,0,0,0,0]);
 const luminance=rgb=>rgb.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((sum,v,i)=>sum+v*[.2126,.7152,.0722][i],0);
 assert.ok((luminance([90,239,176])+.05)/(luminance([70,119,142])+.05)>3,'lightness separates targets from water even without hue');
});
test('safe extent excludes tilted alpha edges for every row inside the returned rectangle',()=>{
 const w=100,h=100,data=new Uint8ClampedArray(w*h*4);
 for(let y=0;y<h;y++)for(let x=3+Math.floor(y/15);x<97-Math.floor(y/20);x++)data[(y*w+x)*4+3]=255;
 const bounds=d.opaqueExtent(data,w,h);
 for(let y=Math.ceil(bounds.top*h);y<=Math.floor(bounds.bottom*h);y++)for(let x=Math.ceil(bounds.left*w);x<=Math.floor(bounds.right*w);x++)assert.equal(data[(y*w+x)*4+3],255);
 assert.throws(()=>d.opaqueExtent(new Uint8ClampedArray(400),10,10),/No opaque/);
});
