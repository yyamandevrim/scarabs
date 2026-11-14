// Temporary Playwright toolchain. Arguments: served URL, Chromium binary, repository root.
import {chromium} from 'playwright';
import fs from 'node:fs';import os from 'node:os';import path from 'node:path';import {spawnSync} from 'node:child_process';
const [base,executablePath,repo]=process.argv.slice(2);
const temporary=fs.mkdtempSync(path.join(os.tmpdir(),'acorn-posters-'));
const browser=await chromium.launch({executablePath,headless:true,args:['--use-angle=swiftshader','--enable-unsafe-swiftshader']});
for(const phone of [false,true]){
 const page=await browser.newPage({viewport:phone?{width:393,height:852}:{width:1440,height:900},reducedMotion:'reduce',deviceScaleFactor:2});
 await page.goto(base);await page.waitForSelector('#model-stage.ready');
 await page.addStyleTag({content:'.part-labels,.leaders,.hero-copy,.hero-rail{visibility:hidden!important}html,body,.hero{background:transparent!important}'});
 await page.locator('#model-canvas').screenshot({omitBackground:true,path:path.join(temporary,phone?'phone.png':'desktop.png')});await page.close();
}
await browser.close();
const python=`from PIL import Image
from pathlib import Path
for name,suffix in [('desktop',''),('phone','-phone')]:
 im=Image.open(Path(${JSON.stringify(temporary)})/(name+'.png'))
 im.save(Path(${JSON.stringify(repo)})/('placement/static/hardware/acorn-poster'+suffix+'.webp'),quality=87,method=6)
 if name=='desktop':
  node=im.crop((int(im.width*.46),int(im.height*.05),int(im.width*.94),int(im.height*.85)))
  node.thumbnail((240,240))
  node.save(Path(${JSON.stringify(repo)})/'placement/static/hardware/acorn-node.webp',quality=88,method=6)
 print(name,im.size)
`;
const converted=spawnSync('uv',['run','--offline','--frozen','--project',path.join(repo,'placement'),'python','-c',python],{stdio:'inherit'});
fs.rmSync(temporary,{recursive:true});if(converted.status)process.exit(converted.status);
