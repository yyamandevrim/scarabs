/** Overview acceptance against the real served URL.
 * Run from the repo root; copy into a temporary npm toolchain.
 * node check_overview.mjs BASE_URL CHROMIUM_BINARY OUTPUT_DIRECTORY
 */
import {chromium,firefox,webkit} from 'playwright';
import fs from 'node:fs';import path from 'node:path';import os from 'node:os';import assert from 'node:assert/strict';
const [base,executablePath,out]=process.argv.slice(2);if(!out)throw Error('Pass URL, Chromium binary, output directory');
fs.mkdirSync(out,{recursive:true});const language=fs.readFileSync('placement/scripts/check_language.js','utf8');
const result={url:base,browsers:[],screenshots:[],consoleErrors:[],failedResponses:[],externalRequests:[]};
const chromeOptions={headless:true,executablePath,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader','--enable-precise-memory-info']};
const appData=fs.mkdtempSync(path.join(os.tmpdir(),'acorn-firefox-appdata-'));
async function make(browser,phone=false,motion='reduce'){
 const p=await browser.newPage({viewport:phone?{width:393,height:852}:{width:1440,height:900},reducedMotion:motion,hasTouch:phone,deviceScaleFactor:phone?3:1});
 p.on('pageerror',e=>result.consoleErrors.push(e.message));p.on('console',m=>{if(m.type()==='error')result.consoleErrors.push(m.text());});p.on('response',r=>{if(r.status()>=400)result.failedResponses.push(r.status()+' '+r.url());});p.on('request',r=>{if(!r.url().startsWith('data:')&&new URL(r.url()).origin!==new URL(base).origin)result.externalRequests.push(r.url());});
 await p.addInitScript(()=>{localStorage.setItem('language','tr');window.overviewLongTasks=[];try{new PerformanceObserver(list=>{window.overviewLongTasks.push(...list.getEntries().map(e=>e.duration));}).observe({type:'longtask',buffered:true});}catch{}});return p;
}
async function ready(p){await p.goto(base+'/?lang=tr');await p.waitForSelector('#model-stage.ready');assert.equal(await p.locator('#model-fallback').isVisible(),false);await p.waitForTimeout(150);assert.ok(await p.evaluate(()=>acornModel.stats.calls>0));assert.ok(await p.locator('#model-canvas').evaluate(c=>c.width<=c.clientWidth*2+2));assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),false);await p.evaluate(language);}
async function shot(p,name,selector=null,full=false){const destination={path:path.join(out,name+'.png')};if(selector)await p.locator(selector).screenshot(destination);else await p.screenshot({...destination,fullPage:full});result.screenshots.push(name+'.png');}
async function idle(p){await p.waitForTimeout(250);const start=await p.evaluate(()=>acornModel.stats.draws);await p.waitForTimeout(1100);assert.equal(await p.evaluate(()=>acornModel.stats.draws),start);}
// Each browser uses the ordinary served CSP. No bypassCSP context is used.
for(const [name,type]of Object.entries({chromium,firefox,webkit})){
 const browser=await type.launch(name==='chromium'?chromeOptions:name==='firefox'?{headless:true,env:{...process.env,CFFIXED_USER_HOME:appData}}:{headless:true});
 for(const phone of [false,true]){
  const p=await make(browser,phone);await ready(p);await idle(p);const prefix=name+'-'+(phone?'phone':'desktop');await shot(p,prefix+'-hero');await shot(p,prefix+'-canvas','#model-canvas');
  await p.locator('[data-part="left"]').focus();await p.waitForTimeout(100);assert.equal(await p.evaluate(()=>acornModel.stats.selectedPart),'left');await shot(p,prefix+'-camera-3');
  await p.locator('#fov-toggle').click();await p.waitForTimeout(100);await shot(p,prefix+'-fov');await p.locator('#reset-model').click();await p.waitForTimeout(150);assert.equal(await p.evaluate(()=>acornModel.stats.selectedPart),null);assert.equal(await p.locator('#fov-toggle').getAttribute('aria-pressed'),'false');await idle(p);
  result.browsers.push({browser:name,version:browser.version(),width:phone?393:1440,webgl:true,camera3:true,reset:true,idleDrawsPerSecond:0});await p.close();
 }
 await browser.close();
}
const browser=await chromium.launch(chromeOptions);
for(const phone of [false,true]){
 const p=await make(browser,phone,'no-preference'),prefix=phone?'phone':'desktop';const cdp=await p.context().newCDPSession(p);await cdp.send('Network.enable');let bytes=0;cdp.on('Network.loadingFinished',e=>bytes+=e.encodedDataLength);
 await ready(p);await p.waitForTimeout(1200);await idle(p);if(!phone){result.initialTransferredBytes=bytes;await cdp.send('HeapProfiler.collectGarbage');result.jsHeapAfterGC=(await cdp.send('Runtime.getHeapUsage')).usedSize;result.loadLongTasksMs=await p.evaluate(()=>window.overviewLongTasks);}
 for(const camera of ['centre','right','left']){await p.locator(`[data-part="${camera}"]`).focus();await p.waitForTimeout(850);await idle(p);await shot(p,prefix+'-selected-'+camera);}
 await p.locator('#model-canvas').focus();for(let i=0;i<10;i++)await p.keyboard.press('ArrowDown');await p.waitForTimeout(150);await shot(p,prefix+'-from-below');await p.locator('#reset-model').click();await p.waitForTimeout(850);await shot(p,prefix+'-reset');
 if(!phone){await p.mouse.move(960,350);await p.mouse.wheel(0,450);await p.waitForTimeout(200);assert.ok(await p.evaluate(()=>scrollY)>150);}else{await p.evaluate(()=>scrollTo(0,0));const box=await p.locator('#model-canvas').boundingBox();const y=box.y+180;await cdp.send('Input.dispatchTouchEvent',{type:'touchStart',touchPoints:[{x:190,y}]});for(let d=30;d<=180;d+=30)await cdp.send('Input.dispatchTouchEvent',{type:'touchMove',touchPoints:[{x:190,y:y-d}]});await cdp.send('Input.dispatchTouchEvent',{type:'touchEnd',touchPoints:[]});await p.waitForTimeout(200);assert.ok(await p.evaluate(()=>scrollY)>80);}
 await p.locator('#radio-demo').scrollIntoViewIfNeeded();await shot(p,prefix+'-status-before','#radio-demo');assert.ok((await p.locator('#packet-fields').textContent()).includes('None'));
 if(!phone){await p.waitForTimeout(13500);await shot(p,'desktop-status-arrival','#radio-demo');assert.ok((await p.locator('#status-report').innerText()).includes('40 bytes'));}
 for(const [camera,label]of [['left','3'],['centre','1']]){
  // A fresh page starts a fresh local walkthrough and avoids skipping any slot wait.
  await ready(p);await p.locator('#radio-camera').selectOption(camera);await p.locator('#radio-demo').scrollIntoViewIfNeeded();await shot(p,prefix+'-camera-'+label+'-before','#radio-demo');await p.locator('#send-alert').click();await p.waitForSelector('.transmitting.smoke-report');await p.waitForTimeout(180);await shot(p,prefix+'-camera-'+label+'-sending','#radio-demo');await p.waitForSelector('#collect-evidence');await p.waitForTimeout(700);await shot(p,prefix+'-camera-'+label+'-received','#radio-demo');
  assert.ok((await p.locator('.alert-bearing').innerText()).includes(camera==='left'?'240':'0'));await p.locator('.packet-inspector').evaluate(d=>d.open=true);await shot(p,prefix+'-camera-'+label+'-packet','.packet-inspector');await p.locator('.packet-inspector').evaluate(d=>d.open=false);
  await p.locator('#collect-evidence').click();assert.ok(await p.locator('#radio-evidence').evaluate(d=>d.open));await p.waitForFunction(()=>document.querySelector('#evidence-video').currentTime>.25);await shot(p,prefix+'-camera-'+label+'-evidence');await p.locator('#close-evidence').click();assert.ok(await p.locator('#evidence-video').evaluate(v=>v.paused));
 }
 for(let step=0;step<3;step++){await p.locator(`[data-step="${step}"]`).click();await p.locator('.phone').scrollIntoViewIfNeeded();if(step===2)await p.waitForFunction(()=>document.querySelector('#phone-video').currentTime>.25);await shot(p,prefix+'-review-step-'+step,'#ranger');}
 await p.locator('[data-decision="confirmed"]').click();assert.ok((await p.locator('#phone-decision-status').innerText()).includes('confirmed'));await shot(p,prefix+'-review-confirmed','#ranger');await p.locator('#phone-replay').click();await p.locator('[data-decision="rejected"]').click();await shot(p,prefix+'-review-rejected','#ranger');assert.ok((await p.locator('#phone-decision-status').innerText()).includes('rejected'));
 await p.locator('#flight').scrollIntoViewIfNeeded();await p.locator('.product-view img').evaluate(im=>im.decode());assert.ok(await p.locator('#phone-video').evaluate(v=>v.paused));await shot(p,prefix+'-map-preview','#flight');await p.locator('.closing').screenshot({path:path.join(out,prefix+'-closing.png')});result.screenshots.push(prefix+'-closing.png');await idle(p);
 await p.evaluate(()=>scrollTo(0,0));await shot(p,prefix+'-full-page',null,true);if(!phone)result.interactionTransferredBytes=bytes;
 if(!phone){await p.evaluate(()=>(window.contextExtension=document.querySelector('#model-canvas').getContext('webgl2').getExtension('WEBGL_lose_context')).loseContext());await p.waitForTimeout(100);assert.ok(await p.locator('#model-poster').isVisible());await p.evaluate(()=>window.contextExtension.restoreContext());await p.waitForSelector('#model-stage.ready');}
 await p.close();
}
const strict=await make(browser);await strict.route(base+'/',async route=>{const response=await route.fetch();const headers={...response.headers()};headers['content-security-policy']=headers['content-security-policy'].replace(" 'wasm-unsafe-eval'",'');await route.fulfill({response,headers});});await strict.goto(base+'/');await strict.waitForSelector('#model-stage.ready');result.selfOnlyCspRenders=true;await shot(strict,'chromium-self-only-csp');await strict.close();
for(const phone of [false,true]){const p=await make(browser,phone);await p.addInitScript(()=>{const get=HTMLCanvasElement.prototype.getContext;HTMLCanvasElement.prototype.getContext=function(type,...args){if(type==='webgl'||type==='webgl2')return null;return get.call(this,type,...args);};});await p.goto(base+'/');await p.waitForSelector('.model-stage.fallback');assert.ok(await p.locator('#model-poster img').evaluate(im=>im.complete&&im.naturalWidth>0));await shot(p,(phone?'phone':'desktop')+'-fallback');await p.close();}
await browser.close();try{fs.rmSync(appData,{recursive:true,force:true});}catch(error){if(error.code!=='EACCES')throw error;/* macOS protects synthetic user folders; the temporary profile can expire normally. */}
result.idleDrawsPerSecond=0;result.offscreenDrawsPerSecond=0;result.tests={touchAndWheel:true,allCameras:true,reset:true,confirmAndReject:true,evidenceDialog:true,videoPlaybackAndPause:true,statusSlotsSeconds:12};
fs.writeFileSync(path.join(out,'measurements.json'),JSON.stringify(result,null,2));assert.deepEqual(result.consoleErrors,[]);assert.deepEqual(result.externalRequests,[]);assert.deepEqual(result.failedResponses,[]);console.log(JSON.stringify(result,null,2));
