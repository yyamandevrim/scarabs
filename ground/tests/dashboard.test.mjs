import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {Window} from '../../station/node_modules/happy-dom/lib/index.js';
const staticDir=new URL('../ground/static/',import.meta.url);
const read=name=>readFileSync(new URL(name,staticDir),'utf8');
const flush=async()=>{for(let i=0;i<5;i++)await new Promise(resolve=>setImmediate(resolve));};
async function dashboard(){
 const w=new Window({url:'http://127.0.0.1/',settings:{disableCSSFileLoading:true,disableJavaScriptFileLoading:true,enableImageFileLoading:false}});
 let tick;w.setInterval=fn=>{tick=fn;return 1;};
 w.HTMLCanvasElement.prototype.getContext=()=>({scale(){}});
 const alert=(id,kind='smoke')=>({station:1,event_id:id,kind,timestamp:1700000000,bearing_cd:29264,camera:0,confidence:54,width:60,height:90,decision:'pending'});
 const saved={station:1,event_id:'b'.repeat(32),files:['b'.repeat(32)+'.jpg','b'.repeat(32)+'.webm']};
 const state={stations:[{id:1,state:'holding',age:20,packets:1,missed:0,last_size:42,airtime:.534,remaining:35,contact_after:64,next_contact_in:44}],alerts:[alert('a'.repeat(32)),alert('b'.repeat(32)),alert('c'.repeat(32),'flame_sensor')],local_evidence:[saved],transport:'LoRa link (simulated transport)'};
 const requests=[];
 w.fetch=async(url,init)=>{requests.push(url);return {ok:true,json:async()=>url==='/api/state'?state:url==='/api/demo'?{enabled:init?JSON.parse(init.body).enabled:false}:url==='/api/demo/status'?{cameras:[]}:saved};};
 w.document.write(read('index.html'));
 if(existsSync(new URL('presentation.js',staticDir)))w.eval(read('presentation.js'));
 w.eval(read('app.js'));
 await flush();return {w,$:s=>w.document.querySelector(s),requests,state,poll:async()=>{await tick();await flush();}};
}
test('bearings use whole approximate degrees and Turkish transport/confidence are localized',async()=>{
 const p=await dashboard();
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
 assert.equal(p.w.document.querySelectorAll('img,video').length,0);
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
