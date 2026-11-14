const {test}=require('node:test');
const assert=require('node:assert/strict');
const {appHarness}=require('./ui_app.cjs');
const settle=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
function transport(h){
 const requests=[];
 h.window.fetch=async(url,options)=>new Promise((resolve,reject)=>{
  const input=JSON.parse(options.body);
  requests.push({input,finish(){resolve({ok:true,json:async()=>({input,resolution_m:120,metrics:{canopy_smoke:{visible_forest_ha:100}}})});},fail(){resolve({ok:false,status:422,json:async()=>({detail:'Choose a land launch point; this cell is mostly water.'})});},network(){reject(new h.window.TypeError('offline'));}});
 });
 return requests;
}
test('edit A then select B before debounce still calculates A and clears its dirty state',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.edit(90);h.api.select(1);h.flush();await settle();
  assert.deepEqual(requests.map(r=>r.input.name),['A']);assert.equal(requests[0].input.heading,90);
  requests[0].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);
 }finally{await h.close();}
});
test('rapid edits to A and B retain both sites in the debounced batch',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.edit(90);h.api.select(1);h.api.edit(130);h.flush();await settle();
  assert.equal(requests[0].input.name,'A');requests[0].finish();await settle();
  assert.equal(requests[1].input.name,'B');assert.equal(requests[1].input.heading,130);
  requests[1].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);
 }finally{await h.close();}
});
test('edits while busy queue both sites and stale response cannot clear the newer edit',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.edit(40);h.flush();await settle();
  h.api.edit(90);h.api.select(1);h.api.edit(130);h.flush();await settle();
  assert.equal(requests.length,1);assert.equal(h.api.state().busy,true);
  requests[0].finish();await settle();
  assert.ok(h.api.state().dirty.includes(0),'old heading response must leave A dirty');
  assert.equal(requests[1].input.name,'A');assert.equal(requests[1].input.heading,90);
  requests[1].finish();await settle();assert.equal(requests[2].input.name,'B');
  requests[2].finish();await settle();assert.deepEqual(h.api.state().dirty,[]);assert.equal(h.api.state().busy,false);
  assert.deepEqual(h.api.state().headings,[90,130]);
 }finally{await h.close();}
});
test('invalid selected controls stay highlighted without blocking valid edits to the other site',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.edit(90);h.api.select(1);h.api.change('lat','');h.flush();await settle();
  assert.equal(requests[0].input.name,'A');requests[0].finish();await settle();
  assert.equal(requests.length,1,'invalid B must not be posted');
  assert.equal(h.window.document.getElementById('lat').getAttribute('aria-invalid'),'true');
  assert.deepEqual(h.api.state().dirty,[1]);
 }finally{await h.close();}
});
test('manual calculation with invalid B preserves the scheduled valid A',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.edit(90);h.api.select(1);h.api.change('lat','');
  h.window.document.getElementById('analyze').click();h.flush();await settle();
  assert.equal(requests[0]?.input.name,'A');requests[0].finish();await settle();
  assert.equal(requests.length,1);assert.deepEqual(h.api.state().dirty,[1]);
  assert.equal(h.window.document.getElementById('lat').getAttribute('aria-invalid'),'true');
 }finally{await h.close();}
});
test('a failed first site does not discard the next valid site or hide its error',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.edit(90);h.api.select(1);h.api.edit(130);h.flush();await settle();
  requests[0].fail();await settle();assert.equal(requests[1]?.input.name,'B');
  requests[1].finish();await settle();assert.deepEqual(h.api.state().dirty,[0]);
  assert.equal(h.api.state().headings[1],130);assert.equal(h.api.state().busy,false);
  assert.match(h.window.document.getElementById('banner-title').textContent,/land launch point/);
  assert.deepEqual(requests.map(r=>r.input.name),['A','B']);
 }finally{await h.close();}
});
test('an invalid edit removes an already queued site while the other site is busy',async()=>{
 const h=await appHarness();try{
  const requests=transport(h);h.api.select(1);h.api.edit(30);h.flush();await settle();
  h.api.select(0);h.api.edit(90);h.flush();await settle();h.api.change('lat','');
  requests[0].finish();await settle();h.flush();await settle();
  assert.equal(requests.length,1);assert.deepEqual(h.api.state().dirty,[0]);
  assert.equal(h.api.state().busy,false);assert.deepEqual(h.api.state().pending,[]);
 }finally{await h.close();}
});
for(const failure of ['fail','network'])test(`a successful pending B preserves A's ${failure} until A succeeds`,async()=>{
 const h=await appHarness();try{
  const requests=transport(h);const initial=h.api.run();await settle();
  requests[0].finish();await settle();requests[1].finish();await initial;
  h.api.edit(90);h.flush();await settle();h.api.select(1);h.api.edit(130);h.flush();await settle();
  requests[2][failure]();await settle();assert.equal(requests[3]?.input.name,'B');
  requests[3].finish();await settle();assert.deepEqual(h.api.state().dirty,[0]);
  assert.equal(h.api.state().headings[1],130);assert.equal(h.api.state().busy,false);
  assert.equal(h.window.document.getElementById('banner').hidden,false);
  assert.match(h.window.document.getElementById('banner-title').textContent,failure==='fail'?/land launch point/:/reach the server/);
  assert.equal(requests.length,4);assert.deepEqual(h.api.state().pending,[]);
  h.api.select(0);h.api.edit(100);h.flush();await settle();
  assert.equal(requests[4]?.input.name,'A');requests[4].finish();await settle();
  assert.deepEqual(h.api.state().dirty,[]);assert.equal(h.window.document.getElementById('banner').hidden,true);
 }finally{await h.close();}
});
