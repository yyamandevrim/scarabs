'use strict';
(() => {
 const $=id=>document.getElementById(id);
 const facts={
  left:['Camera 3','One of the three cameras mounted around the triangular housing. Select the view to see its part of the surrounding forest.'],
  centre:['Camera 1','The front pod defines the module’s reference direction. Smoke analysis happens locally, on the module.'],
  right:['Camera 2','The cameras face outward from the three sides of the housing, watching the forest in every direction.'],
  eye:['Tether openings','The tether passes through paired openings in the top and bottom plates.'],
  housing:['Housing · Arduino UNO Q inside','An Arduino UNO Q runs local smoke analysis. Every smoke suspicion goes to a person for review.']
 };
 let viewer=null,fov=false,exploded=false;
 function selectPart(id){const [title,body]=facts[id];$('part-detail').replaceChildren(Object.assign(document.createElement('h2'),{textContent:title}),Object.assign(document.createElement('p'),{textContent:body}));document.querySelectorAll('[data-part]').forEach(b=>b.setAttribute('aria-current',String(b.dataset.part===id)));viewer?.highlight(id);}
 document.querySelectorAll('[data-part]').forEach(b=>{b.addEventListener('pointerenter',()=>selectPart(b.dataset.part));b.addEventListener('focus',()=>selectPart(b.dataset.part));b.addEventListener('click',()=>{selectPart(b.dataset.part);});});
 $('fov-toggle').addEventListener('click',()=>{fov=!fov;$('fov-toggle').setAttribute('aria-pressed',String(fov));$('fov-toggle').textContent=fov?'Hide fields of view':'Show fields of view';$('model-stage').classList.toggle('show-fov',fov);viewer?.toggleFov(fov);});
 $('explode-toggle').addEventListener('click',()=>{exploded=!exploded;$('explode-toggle').setAttribute('aria-pressed',String(exploded));$('explode-toggle').textContent=exploded?'Put it back':'Take it apart';viewer?.explode(exploded);});
 $('reset-model').addEventListener('click',()=>{exploded=false;$('explode-toggle').setAttribute('aria-pressed','false');$('explode-toggle').textContent='Take it apart';viewer?.reset();});
 const steps=[['cameras','Camera view over Wi-Fi.','Camera view · Wi-Fi'],['evidence','Smoke suspicion evidence on the station panel.','Smoke suspicion · open the evidence'],['evidence','Saved evidence and operator decision controls.','Evidence clip and decision · Wi-Fi']];
 let currentStep=0,phoneVisible=false;
 const phoneVideo=$('phone-video');
 function syncPhoneVideo(){if(currentStep===2&&phoneVisible&&!document.hidden)phoneVideo.play().catch(()=>{});else phoneVideo.pause();}
 document.querySelectorAll('[data-step]').forEach(button=>button.addEventListener('click',()=>{currentStep=Number(button.dataset.step);const [name,alt,caption]=steps[currentStep];$('phone-capture').src='/static/demo/iphone-station-'+name+'.webp';$('phone-capture').alt=alt;$('phone-capture').hidden=currentStep===2;$('phone-capture').classList.toggle('feed-crop',currentStep===0);phoneVideo.hidden=currentStep!==2;$('phone-caption').textContent=caption;document.querySelectorAll('[data-step]').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));syncPhoneVideo();}));
 new IntersectionObserver(([entry])=>{phoneVisible=entry.isIntersecting;syncPhoneVideo();},{threshold:.35}).observe(phoneVideo);
 document.addEventListener('visibilitychange',syncPhoneVideo);
 fetch('/api/config').then(r=>{if(!r.ok)throw Error();return r.json();}).then(config=>{
  const list=$('sources');list.replaceChildren();
  for(const source of config.data?.sources||[]){const li=document.createElement('li'),name=document.createElement('span'),meta=document.createElement('span');name.textContent=source.name;meta.className='mono muted';meta.textContent=[source.licence,source.accessed].filter(Boolean).join(' · ');li.append(name,meta);list.append(li);}
  if(!list.children.length)list.append(Object.assign(document.createElement('li'),{className:'muted',textContent:'Data unavailable'}));
 }).catch(()=>{$('sources').replaceChildren(Object.assign(document.createElement('li'),{className:'muted',textContent:'Data unavailable'}));});
 // Defer the entire 3D bundle until after the first painted frame, including restored pages.
 const fail=()=>{$('model-canvas').tabIndex=-1;$('model-fallback').hidden=false;$('drag-hint').hidden=true;$('model-stage').classList.remove('ready');$('model-stage').classList.add('fallback');};
 requestAnimationFrame(()=>requestAnimationFrame(()=>{
  import('/static/vendor/landing-3d.js').then(module=>module.mountModel({selectPart})).then(api=>{viewer=api;for(const id of ['fov-toggle','explode-toggle','reset-model'])$(id).disabled=false;}).catch(fail);
 }));
})();
