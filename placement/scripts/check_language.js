// Run as preview_evaluate's expression on / or /map after the page is ready.
(async () => {
  const mapPage=location.pathname==='/map';
  const identity=await (await fetch('/api/brand')).json();
  const coordinates=mapPage?[document.querySelector('#lat').value,document.querySelector('#lon').value]:null;
  const checks=[];
  for(const lang of ['en','tr']){
    if(document.documentElement.lang!==lang)document.querySelector('.language').click();
    await new Promise(resolve=>setTimeout(resolve,40));
    const text=document.body.innerText;
    const expected=mapPage?(lang==='en'?'Occluded inside FOV · simulated ha':'Görüş alanı içinde perdelenmiş · simülasyon ha'):(lang==='en'?'A better view.':'Daha iyi bir görüş.');
    if(!text.includes(expected))throw Error('Missing rendered '+lang+' text: '+expected);
    if(document.querySelector('[data-brand-name]').textContent!==identity.name)throw Error('Brand config not rendered');
    if(!document.title.includes(identity.tagline[lang]))throw Error('Localized config tagline not rendered');
    if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal page overflow');
    if(mapPage&&JSON.stringify(coordinates)!==JSON.stringify([document.querySelector('#lat').value,document.querySelector('#lon').value]))throw Error('Language switch lost candidate coordinates');
    checks.push({lang,rendered:true,brand:true,overflow:false});
  }
  const external=performance.getEntriesByType('resource').filter(r=>!r.name.startsWith(location.origin));
  if(external.length)throw Error('Unexpected external resources');
  return {page:location.pathname,width:innerWidth,checks,externalResources:0};
})()
