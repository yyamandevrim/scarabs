// Supplemental three-engine media controls and final map/header captures.
// Arguments: BASE_URL CHROMIUM_BINARY OUTPUT_DIRECTORY. Run from repo root.
import{chromium,firefox,webkit}from'playwright';import fs from'node:fs';import os from'node:os';import path from'node:path';import assert from'node:assert/strict';
const[base,binary,out]=process.argv.slice(2),extra={screenshots:[],checks:[],errors:[]};
const ff=fs.mkdtempSync(path.join(os.tmpdir(),'acorn-media-ff-'));
for(const[name,type]of Object.entries({chromium,firefox,webkit})){
 const b=await type.launch(name==='chromium'?{executablePath:binary,headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']}:name==='firefox'?{headless:true,env:{...process.env,CFFIXED_USER_HOME:ff}}:{headless:true});
 const p=await b.newPage({viewport:{width:1440,height:900},reducedMotion:'reduce'});p.on('pageerror',e=>extra.errors.push(e.message));p.on('console',m=>{if(m.type()==='error')extra.errors.push(m.text());});await p.goto(base+'/');await p.waitForSelector('#model-stage.ready');
 await p.locator('[data-step="2"]').click();await p.locator('.phone').scrollIntoViewIfNeeded();await p.waitForFunction(()=>document.querySelector('#phone-video').currentTime>.4);await p.locator('[data-video="phone-video"] .clip-play').click();assert.ok(await p.locator('#phone-video').evaluate(v=>v.paused));await p.locator('[data-video="phone-video"] .clip-seek').press('End');await p.waitForFunction(()=>document.querySelector('#phone-video').currentTime>document.querySelector('#phone-video').duration*.8);await p.locator('[data-video="phone-video"] .clip-seek').press('Home');await p.waitForFunction(()=>document.querySelector('#phone-video').currentTime<.2);await p.locator('[data-video="phone-video"] .clip-play').click();await p.waitForFunction(()=>!document.querySelector('#phone-video').paused);extra.checks.push(name+' local player play/pause/seek');
 if(name==='chromium'){
  for(const[width,height,label]of[[1440,900,'desktop'],[393,852,'phone']]){await p.setViewportSize({width,height});await p.goto(base+'/');await p.waitForSelector('#model-stage.ready');await p.locator('#fov-toggle').click();await p.waitForTimeout(150);await p.screenshot({path:path.join(out,label+'-default-fov.png')});extra.screenshots.push(label+'-default-fov.png');}
  await p.setViewportSize({width:1440,height:900});await p.goto(base+'/map?lang=tr&language=tr');await p.waitForFunction(()=>document.body.innerText.includes('Visible forest'));await p.evaluate(fs.readFileSync('placement/scripts/check_language.js','utf8'));await p.screenshot({path:path.join(out,'map-header-English.png')});extra.screenshots.push('map-header-English.png');extra.checks.push('map English header and current presets');
 }
 await b.close();
}
fs.writeFileSync(path.join(out,'extra-checks.json'),JSON.stringify(extra,null,2));assert.deepEqual(extra.errors,[]);console.log(extra);
