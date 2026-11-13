'use strict';
// Landing: data readiness and the dataset list come from /api/config, not from page copy.
(function(){
 const $=id=>document.getElementById(id);
 fetch('/api/config').then(r=>{if(!r.ok)throw Error();return r.json()}).then(config=>{
  const list=$('sources');list.replaceChildren();
  for(const source of config.data?.sources||[]){const li=document.createElement('li');const name=document.createElement('span');name.textContent=source.name;const meta=document.createElement('span');meta.className='mono muted';meta.textContent=[source.licence,source.accessed].filter(Boolean).join(' · ');li.append(name,meta);list.append(li);}
  if(!list.children.length){const li=document.createElement('li');li.className='muted';li.textContent='Data unavailable';list.append(li);}
 }).catch(()=>{$('sources').replaceChildren(Object.assign(document.createElement('li'),{className:'muted',textContent:'Data unavailable'}));});
})();
