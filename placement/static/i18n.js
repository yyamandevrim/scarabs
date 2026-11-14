'use strict';
// Placement is English-only. Keep brand hydration shared by Overview and map.
// The old dictionary remains on disk for compatibility; it is never fetched or applied.
(() => {
 document.documentElement.lang='en';
 try{localStorage.setItem('language','en');}catch{}
 window.placementText=en=>en;
 fetch('/api/brand').then(r=>r.json()).then(brand=>{
  document.querySelectorAll('[data-brand-name]').forEach(e=>e.textContent=brand.name);
  document.querySelectorAll('[data-brand-tagline]').forEach(e=>e.textContent=brand.tagline.en);
  for(const key of ['team','expansion','event','challenge'])document.querySelectorAll('[data-brand-'+key+']').forEach(e=>e.textContent=brand[key]||'');
  document.querySelectorAll('[data-brand-logo]').forEach(e=>{if(e.getAttribute('src')!==brand.logo)e.src=brand.logo;});
  document.querySelectorAll('[data-brand-stacked]').forEach(e=>{const path=brand.stacked_logo||brand.logo;if(e.getAttribute('src')!==path)e.src=path;});
  const title=document.body.dataset.pageTitle||'';document.title=brand.name+(title?' · '+title:'');
  window.dispatchEvent(new Event('languagechange'));
 }).catch(()=>{/* Identity is already rendered by branded_page for offline/error resilience. */});
})();
