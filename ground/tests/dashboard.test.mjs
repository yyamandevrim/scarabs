import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {Window} from '../../station/node_modules/happy-dom/lib/index.js';
const staticDir=new URL('../ground/static/',import.meta.url);
const read=name=>readFileSync(new URL(name,staticDir),'utf8');
const flush=async()=>{for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));};
async function dashboard(server={enabled:false}){
 const w=new Window({url:'http://127.0.0.1/',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,enableImageFileLoading:false}});
 let tick;w.setInterval=fn=>{tick=fn;return 1;};
 w.HTMLCanvasElement.prototype.getContext=()=>({scale(){}});
 const alert=(id,kind='smoke')=>({station:1,event_id:id,kind,timestamp:1700000000,bearing_cd:29264,camera:0,confidence:54,width:60,height:90,decision:'pending'});
 const saved={station:1,event_id:'b'.repeat(32),files:['b'.repeat(32)+'.jpg','b'.repeat(32)+'.webm']};
 const state={stations:[{id:1,state:'holding',age:20,packets:1,missed:0,last_size:42,airtime:.534,remaining:35,contact_after:64,next_contact_in:44}],alerts:[alert('a'.repeat(32)),alert('b'.repeat(32)),alert('c'.repeat(32),'flame_sensor')],local_evidence:[saved],transport:'LoRa link (simulated transport)'};
 const requests=[];
 w.fetch=async(url,init)=>{requests.push(url);if(server.handle){const response=await server.handle(url,init);if(response)return response;}if(url==='/api/demo'&&init)server.enabled=JSON.parse(init.body).enabled;return {ok:true,json:async()=>url==='/api/state'?state:url==='/api/demo'?{enabled:server.enabled}:url==='/api/demo/status'?{cameras:[]}:saved};};
 w.document.write(read('index.html'));
 if(existsSync(new URL('presentation.js',staticDir)))w.eval(read('presentation.js'));
 w.eval(read('app.js'));
 await flush();return {w,$:s=>w.document.querySelector(s),requests,state,poll:async()=>{await tick();await flush();}};
}
test('bearings use whole approximate degrees and Turkish transport/confidence are localized',async()=>{
 const p=await dashboard();
 assert.equal(p.w.document.documentElement.lang, 'en');
 assert.equal(p.$('.alert-title').textContent, 'Smoke suspicion');
 assert.match(p.$('.bearing').textContent,/≈ 293°/);
 const collect=[...p.w.document.querySelectorAll('.alert.selected button')].find(b=>b.textContent==='Collect evidence over Wi-Fi');collect.click();await flush();
 p.$('#language').click();await flush();
 assert.match(p.$('#collection-message').textContent,/Kanıt kaydedildi/);
 assert.match(p.$('#transport-label').textContent,/LoRa bağlantısı/);
 assert.match(p.$('.alert-meta').textContent,/%54/);
 assert.match(p.$('#station-state').textContent,/bekleme/);
});
test('saved evidence is visible on its alert and selected on reload; flame offers no direction/media',async()=>{
 const p=await dashboard();
 const saved=p.$('[data-event-id="'+'b'.repeat(32)+'"]');
 assert.ok(saved?.textContent.includes('Evidence saved'));
 assert.ok(saved.classList.contains('selected'));
 const flame=p.$('[data-event-id="'+'c'.repeat(32)+'"]');
 assert.doesNotMatch(flame.textContent,/Show direction|Collect evidence/);
 assert.ok(p.$('img[src="/static/brand/acorn-wordmark-white.svg"]'));
 assert.equal(p.w.document.querySelectorAll('#demo img,#demo video').length,0);
 assert.equal(p.requests.some(url=>url.startsWith('/api/evidence/')||url.startsWith('/api/demo/')),false);
 const view=[...saved.querySelectorAll('button')].find(b=>b.textContent==='View saved evidence · Wi-Fi');view.click();await flush();
 assert.equal(p.$('#demo').hidden,false);
 assert.ok(p.$('#evidence').textContent.includes('b'.repeat(32)));
 assert.ok(p.$('#evidence video').src.endsWith('b'.repeat(32)+'.webm'));
});

test('Wi-Fi demo keeps live camera requests off until the feeds disclosure is opened',async()=>{
 const p=await dashboard();
 const view=[...p.$('.alert.selected').querySelectorAll('button')].find(b=>b.textContent==='View saved evidence · Wi-Fi');
 view.click();await flush();
 assert.equal(p.$('#demo').hidden,false);
 assert.equal(p.requests.includes('/api/demo/status'),false);
 assert.ok(p.$('#evidence video'));
 const feeds=p.$('.wifi-feeds');feeds.open=true;feeds.dispatchEvent(new p.w.Event('toggle'));await flush();
 assert.equal(p.requests.includes('/api/demo/status'),true);
 feeds.open=false;await flush();
 const before=p.requests.filter(url=>url==='/api/demo/status').length;
 await p.poll();
 assert.equal(p.requests.filter(url=>url==='/api/demo/status').length,before);
});

test('selected alert stays first beside its compass and evidence when newer packets arrive',async()=>{
 const p=await dashboard();
 assert.equal(p.$('#alerts').firstElementChild.dataset.eventId,'b'.repeat(32));
 p.state.alerts.unshift({...p.state.alerts[0],event_id:'d'.repeat(32),timestamp:1700000100});
 await p.poll();
 assert.equal(p.$('#alerts').firstElementChild.dataset.eventId,'b'.repeat(32));
 assert.equal(p.$('#alert-count').textContent,'4');
});

