'use strict';
// English only: stored preferences and URL parameters cannot select another language.
(() => {
 document.documentElement.lang='en';
 try{localStorage.setItem('language','en')}catch{}
 document.querySelectorAll('.language').forEach(button=>button.remove());
 window.placementText=en=>en;
 const assetVersion=document.body.dataset.assetVersion||'';
 document.querySelectorAll('[data-product-desktop]').forEach(e=>e.src='/static/placement-preview-en.png?v='+assetVersion);
 document.querySelectorAll('[data-product-phone]').forEach(e=>e.srcset='/static/placement-preview-phone-en.png?v='+assetVersion);
 fetch('/api/brand').then(r=>r.json()).then(brand=>{
  for(const key of ['name','team','expansion','event','challenge'])document.querySelectorAll('[data-brand-'+key+']').forEach(e=>e.textContent=brand[key]||'');
  document.querySelectorAll('[data-brand-tagline]').forEach(e=>e.textContent=brand.tagline.en);
  document.querySelectorAll('[data-brand-logo]').forEach(e=>e.src=brand.logo);
  document.querySelectorAll('[data-brand-stacked]').forEach(e=>e.src=brand.stacked_logo||brand.logo);
  document.title=brand.name+(document.body.dataset.pageTitle?' · '+document.body.dataset.pageTitle:'');
 }).catch(()=>{});
})();
