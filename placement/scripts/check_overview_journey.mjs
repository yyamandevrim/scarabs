// Additional arrival, compass collision and zoom checks. Arguments: BASE_URL CHROMIUM_BINARY OUTPUT_DIRECTORY.
import {chromium} from 'playwright';
import fs from 'node:fs';import path from 'node:path';import assert from 'node:assert/strict';
const [base,executablePath,out]=process.argv.slice(2),results=[];
const browser=await chromium.launch({headless:true,executablePath,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
for(const phone of [false,true]){
 const page=await browser.newPage({viewport:phone?{width:393,height:852}:{width:1440,height:900}});
 await page.goto(base+'/');await page.waitForSelector('#model-stage.ready');await page.waitForTimeout(1700);
 for(const fields of [false,true]){
  await page.locator('#reset-model').click();await page.waitForTimeout(900);if(fields){await page.locator('#fov-toggle').click();await page.waitForTimeout(900);}
  await page.locator('#model-canvas').focus();for(let i=0;i<12;i++)await page.keyboard.press('+');await page.waitForTimeout(100);
  await page.screenshot({path:path.join(out,(phone?'phone':'desktop')+(fields?'-fov-max-zoom.png':'-max-zoom.png'))});
 }
 await page.locator('#radio-demo').scrollIntoViewIfNeeded();
 await page.evaluate(()=>{
  window.journeys=[];let active=null;
  const root=document.querySelector('#radio-demo');
  document.querySelector('#send-alert').addEventListener('click',()=>{active={camera:document.querySelector('#radio-camera').value,pressed:performance.now()};},{capture:true});
  new MutationObserver(()=>{
   if(!active)return;
   if(root.classList.contains('arrival')&&!active.receivedMs)active.receivedMs=performance.now()-active.pressed;
   if(active.receivedMs&&!root.classList.contains('arrival')){active.settledMs=performance.now()-active.pressed;window.journeys.push(active);active=null;}
  }).observe(root,{attributes:true,attributeFilter:['class']});
 });
 for(const camera of ['centre','right','left']){
  await page.locator('#radio-camera').selectOption(camera);await page.locator('#send-alert').click();
  await page.waitForFunction(n=>window.journeys.length===n,camera==='centre'?1:camera==='right'?2:3);
  // Transform the ray and text to screen coordinates and reject any text intersection.
  const collisions=await page.evaluate(()=>{
   const ray=document.querySelector('#compass-bearing path'),matrix=ray.getScreenCTM();
   const start=new DOMPoint(200,183).matrixTransform(matrix),end=new DOMPoint(200,52).matrixTransform(matrix);
   const hits=[];for(const label of document.querySelectorAll('#demo-compass text')){
    const box=label.getBoundingClientRect();for(let t=0;t<=1;t+=.005){const x=start.x+(end.x-start.x)*t,y=start.y+(end.y-start.y)*t;if(x>box.left&&x<box.right&&y>box.top&&y<box.bottom){hits.push(label.textContent);break;}}
   }return hits;
  });assert.deepEqual(collisions,[]);
 }
 const journeys=await page.evaluate(()=>window.journeys);for(const item of journeys){assert.ok(item.receivedMs>=1200&&item.receivedMs<1600);assert.ok(item.settledMs>=1500&&item.settledMs<=2500);}
 results.push({width:phone?393:1440,journeys});await page.close();
}
await browser.close();fs.writeFileSync(path.join(out,'journey-timing.json'),JSON.stringify(results,null,2));console.log(results);
