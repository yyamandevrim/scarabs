// Evaluate on / or /map after load. The browser regression also seeds language=tr
// and requests ?lang=tr&language=tr before running this check.
(async () => {
 const text=document.body.innerText;
 if(document.documentElement.lang!=='en')throw Error('Page language must be English');
 if(document.querySelector('.language'))throw Error('Language toggle remains');
 if(/Türkçe|Görüş|görünür|Simülasyon|Kalkış|bağlı değil/i.test(text))throw Error('Turkish text rendered');
 if(/two of three|connect two|camera pair|two active inputs|disconnected|three.camera.+reference|heading drift/i.test(text))throw Error('Obsolete camera model rendered');
 if(document.documentElement.scrollWidth>innerWidth)throw Error('Horizontal page overflow');
 const identity=await (await fetch('/api/brand')).json();
 if(document.querySelector('[data-brand-name]').textContent!==identity.name)throw Error('Brand config not rendered');
 const external=performance.getEntriesByType('resource').filter(r=>!r.name.startsWith(location.origin));
 if(external.length)throw Error('Unexpected external resources');
 return {page:location.pathname,width:innerWidth,language:'en',toggle:false,overflow:false,externalResources:0};
})()
