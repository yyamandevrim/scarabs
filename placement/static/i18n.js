'use strict';
// One shared translation layer for static and dynamically generated text.
(() => {
 let lang;try{lang=localStorage.getItem('language')||'en'}catch{lang='en'}
 if(!['en','tr'].includes(lang))lang='en';
 document.documentElement.lang=lang;
 let dictionary={}, brand=null, observer;
 const assetVersion=document.body.dataset.assetVersion||'';
 window.placementText=(en,tr)=>lang==='tr'?tr:en;
 const originals=new WeakMap();
 const translate=(value,to)=>{
   const entries=Object.entries(dictionary).map(([en,tr])=>to==='tr'?[en,tr]:[tr,en]).sort((a,b)=>b[0].length-a[0].length);
   const trimmed=value.trim();const exact=entries.find(([source])=>trimmed===source);
   if(exact)return value.replace(trimmed,exact[1]);
   const table=new Map(entries);
   const escaped=entries.map(([source])=>source.replace(/[.*+?^${}()|[\]\\]/g,'\\$&'));
   const pattern=new RegExp('(?<![\\p{L}\\p{N}])(?:'+escaped.join('|')+')(?![\\p{L}\\p{N}])','gu');
   return value.replace(pattern,match=>table.get(match));
 };
 function render(){
   observer?.disconnect();
   const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
   let node;
   while(node=walker.nextNode()){
     if(node.parentElement.closest('script,style,[data-brand-name],[data-brand-tagline],[data-brand-team],[data-brand-expansion],[data-brand-event],[data-brand-challenge],.language,[data-localized]'))continue;
     const old=originals.get(node);const canonical=old&&old.last===node.nodeValue?old.source:translate(node.nodeValue,'en');
     const value=lang==='en'?canonical:translate(canonical,'tr');
     if(node.nodeValue!==value)node.nodeValue=value;
     originals.set(node,{source:canonical,last:value});
   }
   document.querySelectorAll('[aria-label], [title], [alt]').forEach(el=>{
     for(const attr of ['aria-label','title','alt']){const current=el.getAttribute(attr);if(current===null)continue;const canonical=translate(current,'en');el.setAttribute(attr,lang==='en'?canonical:translate(canonical,'tr'));}
   });
   document.querySelectorAll('[data-product-desktop]').forEach(e=>{const path='/static/placement-preview-'+lang+'.png?v='+assetVersion;if(e.getAttribute('src')!==path)e.src=path});
   document.querySelectorAll('[data-product-phone]').forEach(e=>{const path='/static/placement-preview-phone-'+lang+'.png?v='+assetVersion;if(e.getAttribute('srcset')!==path)e.srcset=path});
   document.querySelectorAll('.language').forEach(b=>{b.textContent=lang==='en'?'Türkçe':'English';b.setAttribute('aria-label',lang==='en'?'Switch to Turkish':'İngilizceye geç')});
   if(brand){
     document.querySelectorAll('[data-brand-name]').forEach(e=>e.textContent=brand.name);
     document.querySelectorAll('[data-brand-tagline]').forEach(e=>e.textContent=brand.tagline[lang]);
     document.querySelectorAll('[data-brand-team]').forEach(e=>e.textContent=brand.team);
     for(const key of ['expansion','event','challenge'])document.querySelectorAll('[data-brand-'+key+']').forEach(e=>e.textContent=brand[key]||'');
     document.querySelectorAll('[data-brand-logo]').forEach(e=>{if(e.getAttribute('src')!==brand.logo)e.src=brand.logo});
     document.querySelectorAll('[data-brand-stacked]').forEach(e=>{const path=brand.stacked_logo||brand.logo;if(e.getAttribute('src')!==path)e.src=path});
     const pageTitle=document.body.dataset.pageTitle||'';
     document.title=brand.name+(pageTitle?' · '+(lang==='en'?pageTitle:translate(pageTitle,'tr')):'');
   }
   observer?.observe(document.body,{subtree:true,childList:true,characterData:true});
 }
 document.querySelectorAll('.language').forEach(button=>button.addEventListener('click',()=>{
   lang=lang==='en'?'tr':'en';document.documentElement.lang=lang;
   try{localStorage.setItem('language',lang)}catch{}
   render();window.dispatchEvent(new Event('languagechange'));render();
 }));
 Promise.allSettled([fetch('/static/translations.json?v='+assetVersion).then(r=>r.json()),fetch('/api/brand').then(r=>r.json())]).then(([d,b])=>{
   dictionary=d.status==='fulfilled'?d.value:{};brand=b.status==='fulfilled'?b.value:null;observer=new MutationObserver(render);render();window.dispatchEvent(new Event('languagechange'));
 });
})();
