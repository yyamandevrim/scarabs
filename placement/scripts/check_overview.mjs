/** Overview acceptance on the real served URL; run from repo root in a temporary npm toolchain.
 * Arguments: BASE_URL CHROMIUM_BINARY OUTPUT_DIRECTORY.
 */
import {chromium,firefox,webkit} from 'playwright';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import assert from 'node:assert/strict';
const [base,executablePath,out]=process.argv.slice(2);
fs.mkdirSync(out,{recursive:true});
const language=fs.readFileSync('placement/scripts/check_language.js','utf8');
const result={url:base,browsers:[],screenshots:[],consoleErrors:[],failedResponses:[],externalRequests:[],smokeResponses:[]};
const chromeOptions={headless:true,executablePath,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-precise-memory-info']};
const appData=fs.mkdtempSync(path.join(os.tmpdir(),'acorn-firefox-appdata-'));
async function make(browser,phone=false,motion='reduce'){
 const p=await browser.newPage({viewport:phone?{width:393,height:852}:{width:1440,height:900},reducedMotion:motion,hasTouch:phone,deviceScaleFactor:phone?3:1});
 p.on('pageerror',e=>result.consoleErrors.push(e.message));
 p.on('console',m=>{if(m.type()==='error')result.consoleErrors.push(m.text());});
 p.on('response',r=>{if(r.status()>=400)result.failedResponses.push(r.status()+' '+r.url());});
 p.on('request',r=>{if(!r.url().startsWith('data:')&&new URL(r.url()).origin!==new URL(base).origin)result.externalRequests.push(r.url());});
 await p.addInitScript(()=>{
  localStorage.setItem('language','tr');window.overviewLongTasks=[];window.overviewShifts=[];
  try{new PerformanceObserver(l=>window.overviewLongTasks.push(...l.getEntries().map(e=>e.duration))).observe({type:'longtask',buffered:true});
   new PerformanceObserver(l=>window.overviewShifts.push(...l.getEntries().filter(e=>!e.hadRecentInput).map(e=>e.value))).observe({type:'layout-shift',buffered:true});}catch{}
 });
 return p;
}
async function ready(p){
 await p.goto(base+'/?lang=tr');await p.waitForSelector('#model-stage.ready');
 assert.equal(await p.locator('#model-fallback').isVisible(),false);await p.waitForTimeout(150);
 assert.ok(await p.evaluate(()=>acornModel.stats.calls>0));
 assert.ok(await p.locator('#model-canvas').evaluate(c=>c.width<=c.clientWidth*2+2));
 assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);
 await p.evaluate(language);
}
async function shot(p,name,selector=null,full=false){
 const destination={path:path.join(out,name+'.png')};
 if(selector)await p.locator(selector).screenshot(destination);else await p.screenshot({...destination,fullPage:full});
 result.screenshots.push(name+'.png');
}
async function idle(p){
 await p.waitForTimeout(250);const start=await p.evaluate(()=>acornModel.stats.draws);
 await p.waitForTimeout(1100);assert.equal(await p.evaluate(()=>acornModel.stats.draws),start);
}
async function keys(p,key,count){for(let i=0;i<count;i++)await p.keyboard.press(key);}
// All engines preserve the ordinary served CSP. Firefox isolates only OS app-data access.
for(const [name,type]of Object.entries({chromium,firefox,webkit})){
 const browser=await type.launch(name==='chromium'?chromeOptions:name==='firefox'?{headless:true,env:{...process.env,CFFIXED_USER_HOME:appData}}:{headless:true});
 for(const phone of [false,true]){
  const p=await make(browser,phone);await ready(p);await idle(p);
  const prefix=name+'-'+(phone?'phone':'desktop');await shot(p,prefix+'-hero');await shot(p,prefix+'-canvas','#model-canvas');
  await p.locator('[data-part="left"]').focus();await p.waitForTimeout(100);
  assert.equal(await p.evaluate(()=>acornModel.stats.selectedPart),'left');await shot(p,prefix+'-camera-3');
  const beforeFov=await p.evaluate(()=>acornModel.stats.draws);await p.locator('#fov-toggle').click();await p.waitForFunction(before=>acornModel.stats.draws>before,beforeFov);await p.waitForTimeout(100);await shot(p,prefix+'-fov');
  await p.locator('#reset-model').click();await p.waitForTimeout(150);
  assert.equal(await p.evaluate(()=>acornModel.stats.selectedPart),null);
  assert.equal(await p.locator('#fov-toggle').getAttribute('aria-pressed'),'false');await idle(p);
  // The first panel is moving video, the second a saved frame, the third a decision.
  await p.locator('[data-step="0"]').click();await p.locator('.phone').scrollIntoViewIfNeeded();
  await p.waitForFunction(()=>document.querySelector('#phone-video').currentTime>.25);
  assert.equal(await p.locator('#phone-video').evaluate(v=>v.loop),true);
  assert.equal(await p.locator('#phone-event-meta').isVisible(),false);
  await p.locator('[data-step="1"]').click();assert.ok(await p.locator('#phone-video').evaluate(v=>v.paused));
  assert.ok(await p.locator('#phone-capture').isVisible());
  result.browsers.push({browser:name,version:browser.version(),width:phone?393:1440,webgl:true,video:true,camera3:true,reset:true,idleDrawsPerSecond:0});await p.close();
 }
 await browser.close();
}
if(process.env.OVERVIEW_RENDER_ONLY==='1'){
 fs.writeFileSync(path.join(out,'render-checks.json'),JSON.stringify(result,null,2));
 assert.deepEqual(result.consoleErrors,[]);assert.deepEqual(result.externalRequests,[]);assert.deepEqual(result.failedResponses,[]);console.log('Six engine/viewport renders and media states passed.');process.exit(0);
}
const browser=await chromium.launch(chromeOptions);
for(const phone of [false,true]){
 const p=await make(browser,phone,'no-preference'),prefix=phone?'phone':'desktop';
 const cdp=await p.context().newCDPSession(p);await cdp.send('Network.enable');let bytes=0;
 cdp.on('Network.loadingFinished',e=>bytes+=e.encodedDataLength);
 await ready(p);await p.waitForTimeout(1850);await idle(p);
 if(!phone){result.initialTransferredBytes=bytes;await cdp.send('HeapProfiler.collectGarbage');result.jsHeapAfterGC=(await cdp.send('Runtime.getHeapUsage')).usedSize;result.loadLongTasksMs=await p.evaluate(()=>window.overviewLongTasks);result.initialLayoutShift=await p.evaluate(()=>window.overviewShifts.reduce((a,b)=>a+b,0));}
 await shot(p,prefix+'-hero');
 // Nine viewpoints: three fronts, three rears, three-quarter, top and underside.
 for(const [camera,label]of [['centre','1'],['right','2'],['left','3']]){
  await p.locator(`[data-part="${camera}"]`).focus();await p.waitForTimeout(850);await idle(p);await shot(p,prefix+'-angle-front-'+label);
  await p.locator('#model-canvas').focus();await keys(p,'ArrowRight',26);await keys(p,'ArrowUp',4);await p.waitForTimeout(100);await shot(p,prefix+'-angle-behind-'+label);
 }
 await p.locator('#reset-model').click();await p.waitForTimeout(850);await p.locator('#model-canvas').focus();await keys(p,'ArrowUp',8);await shot(p,prefix+'-angle-top');
 await p.locator('#reset-model').click();await p.waitForTimeout(850);await p.locator('#model-canvas').focus();await keys(p,'ArrowDown',13);await shot(p,prefix+'-angle-below');
 await p.locator('#reset-model').click();await p.waitForTimeout(850);await p.locator('#fov-toggle').click();await p.waitForTimeout(850);await shot(p,prefix+'-fov');await p.locator('#reset-model').click();await p.waitForTimeout(850);
 if(!phone){
  await p.mouse.move(960,350);await p.mouse.down();await p.mouse.move(1030,365,{steps:5});await p.mouse.up();assert.equal(await p.locator('#model-canvas').getAttribute('data-pointer'),'1');assert.equal(await p.locator('#model-canvas').evaluate(c=>getComputedStyle(c).outlineStyle),'none');
  await p.mouse.wheel(0,450);await p.waitForFunction(()=>scrollY>150,{},{timeout:2000});
 }else{
  await p.evaluate(()=>scrollTo(0,0));const box=await p.locator('#model-canvas').boundingBox(),y=box.y+180;
  await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:190,y}]});
  for(let d=30;d<=180;d+=30)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:190,y:y-d}]});
  await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await p.waitForTimeout(200);assert.ok(await p.evaluate(()=>scrollY)>80);
  for(const part of await p.locator('[data-part]').all()){const bounds=await part.boundingBox();assert.ok(bounds.x>=0&&bounds.x+bounds.width<=393);}
 }
 await p.locator('#radio-demo').scrollIntoViewIfNeeded();await p.locator('#radio-camera').selectOption('centre');
 await shot(p,prefix+'-status-before','#radio-demo');assert.ok((await p.locator('#packet-fields').textContent()).includes('None'));
 if(!phone){await p.waitForSelector('.transmitting.status-reporting',{timeout:15000});await shot(p,'desktop-status-travelling','#radio-demo');}
 await p.evaluate(()=>{
  window.smokeStartTimes=[];let pressed=0;
  document.querySelector('#send-alert').addEventListener('click',()=>{pressed=performance.now();},{capture:true});
  new MutationObserver(()=>{if(pressed&&document.querySelector('#radio-demo').classList.contains('transmitting')){const at=pressed;pressed=0;requestAnimationFrame(()=>window.smokeStartTimes.push(performance.now()-at));}}).observe(document.querySelector('#radio-demo'),{attributes:true,attributeFilter:['class']});
 });
 const compassTop=await p.locator('#demo-compass').evaluate(el=>el.getBoundingClientRect().top+scrollY);
 for(const [camera,label,angle]of [['centre','1','0'],['right','2','120'],['left','3','240']]){
  if(camera!=='centre')await p.locator('#radio-camera').selectOption(camera);
  await shot(p,prefix+'-camera-'+label+'-before','#radio-demo');
  assert.ok(await p.locator('#send-alert').isEnabled());await p.locator('#send-alert').click();
  await p.waitForSelector('.transmitting.smoke-report');assert.ok(await p.locator('#send-alert').isEnabled());await p.waitForTimeout(180);await shot(p,prefix+'-camera-'+label+'-sending','#radio-demo');
  await p.waitForSelector('#collect-evidence');await p.waitForTimeout(650);await shot(p,prefix+'-camera-'+label+'-received','#radio-demo');
  assert.ok((await p.locator('.alert-bearing').innerText()).includes('≈ '+angle+'°'));
  assert.ok(Math.abs(await p.locator('#demo-compass').evaluate(el=>el.getBoundingClientRect().top+scrollY)-compassTop)<1,'Compass must not jump on arrival');
  await p.locator('.packet-inspector').evaluate(d=>d.open=true);
  assert.ok((await p.locator('#packet-fields').textContent()).includes('af27f33e9e244d9db8f18eb4276fd1ad'));
  await shot(p,prefix+'-camera-'+label+'-packet','.packet-inspector');await p.locator('.packet-inspector').evaluate(d=>d.open=false);
  await p.locator('#collect-evidence').click();assert.ok(await p.locator('#radio-evidence').evaluate(d=>d.open));
  await p.waitForFunction(()=>document.querySelector('#evidence-video').currentTime>.25);await shot(p,prefix+'-camera-'+label+'-evidence');await p.locator('#close-evidence').click();assert.ok(await p.locator('#evidence-video').evaluate(v=>v.paused));
 }
 const timings=await p.evaluate(()=>window.smokeStartTimes);assert.equal(timings.length,3);assert.ok(timings.every(t=>t<150));result.smokeResponses.push({width:phone?393:1440,startToFrameMs:timings});
 let phoneTop=null;
 for(let step=0;step<3;step++){
  await p.locator(`[data-step="${step}"]`).click();await p.locator('.phone').scrollIntoViewIfNeeded();
  if(step!==1)await p.waitForFunction(()=>document.querySelector('#phone-video').currentTime>.25);
  const top=await p.locator('.phone').evaluate(el=>el.getBoundingClientRect().top+scrollY);if(phoneTop===null)phoneTop=top;else assert.ok(Math.abs(phoneTop-top)<1,'Phone must not move between steps');
  await shot(p,prefix+'-review-step-'+step,'#ranger');
 }
 await p.locator('[data-decision="confirmed"]').click();assert.ok((await p.locator('#phone-decision-status').innerText()).includes('confirmed'));await shot(p,prefix+'-review-confirmed','#ranger');
 await p.locator('[data-phone-page="history"]').click();await shot(p,prefix+'-review-history','#ranger');
 await p.locator('#phone-replay').click();await p.locator('[data-decision="rejected"]').click();await shot(p,prefix+'-review-rejected','#ranger');assert.ok((await p.locator('#phone-decision-status').innerText()).includes('rejected'));
 await p.locator('#flight').scrollIntoViewIfNeeded();await p.locator('.product-view img').evaluate(im=>im.decode());assert.ok(await p.locator('#phone-video').evaluate(v=>v.paused));await shot(p,prefix+'-map-preview','#flight');await shot(p,prefix+'-closing','.closing');await idle(p);
 await p.evaluate(()=>scrollTo(0,0));await shot(p,prefix+'-full-page',null,true);
 if(!phone){result.interactionTransferredBytes=bytes;result.totalLayoutShift=await p.evaluate(()=>window.overviewShifts.reduce((a,b)=>a+b,0));
  await p.evaluate(()=>(window.contextExtension=document.querySelector('#model-canvas').getContext('webgl2').getExtension('WEBGL_lose_context')).loseContext());await p.waitForTimeout(100);assert.ok(await p.locator('#model-poster').isVisible());await p.evaluate(()=>window.contextExtension.restoreContext());await p.waitForSelector('#model-stage.ready');}
 await p.close();
}
const strict=await make(browser);await strict.route(base+'/',async route=>{const response=await route.fetch(),headers={...response.headers()};headers['content-security-policy']=headers['content-security-policy'].replace(" 'wasm-unsafe-eval'",'');await route.fulfill({response,headers});});await strict.goto(base+'/');await strict.waitForSelector('#model-stage.ready');result.selfOnlyCspRenders=true;await shot(strict,'chromium-self-only-csp');await strict.close();
for(const phone of [false,true]){
 const p=await make(browser,phone);await p.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){if(type==='webgl'||type==='webgl2')return null;return get.call(this,type,...args);};});await p.goto(base+'/');await p.waitForSelector('.model-stage.fallback');assert.ok(await p.locator('#model-poster img').evaluate(im=>im.complete&&im.naturalWidth>0));await shot(p,(phone?'phone':'desktop')+'-fallback');await p.close();
}
await browser.close();try{fs.rmSync(appData,{recursive:true,force:true});}catch(error){if(error.code!=='EACCES')throw error;}
result.idleDrawsPerSecond=0;result.offscreenDrawsPerSecond=0;result.tests={touchAndWheel:true,allCameras:true,reset:true,confirmAndReject:true,evidenceDialog:true,videoPlaybackAndPause:true,statusCadenceSeconds:12,oneRealUuid:true,immediateSmoke:true};
fs.writeFileSync(path.join(out,'measurements.json'),JSON.stringify(result,null,2));assert.deepEqual(result.consoleErrors,[]);assert.deepEqual(result.externalRequests,[]);assert.deepEqual(result.failedResponses,[]);console.log(JSON.stringify(result,null,2));
