const {test}=require('node:test');
const assert=require('node:assert/strict');
const {appHarness}=require('./ui_app.cjs');
const settle=async()=>{for(let i=0;i<20;i++)await Promise.resolve();};
function transport(h){
 const requests=[],configReads=[];let config=h.api.config(),offline=false;
 h.window.fetch=async(url,options)=>{
  if(offline)throw new h.window.TypeError('offline');
  if(url==='/api/config'){configReads.push(url);return {ok:true,json:async()=>config};}
  return new Promise((resolve,reject)=>{
   const input=JSON.parse(options.body);
   options.signal?.addEventListener('abort',()=>reject(Object.assign(new Error('aborted'),{name:'AbortError'})));
   requests.push({input,finish(){resolve({ok:true,json:async()=>({input,resolution_m:input.resolution==='detailed'?40:120,active_cameras:[0,1,2],camera_breakdown:[],algorithm:'v8',metrics:{canopy_smoke:{visible_forest_ha:input.name==='A'?100:200}}})});},fail(){resolve({ok:false,status:422,json:async()=>({detail:'Choose a land launch point; this cell is mostly water.'})});},network(){reject(new h.window.TypeError('offline'));}});
  });
 };
 return {requests,configReads,setConfig(value){config=value},offline(value){offline=value}};
}
async function initial(h,t){const promise=h.api.run();await settle();t.requests[0].finish();await settle();t.requests[1].finish();await promise;}
function text(h,id){return h.window.document.getElementById(id).textContent;}
test('height and detail are shared and a partial batch never shows an unfair verdict',async()=>{
 const h=await appHarness();try{
  const t=transport(h);await initial(h,t);
  h.api.edit(30);assert.match(text(h,'verdict'),/Updating/);assert.match(text(h,'result-state'),/Updating/);
  h.flush();await settle();assert.equal(t.requests[2].input.height,30);t.requests[2].finish();await settle();
  assert.equal(t.requests[3].input.height,30);assert.match(text(h,'verdict'),/Updating/);
  t.requests[3].finish();await settle();assert.deepEqual(h.api.state().heights,[30,30]);assert.match(text(h,'verdict'),/2×/);
  h.api.change('resolution','detailed');h.flush();await settle();assert.equal(t.requests[4].input.resolution,'detailed');t.requests[4].finish();await settle();assert.equal(t.requests[5].input.resolution,'detailed');t.requests[5].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);
 }finally{await h.close();}
});
test('whole site cards select the edited site and shared settings survive site switching',async()=>{
 const h=await appHarness();try{
  const t=transport(h);h.api.edit(500);h.api.select(1);h.flush();await settle();
  assert.match(text(h,'settings-site'),/Editing B/);assert.equal(text(h,'height-site'),'Both sites');
  t.requests[0].finish();await settle();t.requests[1].finish();await settle();assert.deepEqual(h.api.state().heights,[500,500]);
  const cards=h.window.document.querySelectorAll('button.headline-site');assert.equal(cards.length,2);assert.equal(cards[1].getAttribute('aria-pressed'),'true');assert.equal(cards[1].querySelector('button'),null);
 }finally{await h.close();}
});
test('a superseded response cannot clear the newer shared edit',async()=>{
 const h=await appHarness();try{
  const t=transport(h);h.api.edit(30);h.flush();await settle();h.api.edit(700);h.flush();await settle();
  t.requests[0].finish();await settle();assert.ok(h.api.state().dirty.includes(0));
  t.requests[1].finish();await settle();assert.equal(t.requests[2].input.height,700);t.requests[2].finish();await settle();assert.equal(t.requests[3].input.height,700);t.requests[3].finish();await settle();assert.deepEqual(h.api.state().heights,[700,700]);assert.deepEqual(h.api.state().dirty,[]);
 }finally{await h.close();}
});
test('invalid per-site position does not prevent a queued valid site from completing',async()=>{
 const h=await appHarness();try{
  const t=transport(h);h.api.change('lat','60.31');h.api.select(1);h.api.change('lat','');h.flush();await settle();assert.equal(t.requests[0].input.name,'A');t.requests[0].finish();await settle();assert.equal(t.requests.length,1);assert.deepEqual(h.api.state().dirty,[1]);assert.equal(h.window.document.getElementById('lat').getAttribute('aria-invalid'),'true');
 }finally{await h.close();}
});
test('validation errors remain actionable and a manual retry refreshes config then recovers',async()=>{
 const h=await appHarness();try{
  const t=transport(h);h.api.change('lat','60.31');h.flush();await settle();t.requests[0].fail();await settle();assert.match(text(h,'banner-title'),/land launch point/);assert.deepEqual(h.api.retryDelays(),[]);
  h.window.document.getElementById('retry').click();await settle();assert.ok(t.configReads.length>=2);t.requests[1].finish();await settle();t.requests[2].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);assert.equal(h.window.document.getElementById('banner').hidden,true);
 }finally{await h.close();}
});
test('network recovery backs off, refreshes changed presets and discards stale-model results',async()=>{
 const h=await appHarness();try{
  const t=transport(h);await initial(h,t);h.api.edit(100);h.flush();await settle();t.offline(true);t.requests[2].network();await settle();assert.deepEqual(h.api.retryDelays(),[1000]);
  h.flush(1000);await settle();assert.deepEqual(h.api.retryDelays(),[2000]);h.flush(2000);await settle();assert.deepEqual(h.api.retryDelays(),[4000]);
  const config=h.api.config();config.presets.forEach(c=>{c.name='Updated '+c.name;c.height=600});config.data.files.synthetic='v2';t.setConfig(config);t.offline(false);h.flush(4000);await settle();
  assert.equal(h.api.state().heights[0],null,'stale-model figures must disappear when config changes');assert.equal(t.requests[3].input.name,'Updated A');assert.equal(t.requests[3].input.height,600);t.requests[3].finish();await settle();t.requests[4].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);assert.equal(h.window.document.getElementById('banner').hidden,true);
 }finally{await h.close();}
});
test('an interrupted request times out and a retry needs no reload',async()=>{
 const h=await appHarness();try{
  const t=transport(h);h.api.edit(100);h.flush();await settle();h.flush(15000);await settle();assert.match(text(h,'banner-title'),/Retrying automatically/);assert.equal(h.api.state().busy,false);
  h.flush(1000);await settle();t.requests[1].finish();await settle();t.requests[2].finish();await settle();assert.deepEqual(h.api.state().heights,[100,100]);assert.deepEqual(h.api.state().dirty,[]);
 }finally{await h.close();}
});
test('a changed server schema refreshes presets after 422 and calculates again automatically',async()=>{
 const h=await appHarness();try{
  const t=transport(h);await initial(h,t);const config=h.api.config();config.presets.forEach(c=>c.name='Fresh '+c.name);t.setConfig(config);
  h.api.change('lat','60.31');h.flush();await settle();t.requests[2].fail();await settle();
  assert.equal(t.requests[3].input.name,'Fresh A');assert.match(text(h,'verdict'),/Updating|appears/);t.requests[3].finish();await settle();t.requests[4].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);assert.equal(h.window.document.getElementById('banner').hidden,true);
 }finally{await h.close();}
});
