import {demo,cameraNames,fixture,eventTime} from './radio-packet.js';
const $=id=>document.getElementById(id);
const facts={centre:['Camera 1','The forward pod defines the module’s reference direction. Its lens faces you when selected.'],right:['Camera 2','This pod faces the next side of the triangular housing, continuing the view around the module.'],left:['Camera 3','The third pod completes the view around the housing. Select it to look directly into its lens.'],eye:['Tether attachment','The bridle and tether pass through the paired openings in the top and bottom plates.'],housing:['Housing','The housing carries the on-device computer and the three camera mounts.']};
let viewer=null,fov=false;
function detail(id){const [title,body]=id?facts[id]:['Look around the module','Select a camera to face its lens. The three pods look outward around the housing.'];$('part-detail').replaceChildren(Object.assign(document.createElement('h2'),{textContent:title}),Object.assign(document.createElement('p'),{textContent:body}));document.querySelectorAll('[data-part]').forEach(b=>b.setAttribute('aria-current',String(b.dataset.part===id)));}
function selectPart(id){detail(id);viewer?.highlight(id);}
document.querySelectorAll('[data-part]').forEach(button=>{button.addEventListener('click',()=>selectPart(button.dataset.part));button.addEventListener('focus',()=>selectPart(button.dataset.part));});
$('fov-toggle').addEventListener('click',()=>{fov=!fov;$('fov-toggle').textContent=fov?'Hide fields of view':'Show fields of view';$('fov-toggle').setAttribute('aria-pressed',String(fov));viewer?.toggleFov(fov);});
$('reset-model').addEventListener('click',()=>{fov=false;$('fov-toggle').setAttribute('aria-pressed','false');$('fov-toggle').textContent='Show fields of view';detail(null);viewer?.reset();});
if(matchMedia('(pointer:coarse)').matches)$('drag-hint').textContent='Drag to turn · pinch to zoom';
const fail=()=>{$('model-stage').classList.remove('ready');$('model-stage').classList.add('fallback');$('model-canvas').tabIndex=-1;$('model-fallback').hidden=false;$('part-detail').querySelector('h2').textContent='Module guide';$('part-detail').querySelector('p').textContent='Select a part to read about its role.';};
requestAnimationFrame(()=>requestAnimationFrame(()=>{import('/static/vendor/landing-3d.js').then(m=>m.mountModel({selectPart})).then(api=>{viewer=api;for(const id of ['fov-toggle','reset-model'])$(id).disabled=false;}).catch(fail);}));
let step=0,videoVisible=false;
const video=$('phone-video');
const explanations=['Look through the camera, then open its smoke suspicion.','A saved frame belongs to this record. Open its clip before deciding.','Review the clip, then confirm or reject. The decision stays with the record.'];
function phone(){
 $('phone-camera-name').textContent=cameraNames[demo.camera];
 $('phone-title').textContent=['Camera view','Smoke suspicion','Review evidence'][step];
 $('phone-event-meta').textContent=eventTime()+' · '+Math.round(fixture.score*100)+'% model score';
 $('phone-capture').hidden=step===2;$('phone-image-action').hidden=step===2;video.hidden=step!==2;document.querySelector('[data-video="phone-video"]').hidden=step!==2;
 $('phone-next').hidden=step===2;$('phone-next').textContent=step===0?'Open record':'Watch evidence';
 $('phone-decisions').hidden=step!==2||!!demo.decision;
 $('phone-record-state').textContent=demo.decision?'Decision saved':step===0?'Smoke suspicion':'Awaiting your decision';
 $('phone-record-copy').textContent=demo.decision?'Your review stays with this suspicion.':step===0?'The camera has flagged a view for you to inspect.':'Watch the evidence before you choose.';
 $('phone-decision-status').textContent=demo.decision?(demo.decision==='confirmed'?'Suspicion confirmed.':'Suspicion rejected.') : '';
 $('phone-replay').hidden=!demo.decision;
 $('step-explanation').textContent=explanations[step];
 document.querySelectorAll('[data-step]').forEach(button=>button.setAttribute('aria-pressed',String(Number(button.dataset.step)===step)));
 if(step!==2||document.hidden||!videoVisible)video.pause();
}
function setStep(value){step=value;if(step===1)video.load();phone();const content=document.querySelector('.phone-content');content.classList.remove('changing');void content.offsetWidth;content.classList.add('changing');if(step===2&&videoVisible)video.play().catch(()=>{});if(innerWidth<=760)document.querySelector('.phone').scrollIntoView({block:'center',behavior:matchMedia('(prefers-reduced-motion:reduce)').matches?'instant':'smooth'});}
document.querySelectorAll('[data-step]').forEach(button=>button.addEventListener('click',()=>setStep(Number(button.dataset.step))));
$('phone-next').addEventListener('click',()=>setStep(Math.min(2,step+1)));
$('phone-image-action').addEventListener('click',()=>setStep(Math.min(2,step+1)));
$('phone-image-action').addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setStep(Math.min(2,step+1));}});
document.querySelectorAll('[data-decision]').forEach(button=>button.addEventListener('click',()=>{video.pause();demo.decide(button.dataset.decision);}));
$('phone-replay').addEventListener('click',()=>{demo.decide(null);video.currentTime=0;phone();});
demo.addEventListener('change',phone);
new IntersectionObserver(([entry])=>{videoVisible=entry.isIntersecting;if(videoVisible&&step===2&&!demo.decision&&!document.hidden)video.play().catch(()=>{});else video.pause();},{threshold:.2}).observe(video);
document.addEventListener('visibilitychange',()=>{if(document.hidden)video.pause();});
phone();
fetch('/api/config').then(r=>r.json()).then(config=>{const list=$('sources');list.replaceChildren();for(const source of config.data?.sources||[]){const li=document.createElement('li'),name=document.createElement('span'),meta=document.createElement('span');name.textContent=source.name;meta.className='mono';meta.textContent=[source.licence,source.accessed].filter(Boolean).join(' · ');li.append(name,meta);list.append(li);}if(!list.children.length)list.textContent='Data sources unavailable';}).catch(()=>{$('sources').textContent='Data sources unavailable';});

// Local controls avoid WebKit's CSP-blocked blob icons and keep one player per clip.
for(const controls of document.querySelectorAll('[data-video]')){
 const media=$(controls.dataset.video),play=controls.querySelector('.clip-play'),seek=controls.querySelector('.clip-seek'),time=controls.querySelector('.clip-time');
 const refresh=()=>{play.textContent=media.paused?'Play':'Pause';play.setAttribute('aria-label',(media.paused?'Play':'Pause')+' evidence');seek.value=media.duration?media.currentTime/media.duration*100:0;time.textContent=Math.floor(media.currentTime/60)+':'+String(Math.floor(media.currentTime%60)).padStart(2,'0');};
 play.addEventListener('click',()=>{if(media.paused)media.play().catch(()=>{});else media.pause();});
 seek.addEventListener('input',()=>{if(Number.isFinite(media.duration))media.currentTime=Number(seek.value)/100*media.duration;});
 for(const name of ['play','pause','timeupdate','loadedmetadata','ended'])media.addEventListener(name,refresh);
 refresh();
}
