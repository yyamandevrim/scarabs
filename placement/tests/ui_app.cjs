// Real app listeners and request sequencing in an offline DOM; no browser/server.
const fs=require('node:fs');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
async function appHarness(){
 const root=path.resolve(__dirname,'..');
 const {Window}=await import(pathToFileURL(path.resolve(root,'../station/node_modules/happy-dom/lib/index.js')));
 const window=new Window({url:'http://placement.local/map',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true}});
 window.document.write(fs.readFileSync(path.join(root,'static/index.html'),'utf8').replace(/<script[^>]*>[\s\S]*?<\/script>/g,''));
 window.matchMedia=()=>({matches:false});window.structuredClone=structuredClone;
 const timers=new Map();let id=0;
 window.setTimeout=fn=>{timers.set(++id,fn);return id;};window.clearTimeout=i=>timers.delete(i);
 for(const file of ['metrics.js','charts.js'])window.eval(fs.readFileSync(path.join(root,'static',file),'utf8'));
 const source=fs.readFileSync(path.join(root,'static/app.js'),'utf8').replace(/init\(\);\s*$/,'');
 const api=window.eval(source+`
 (()=>{
  const preset={name:'A',lat:60.293,lon:24.557,height:600,heading:20,resolution:'coarse',max_range:12000,smoke_height:50,reference:false,cameras:[{yaw:-70,tilt:10,hfov:80,vfov:50,active:true},{yaw:0,tilt:10,hfov:80,vfov:50,active:true},{yaw:70,tilt:10,hfov:80,vfov:50,active:false}]};
  candidates=[structuredClone(preset),{...structuredClone(preset),name:'B'}];dirty.clear();map={};
  render=()=>renderSummary();revealSite=()=>{};
  showControls();renderSummary();
  return {
   edit(heading){$('heading').value=heading;$('heading').dispatchEvent(new Event('input'));$('heading').dispatchEvent(new Event('change'));},
   change(id,value){$(id).value=value;$(id).dispatchEvent(new Event('change'));},
   select(i){$('headline-figures').querySelectorAll('button')[i].click();},
   state:()=>({dirty:[...dirty],busy,pending:[...pending],headings:results.map(r=>r?.input.heading)}),
   chart(fixture,next){results[selected]=fixture;render=()=>{renderSummary();renderSensitivity();};$('scenario').value=next;$('scenario').dispatchEvent(new Event('change'));},
   notes(fixture){results[selected]=fixture;dataInfo={};renderTable();},
   run:()=>run(true)
  };
 })()`);
 const state=api.state;api.state=()=>JSON.parse(JSON.stringify(state()));
 return {window,api,flush(){const tasks=[...timers.values()];timers.clear();return Promise.all(tasks.map(fn=>fn()));},async close(){await window.happyDOM.close();}};
}
module.exports={appHarness};
