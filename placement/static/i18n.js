'use strict';
// One shared translation layer for static and dynamically generated text.
(() => {
 let lang;try{lang=localStorage.getItem('language')||'en'}catch{lang='en'}
 if(!['en','tr'].includes(lang))lang='en';
 document.documentElement.lang=lang;
 let dictionary={}, brand=null, observer;
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
     if(node.parentElement.closest('script,style,[data-brand-name],[data-brand-tagline],[data-brand-team],.language'))continue;
     const old=originals.get(node);const canonical=old&&old.last===node.nodeValue?old.source:translate(node.nodeValue,'en');
     const value=lang==='en'?canonical:translate(canonical,'tr');
     if(node.nodeValue!==value)node.nodeValue=value;
     originals.set(node,{source:canonical,last:value});
   }
   document.querySelectorAll('[aria-label]').forEach(el=>{
     const current=el.getAttribute('aria-label');const canonical=translate(current,'en');
     el.setAttribute('aria-label',lang==='en'?canonical:translate(canonical,'tr'));
   });
   document.querySelectorAll('.language').forEach(b=>{b.textContent=lang==='en'?'Türkçe':'English';b.setAttribute('aria-label',lang==='en'?'Switch to Turkish':'İngilizceye geç')});
   if(brand){
     document.querySelectorAll('[data-brand-name]').forEach(e=>e.textContent=brand.name);
     document.querySelectorAll('[data-brand-tagline]').forEach(e=>e.textContent=brand.tagline[lang]);
     document.querySelectorAll('[data-brand-team]').forEach(e=>e.textContent=brand.team);
     document.querySelectorAll('[data-brand-logo]').forEach(e=>{if(e.getAttribute('src')!==brand.logo)e.src=brand.logo});
     document.querySelectorAll('[data-brand-icon]').forEach(e=>{if(e.getAttribute('href')!==brand.logo)e.href=brand.logo});
     document.title=brand.name+' · '+brand.tagline[lang];
   }
   observer?.observe(document.body,{subtree:true,childList:true,characterData:true});
 }
 document.querySelectorAll('.language').forEach(button=>button.addEventListener('click',()=>{
   lang=lang==='en'?'tr':'en';document.documentElement.lang=lang;
   try{localStorage.setItem('language',lang)}catch{}
   render();window.dispatchEvent(new Event('languagechange'));render();
 }));
 Promise.all([fetch('/static/translations.json').then(r=>r.json()),fetch('/api/brand').then(r=>r.json())]).then(([d,b])=>{
   dictionary=d;brand=b;observer=new MutationObserver(render);render();
 });
})();