const toggle=async(p,enabled)=>{p.$('#demo-toggle').checked=enabled;p.$('#demo-toggle').dispatchEvent(new p.w.Event('change'));await flush();};
const response=value=>({ok:true,json:async()=>value});
const deferred=()=>{let resolve;const promise=new Promise(done=>{resolve=done;});return {promise,resolve};};
function assertOff(p){
 assert.equal(p.$('#demo-toggle').checked,false);
 assert.equal(p.$('#demo').hidden,true);
 assert.equal(p.w.document.querySelectorAll('#demo img,#demo video').length,0);
 assert.equal(p.$('#workspace').classList.contains('with-wifi'),false);
}
test('shared server demo off reaches the other DOM tab on its next poll without another POST',async()=>{
 const server={enabled:false};
 const a=await dashboard(server);await toggle(a,true);const b=await dashboard(server);
 let posts=0;server.handle=async(url,init)=>{if(init?.method==='POST')posts++;};
 await b.poll();
 assert.ok(a.$('#evidence video'));assert.ok(b.$('#evidence video'));
 await toggle(b,false);const before=a.requests.length;
 await a.poll();assertOff(a);assertOff(b);
 assert.deepEqual(a.requests.slice(before).sort(),['/api/demo','/api/state']);
 assert.equal(posts,1);
 // A disclosure opening while off may not fetch station status or frames.
 a.$('.wifi-feeds').open=true;a.$('.wifi-feeds').dispatchEvent(new a.w.Event('toggle'));await flush();
 assert.deepEqual(a.requests.slice(before).sort(),['/api/demo','/api/state']);
});
test('a poll started before an off POST cannot restore old on state',async()=>{
 const server={enabled:false},p=await dashboard(server);await toggle(p,true);
 const oldMode=deferred();let delayed=true;
 server.handle=async(url,init)=>{if(url==='/api/demo'&&!init&&delayed){delayed=false;return oldMode.promise;}};
 const polling=p.poll();await flush();await toggle(p,false);assertOff(p);
 oldMode.resolve(response({enabled:true}));await polling;assertOff(p);
});
test('a poll started during an off POST cannot reopen media after that POST succeeds',async()=>{
 const server={enabled:false},p=await dashboard(server);await toggle(p,true);
 const off=deferred(),state=deferred();
 server.handle=async(url,init)=>{
  if(url==='/api/demo'&&init)return off.promise;
  if(url==='/api/demo')return response({enabled:true});
  if(url==='/api/state')return state.promise;
 };
 await toggle(p,false);const polling=p.poll();await flush();
 server.enabled=false;off.resolve(response({enabled:false}));await flush();assertOff(p);
 const before=p.requests.length;state.resolve(response(p.state));await polling;
 assertOff(p);assert.equal(p.requests.slice(before).some(url=>url.startsWith('/api/evidence/')||url.startsWith('/api/demo/')),false);
});
test('mode poll authentication or state failures clear cached imagery and stop Wi-Fi requests',async()=>{
 for(const failed of ['/api/demo','/api/state']){
  const server={enabled:false},p=await dashboard(server);await toggle(p,true);assert.ok(p.$('#evidence video'));
  server.handle=async url=>url===failed?{ok:false}:undefined;
  await p.poll();assertOff(p);
  const before=p.requests.filter(url=>url.startsWith('/api/evidence/')||url.startsWith('/api/demo/')).length;
  await p.poll();
  assert.equal(p.requests.filter(url=>url.startsWith('/api/evidence/')||url.startsWith('/api/demo/')).length,before);
 }
});
test('slow old evidence cannot reappear after off and on, and failed mode POST stays closed',async()=>{
 const server={enabled:false},p=await dashboard(server),oldEvidence=deferred();let delayed=true;
 server.handle=async(url,init)=>{if(url.startsWith('/api/evidence/')&&!init&&delayed){delayed=false;return oldEvidence.promise;}};
 await toggle(p,true);await toggle(p,false);assertOff(p);
 // A fresh on request while the previous evidence request is outstanding must
 // eventually show current evidence, without letting the old response render.
 await toggle(p,true);
 oldEvidence.resolve(response({files:['stale.webm']}));await flush();
 assert.equal(p.$('#evidence video'),null);
 await p.poll();assert.ok(p.$('#evidence video').src.endsWith('b'.repeat(32)+'.webm'));
 await toggle(p,false);assertOff(p);
 server.handle=async(url,init)=>url==='/api/demo'&&init?{ok:false}:undefined;
 await toggle(p,true);assertOff(p);
});

test('authoritative off hides imagery even while packet-state response is slow',async()=>{
 const server={enabled:false},p=await dashboard(server);await toggle(p,true);
 const slowState=deferred();server.enabled=false;
 server.handle=async url=>url==='/api/state'?slowState.promise:undefined;
 const polling=p.poll();await flush();
 try{assertOff(p);}finally{slowState.resolve(response(p.state));await polling;}
});
test('Wi-Fi status authentication failure clears saved media as well as live frames',async()=>{
 const server={enabled:false},p=await dashboard(server);await toggle(p,true);assert.ok(p.$('#evidence video'));
 server.handle=async url=>url==='/api/demo/status'?{ok:false}:undefined;
 p.$('.wifi-feeds').open=true;p.$('.wifi-feeds').dispatchEvent(new p.w.Event('toggle'));await flush();
 assertOff(p);
});
