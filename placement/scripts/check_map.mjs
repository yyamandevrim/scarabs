/** Copy into a temporary npm directory with Playwright installed; run from repo root.
 * node TEMP/check_map.mjs BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY
 * Includes a separate owned server which is killed/restarted for recovery tests.
 */
import {chromium} from 'playwright';
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
import {spawn} from 'node:child_process';import net from 'node:net';
const [base,executablePath,out]=process.argv.slice(2);if(!out)throw Error('Pass BASE_URL CHROMIUM_BINARY SCREENSHOT_DIRECTORY');
fs.mkdirSync(out,{recursive:true});const language=fs.readFileSync('placement/scripts/check_language.js','utf8');
const browser=await chromium.launch({executablePath,headless:true});const errors=[],external=[],failed=[],checks=[],analyses=[];
const delay=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function ready(p){await p.waitForFunction(()=>document.querySelector('#result-summary').getAttribute('aria-busy')==='false'&&document.querySelectorAll('.headline-value').length===2&&!document.querySelector('#result-state').textContent);await p.waitForSelector('.coverage-map');await p.evaluate(()=>document.fonts.ready);}
async function shot(p,name){checks.push({name,...await p.evaluate(language)});await p.screenshot({path:path.join(out,name+'.png')});}
const contrast=([a,b])=>{const lum=v=>v.match(/[\d.]+/g).slice(0,3).map(n=>+n/255).map(c=>c<=.04045?c/12.92:((c+.055)/1.055)**2.4).reduce((v,c,i)=>v+c*[.2126,.7152,.0722][i],0);return (Math.max(lum(a),lum(b))+.05)/(Math.min(lum(a),lum(b))+.05);};
try{
 for(const phone of [false,true]){
  const p=await browser.newPage({viewport:phone?{width:393,height:852}:{width:1440,height:900},deviceScaleFactor:phone?3:1,isMobile:phone,hasTouch:phone,reducedMotion:'reduce'});
  p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('response',r=>{if(r.status()>=400)failed.push(r.status()+' '+r.url())});p.on('request',r=>{if(!r.url().startsWith(base)&&!r.url().startsWith('data:'))external.push(r.url())});
  await p.addInitScript(()=>localStorage.setItem('language','tr'));await p.goto(base+'/map?lang=tr&language=tr');await ready(p);
  assert.equal(await p.locator('.other-coverage-map').count(),1);assert.equal(await p.locator('.headline-site[aria-pressed="true"]').count(),1);
  assert.equal(await p.locator('.leaflet-control-scale-line').evaluate(e=>getComputedStyle(e).textShadow),'none');
  await shot(p,phone?'phone-default':'desktop-default');
  if(phone){
   assert.ok(await p.locator('#verdict').evaluate(e=>e.getBoundingClientRect().bottom<=innerHeight),'verdict must fit in the first phone screen');
   assert.equal(await p.locator('.sector-label:visible').count(),3);
   assert.equal(await p.locator('.candidate-label:visible').count(),2);
   assert.ok(await p.locator('.shell-nav').isVisible());
  }
  // The number itself is the selection target, not just the small name.
  await p.locator('.headline-site').nth(1).locator('.headline-value').click();assert.equal(await p.locator('.headline-site').nth(1).getAttribute('aria-pressed'),'true');await shot(p,phone?'phone-site-b':'desktop-site-b');
  let slow=true;await p.route('**/api/analyze',async route=>{analyses.push(route.request().postDataJSON());if(slow)await delay(900);await route.continue()});
  await p.selectOption('#height','30');assert.equal(await p.locator('.headline-site.stale').count(),2);assert.match(await p.locator('#verdict').innerText(),/Updating/);
  await shot(p,phone?'phone-updating':'desktop-updating');
  const zoomBefore=await p.evaluate(()=>map.getZoom());await p.locator('.leaflet-control-zoom-in').click();assert.ok(await p.evaluate(()=>map.getZoom())>zoomBefore,'map remains interactive during calculation');
  await ready(p);slow=false;assert.deepEqual(analyses.slice(-2).map(a=>a.height),[30,30]);assert.ok((await p.locator('.headline-sub').allTextContents()).filter(t=>t.includes('30 m')).length===2);await shot(p,phone?'phone-shared-30':'desktop-shared-30');
  await p.selectOption('#resolution','detailed');await ready(p);assert.deepEqual(analyses.slice(-2).map(a=>a.resolution),['detailed','detailed']);await shot(p,phone?'phone-detail':'desktop-detail');
  await p.selectOption('#height','600');await ready(p);await p.selectOption('#resolution','coarse');await ready(p);
  await p.locator('#height-comparison summary').click();await p.waitForFunction(()=>document.querySelectorAll('.height-grid tbody td').length===10&&[...document.querySelectorAll('.height-grid tbody td')].every(e=>!e.textContent.includes('—')));if(phone)await p.locator('#height-comparison').scrollIntoViewIfNeeded();await shot(p,phone?'phone-heights':'desktop-heights');await p.locator('#height-comparison summary').click();
  for(const tab of ['breakdown','data']){await p.locator('#tab-'+tab).click();await shot(p,(phone?'phone-':'desktop-')+tab);}
  await p.locator('#tab-compare').click();await p.locator('.headline-site').first().click();
  if(phone)await p.evaluate(()=>scrollTo(0,0));
  // Fit both centres again after deliberate zooming, then exercise real pointer/touch drawing.
  await p.evaluate(()=>{const b=L.latLngBounds(candidates.map(c=>[c.lat,c.lon])).pad(.08);map.fitBounds(b,{padding:[24,24],maxZoom:11});});
  await p.locator('#draw').click();await p.locator('#draw').click();assert.ok(await p.locator('#finish').isHidden());assert.ok(await p.locator('#draw-help').isHidden());
  await p.locator('#draw').click();assert.ok(await p.locator('#finish').isDisabled());await shot(p,phone?'phone-drawing-start':'desktop-drawing-start');
  for(const selector of ['#draw','#finish'])assert.ok((await p.locator(selector).boundingBox()).height>=44);
  const box=await p.locator('#map').boundingBox(),points=phone?[[.48,.18],[.85,.18],[.85,.58],[.48,.58]]:[[.55,.3],[.8,.3],[.8,.65],[.55,.65]];
  for(const [x,y]of points){if(phone)await p.touchscreen.tap(box.x+box.width*x,box.y+box.height*y);else await p.mouse.click(box.x+box.width*x,box.y+box.height*y);}
  assert.ok(await p.locator('#finish').isEnabled());
  const colors=await p.locator('#finish').evaluate(e=>[getComputedStyle(e).color,getComputedStyle(e).backgroundColor]);assert.ok(contrast(colors)>=7);if(phone)assert.match(await p.locator('#draw-help').innerText(),/^Tap/);
  await shot(p,phone?'phone-drawing-ready':'desktop-drawing-ready');
  await p.locator('#view-compare').evaluate(e=>e.scrollTop=999);await p.locator('#finish').click();await ready(p);
  assert.ok(await p.locator('#draw-help').isHidden());assert.equal(await p.locator('.priority-area').getAttribute('stroke-dasharray'),null);assert.ok(await p.locator('.priority-halo').count());assert.equal(await p.locator('#view-compare').evaluate(e=>e.scrollTop),0);
  await shot(p,phone?'phone-priority-results':'desktop-priority-results');
  assert.ok((await p.locator('#clear-priority').boundingBox()).height>=44);
  if(phone){assert.ok(await p.locator('#headline-figures').evaluate(e=>e.getBoundingClientRect().top>=48));await p.evaluate(()=>scrollTo(0,0));await shot(p,'phone-priority-map');}
  await p.locator('#clear-priority').click();await ready(p);assert.ok(await p.locator('#clear-priority').isHidden());assert.equal(await p.locator('.priority-area').count(),0);await shot(p,phone?'phone-priority-cleared':'desktop-priority-cleared');
  // Refresh a second clean default capture for the unchanged-size Overview exports.
  await p.goto(base+'/map');await ready(p);await p.screenshot({path:path.join(out,phone?'preview-phone.png':'preview-desktop.png')});await p.close();
 }
 assert.deepEqual(errors,[]);assert.deepEqual(external,[]);assert.deepEqual(failed,[]);
 console.log('Normal desktop/phone and drawing checks passed');
 // A dedicated server is the only process killed in this test.
 const port=await new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const port=s.address().port;s.close(()=>resolve(port))})}),recoveryBase='http://127.0.0.1:'+port;
 const log=fs.openSync(path.join(out,'recovery-server.log'),'a');let server;
 async function start(){server=spawn('uv',['run','--offline','--frozen','uvicorn','forest_placement.api:app','--host','127.0.0.1','--port',String(port),'--no-access-log'],{cwd:path.join(process.cwd(),'placement'),detached:true,stdio:['ignore',log,log]});for(let i=0;i<100;i++){try{if((await fetch(recoveryBase+'/api/config')).ok)return}catch{}await delay(100)}throw Error('Owned recovery server failed to start');}
 function kill(){if(server){try{process.kill(-server.pid,'SIGKILL')}catch{}server=null;}}
 const recovery={expectedNetworkErrors:[],configReads:0,pageNavigations:0};
 try{
  await start();const p=await browser.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});let outage=false,refreshFixture=false,interrupt=false;
  p.on('framenavigated',f=>{if(f===p.mainFrame())recovery.pageNavigations++});p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error'){if(outage&&/net::ERR_CONNECTION_REFUSED|net::ERR_FAILED|net::ERR_CONNECTION_RESET/.test(m.text()))recovery.expectedNetworkErrors.push(m.text());else errors.push(m.text());}});
  await p.route('**/api/config',async route=>{recovery.configReads++;try{const response=await route.fetch();const config=await response.json();if(refreshFixture){config.presets.forEach(c=>{c.height=600;c.name='Refreshed '+c.name.split(' · ').pop()});config.data.files={...config.data.files,recoveryFixture:'v2'};}await route.fulfill({response,json:config});}catch{await route.abort('failed');}});
  await p.route('**/api/analyze',async route=>{if(interrupt){interrupt=false;outage=true;kill();await route.continue();}else await route.continue();});
  await p.goto(recoveryBase+'/map');await ready(p);await p.evaluate(()=>window.recoverySession='same-open-page');
  interrupt=true;await p.selectOption('#height','100');await p.waitForSelector('#banner:not([hidden])');await p.screenshot({path:path.join(out,'desktop-reconnecting.png')});
  await delay(2200);refreshFixture=true;await start();await ready(p);
  assert.equal(await p.evaluate(()=>window.recoverySession),'same-open-page');assert.equal(recovery.pageNavigations,1);assert.ok(recovery.configReads>=2);assert.match(await p.locator('.headline-site').first().innerText(),/Refreshed/);assert.equal(await p.inputValue('#height'),'600');assert.ok(await p.locator('#banner').isHidden());
  await p.screenshot({path:path.join(out,'desktop-recovered.png')});recovery.readyWithoutReload=true;recovery.refreshedPresets=true;await p.close();
 }finally{kill();fs.closeSync(log)}
 assert.deepEqual(errors,[]);const results={date:'2026-11-14',checks,normalConsoleErrors:errors,externalRequests:external,failedResponses:failed,recovery,analyses};fs.writeFileSync(path.join(out,'checks.json'),JSON.stringify(results,null,2));console.log(JSON.stringify({states:checks.length,recovery,errors,external,failed}));
}finally{await browser.close()}
