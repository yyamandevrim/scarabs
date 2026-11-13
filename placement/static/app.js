'use strict';
const $=id=>document.getElementById(id),M=PlacementMetrics,C=PlacementCharts;
const lang=()=>document.documentElement.lang;
const tr=(en,turkish)=>lang()==='tr'?turkish:en;
function localized(el,en,turkish){el.setAttribute('data-localized','');el.textContent=tr(en,turkish);return el;}
const fmt=(value,digits=0)=>M.number(value,lang(),digits);
const area=(value,resolution)=>M.headline(value,resolution,lang());
let candidates=[],results=[null,null],selected=0,map=null,layers=null,overlay=null,priorityLayer=null,drawing=false,drawPoints=[],priority=null,timer=null,busy=false,pending=new Set();
let scenario='canopy_smoke',dataInfo=null,dirty=new Set([0,1]),lastError='',ready=false;
const cameraNames=['Left','Centre','Right'],cameraNamesTr=['Sol','Merkez','Sağ'],letters='AB';
const camName=i=>tr(cameraNames[i],cameraNamesTr[i]);
const pairName=p=>p.pair.map((i,k)=>k?camName(i).toLocaleLowerCase(lang()==='tr'?'tr':'en'):camName(i)).join(' + ');
const siteName=c=>c?.name?.split(' · ').pop()||'—';
let mapRenderRevision=0;
const token=name=>getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const scenarioNames={canopy_smoke:['smoke + canopy','duman + taç'],canopy_ground:['ground + canopy','zemin + taç'],bare_smoke:['smoke / bare terrain','duman / çıplak arazi'],bare_ground:['ground / bare terrain','zemin / çıplak arazi']};
function el(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=text;return e;}
function addText(parent,tag,text,cls){const e=el(tag,cls,text);parent.append(e);return e;}

// --- Shell state -------------------------------------------------------------
function status(text,error=false){$('status').textContent=text;$('status').classList.toggle('error',error);}
function banner(title,text,retry){$('banner').hidden=!title;$('banner-title').textContent=title||'';$('banner-text').textContent=text||'';$('retry').hidden=!retry;}
function state(text,error=false,turkish){const e=$('result-state');if(turkish)localized(e,text,turkish);else{e.removeAttribute('data-localized');e.textContent=text;}e.classList.toggle('error',error);}
function setBusy(value){for(const id of ['result-summary','details-results'])$(id).setAttribute('aria-busy',String(value));$('analyze').disabled=value;$('analyze').setAttribute('aria-busy',String(value));}
function markStale(indices=[selected]){indices.forEach(i=>dirty.add(i));lastError='';document.body.classList.add('stale');if(indices.some(i=>results[i]))state('Updating · results are for previous settings.');}
function later(delay=600){markStale();clearTimeout(timer);timer=setTimeout(()=>run(false),delay);}

// --- Controls ----------------------------------------------------------------
function readControls(){if(!candidates.length)return;const c=candidates[selected];c.lat=+$('lat').value;c.lon=+$('lon').value;c.height=+$('height').value;c.heading=+$('heading').value;c.resolution=$('resolution').value;c.max_range=+$('max-range').value*1000;c.smoke_height=+$('smoke-height').value;$('heading-value').textContent=c.heading+'°';}
function cameraControls(){const c=candidates[selected];const count=c.cameras.filter(cam=>cam.active).length,off=c.cameras.map((cam,i)=>cam.active?null:i).filter(i=>i!==null);
 localized($('camera-status'),`${count} active / 3 mounted`+(off.length?' · '+off.map(i=>cameraNames[i]).join(' + ')+' disconnected':''),`3 takılı kameradan ${count} etkin`+(off.length?' · '+off.map(i=>cameraNamesTr[i]).join(' + ')+' bağlı değil':''));
 const box=$('camera-controls');box.replaceChildren();const head=el('div','camera-row camera-head');['Active','Yaw °','Tilt °','H-FOV °','V-FOV °'].forEach(t=>head.append(el('span','',t)));box.append(head);
 c.cameras.forEach((cam,i)=>{const row=el('div','camera-row'+(cam.active?'':' inactive'));const label=el('label','camera-name'),check=document.createElement('input');check.type='checkbox';check.checked=cam.active;check.disabled=c.reference||(!cam.active&&count>=2);check.setAttribute('aria-label',cameraNames[i]+' camera connected');check.addEventListener('change',()=>{cam.active=check.checked;cameraControls();later()});label.append(check,document.createTextNode(cameraNames[i]));row.append(label);
  ['yaw','tilt','hfov','vfov'].forEach(key=>{const input=document.createElement('input');input.type='number';input.className='mono';input.value=cam[key];input.step=1;const limits={yaw:[-180,180],tilt:[-80,89],hfov:[1,160],vfov:[1,160]}[key];input.min=limits[0];input.max=limits[1];input.setAttribute('aria-label',cameraNames[i]+' '+{yaw:'yaw',tilt:'tilt',hfov:'horizontal FOV',vfov:'vertical FOV'}[key]);input.addEventListener('change',()=>{cam[key]=+input.value;later()});row.append(input)});box.append(row)});
}
function showControls(){const c=candidates[selected];if(!c)return;$('lat').value=c.lat.toFixed(5);$('lon').value=c.lon.toFixed(5);$('height').value=c.height;$('heading').value=c.heading;$('heading-value').textContent=c.heading+'°';$('resolution').value=c.resolution;$('max-range').value=c.max_range/1000;$('smoke-height').value=c.smoke_height;$('reference').checked=c.reference;$('settings-site').textContent=letters[selected]+' · '+siteName(c);cameraControls();}
function selectSite(i,reveal=true){if(i===selected||!candidates[i])return;readControls();selected=i;showControls();render();if(reveal)revealSite(i);}

// --- Headline metric: total visible forest, or priority forest while a polygon is active.
const usePriority=()=>Boolean(priority);
function headlineValue(r){return usePriority()?M.priorityValue(r,scenario):r?.metrics?.[scenario]?.visible_forest_ha;}
function mode(r){return r?.input?.reference?'reference':'pair';}
function pairText(r){return r?.input?.reference?tr('Three cameras, reference','Üç kamera, referans'):(r?.active_cameras||[]).map((i,k)=>k?camName(i).toLocaleLowerCase(lang()==='tr'?'tr':'en'):camName(i)).join(' + ');}


function renderSummary(){
 const priorityMode=usePriority();
 localized($('result-title'),(priorityMode?'Visible priority forest · ':'Visible forest · ')+scenarioNames[scenario][0],(priorityMode?'Görünür öncelikli orman · ':'Görünür orman · ')+scenarioNames[scenario][1]);
 const figures=$('headline-figures');figures.replaceChildren();
 candidates.forEach((c,i)=>{const r=results[i],m=r?.metrics?.[scenario],block=el('div','headline-site'+(i===selected?' selected':'')+(r&&dirty.has(i)?' stale':''));
  const b=el('button','headline-name');b.type='button';b.append(el('span','cand-letter mono',letters[i]),document.createTextNode(siteName(c)));b.setAttribute('aria-pressed',String(i===selected));b.addEventListener('click',()=>selectSite(i));block.append(b);
  const shown=r?area(headlineValue(r),r.resolution_m):'—',n=addText(block,'div',shown,'headline-value'+(shown==='—'?' missing':''));if(shown!=='—')addText(n,'small',' ha');
  if(r)localized(addText(block,'p','','headline-sub'),`${fmt(r.input.height)} m · ${fmt(r.input.heading)}° · ${pairText(r)}`,`${fmt(r.input.height)} m · ${fmt(r.input.heading)}° · ${pairText(r)}`);else localized(addText(block,'p','','headline-sub'),'Not computed','Hesaplanmadı');
  if(r&&priorityMode&&M.valid(m?.visible_forest_ha))localized(addText(block,'p','','headline-sub'),`of ${area(m.visible_forest_ha,r.resolution_m)} ha visible forest in total`,`toplam görünür orman ${area(m.visible_forest_ha,r.resolution_m)} ha`);
  if(r&&M.valid(M.share(m)))localized(addText(block,'p','','headline-sub'),`${M.percent(M.share(m),'en')} of the view is water`,`Görülen alanda su payı: ${M.percent(M.share(m),'tr')}`);
  figures.append(block)});
 const values=results.map(headlineValue),comparable=results.every(Boolean)&&mode(results[0])===mode(results[1]);
 if(results.every(Boolean)&&!comparable)localized($('verdict'),'No comparison: the sites use different camera modes.','Karşılaştırma yok: iki konumda farklı kamera modu var.');
 else if(values.every(M.valid)){const winner=values[0]>=values[1]?0:1,other=1-winner,high=values[winner],low=values[other],what=priorityMode?['visible priority forest','görünür öncelikli orman']:['visible forest','görünür orman'];
  localized($('verdict'),high===low?`Both sites show the same ${what[0]}.`:low>0?`${siteName(candidates[winner])} shows ${fmt(high/low,1)}× the ${what[0]}.`:`${siteName(candidates[winner])} shows more ${what[0]}.`,high===low?`İki konumda da aynı ${what[1]} görünüyor.`:low>0?`${siteName(candidates[winner])} konumunda ${fmt(high/low,1)} kat daha fazla ${what[1]} görünüyor.`:`${siteName(candidates[winner])} konumunda daha fazla ${what[1]} görünüyor.`);
 }else localized($('verdict'),busy&&!lastError?'The comparison appears when both sites are calculated.':'No comparison yet. Recalculate both sites to compare.',busy&&!lastError?'Karşılaştırma iki konum da hesaplandığında görünür.':'Henüz karşılaştırma yok. Karşılaştırmak için iki konumu yeniden hesaplayın.');
 const smoke=r=>r?.metrics?.canopy_smoke,ranked=comparable?[0,1].filter(i=>M.valid(smoke(results[i])?.visible_forest_ha)).sort((a,b)=>(priorityMode?(smoke(results[b]).priority_visible_ha??-Infinity)-(smoke(results[a]).priority_visible_ha??-Infinity):0)||smoke(results[b]).visible_forest_ha-smoke(results[a]).visible_forest_ha):[];
 if(ranked.length===2){const order=ranked.map((i,k)=>`${k+1} ${siteName(candidates[i])}`).join(', ');localized($('ranking'),`Ranking by ${priorityMode?'visible priority forest':'total visible forest'} (smoke-target scenario): ${order}`,`Sıralama, ${priorityMode?'görünür öncelikli orman':'toplam görünür orman'} (duman hedefi senaryosu): ${order}`);}else $('ranking').textContent='';
 const stale=[...dirty].some(i=>results[i]),missing=[0,1].filter(i=>!results[i]).map(i=>siteName(candidates[i])).join(', ');document.body.classList.toggle('stale',stale);
 if(lastError)state(lastError+(results.some(Boolean)?' Results are for previous settings.':''),true);else if(stale)state('Updating · results are for previous settings.');else if(missing)state(busy?`Calculating ${missing}…`:'— means not computed. Recalculate both sites to begin.',false,busy?`${missing} hesaplanıyor…`:'— hesaplanmadı demektir. Başlamak için iki konumu yeniden hesaplayın.');else state('');

}

// --- Charts ------------------------------------------------------------------
function renderAccounting(){
 const box=$('accounting');box.replaceChildren();const rows=results.map((r,i)=>({i,r,a:r?C.accounting(r.metrics?.[scenario],M.round,M.blind,r.resolution_m):null}));const max=Math.max(1,...rows.map(x=>x.a?.total).filter(M.valid));
 rows.forEach(({i,r,a})=>{const row=el('div','acc-row'+(i===selected?' selected':''));const head=el('div','acc-head');head.append(el('span','cand-letter mono',letters[i]),el('span','acc-name',siteName(candidates[i])),el('span','acc-total mono',a?fmt(a.total):'—'));row.append(head);
  const bar=el('div','acc-bar');if(a){for(const [key,cls] of [['visible','visible'],['occluded','occluded'],['outside','outside']]){const seg=el('i',cls);seg.style.width=(a[key]/max*100)+'%';seg.title=key;bar.append(seg);}}else bar.classList.add('empty');row.append(bar);
  const legend=el('div','acc-values');if(a){for(const [key,en,turkish] of [['visible','Visible','Görünür'],['occluded','Occluded','Perdelenmiş'],['outside','Outside FOV','Görüş dışında']]){const s=el('span');s.append(el('i','sw '+key));localized(s.appendChild(el('span')),`${en} ${fmt(a[key])}`,`${turkish} ${fmt(a[key])}`);legend.append(s);}}else localized(legend,r?'Split not available':'Not computed',r?'Ayrım yok':'Hesaplanmadı');row.append(legend);box.append(row)});
 localized(addText(box,'p','','small'),'Forest inside the range disk. Total = visible + occluded in FOV + outside FOV.','Menzil diski içindeki orman. Toplam = görünür + görüş içinde perdelenmiş + görüş dışında.');
}
function renderPairs(){
 const box=$('pairs');box.replaceChildren();$('pair-gain').textContent='';$('pair-summary').textContent='';localized($('pair-title'),'Compare camera pairs','Kamera çiftlerini karşılaştır');
 const result=results[selected];document.querySelector('.pair-panel')?.classList.toggle('empty',!result);
 if(!result){localized($('pair-context'),'Not computed','Hesaplanmadı');return;}
 const res=result.resolution_m,step=v=>M.round(v,res),pairs=result.pair_comparison||[],priorityMode=Boolean(result.input.priority),best=M.bestPair(pairs,scenario,priorityMode),current=result.metrics?.[scenario],same=p=>!result.input.reference&&JSON.stringify(p.pair)===JSON.stringify(result.active_cameras),ref=result.reference?.metrics?.[scenario];
 $('pair-context').textContent=`${letters[selected]} · ${siteName(candidates[selected])} · ${fmt(result.input.heading)}° · ${fmt(result.input.height)} m`;
 const value=m=>priorityMode?m?.priority_visible_ha:m?.visible_forest_ha,max=Math.max(1,...pairs.map(p=>value(p[scenario])).concat([value(ref)]).filter(M.valid));
 localized(addText(box,'p','','pairs-axis'),priorityMode?'Visible priority forest · ha':'Visible forest · ha','Görünür '+(priorityMode?'öncelikli ':'')+'orman · ha');
 pairs.forEach(p=>{const b=el('button','pair-row'+(same(p)?' chosen':'')+(p===best?' best':''));b.type='button';b.setAttribute('aria-pressed',String(same(p)));
  const top=el('span','pair-top');top.append(el('span','pair-name',pairName(p)),el('b','mono',area(value(p[scenario]),res)));b.append(top);
  const bar=el('span','pair-bar'),fill=el('i','visible');fill.style.width=(M.valid(value(p[scenario]))?value(p[scenario])/max*100:0)+'%';const ov=el('i','overlap');ov.style.width=(M.valid(p[scenario]?.overlap_forest_ha)?p[scenario].overlap_forest_ha/max*100:0)+'%';bar.append(fill,ov);b.append(bar);
  const sub=b.appendChild(el('span','pair-sub'));localized(sub.appendChild(el('span')),`${fmt(step(p[scenario]?.overlap_forest_ha))} ha overlap`,`${fmt(step(p[scenario]?.overlap_forest_ha))} ha ortak görüş`);if(p===best)localized(top.querySelector('.pair-name').appendChild(el('span','tag tag-best')),'Best','En iyi');if(same(p))localized(top.querySelector('.pair-name').appendChild(el('span','tag tag-current')),'Current','Mevcut');
  b.addEventListener('click',()=>{const c=candidates[selected],leaving=candidates.some(x=>x.reference);
   // Leaving reference mode returns both sites to two inputs, so both are recalculated.
   if(leaving)candidates.forEach(x=>{x.reference=false;x.cameras.forEach((cam,i)=>cam.active=i<2)});
   c.cameras.forEach((cam,i)=>cam.active=p.pair.includes(i));showControls();run(leaving)});box.append(b)});

 if(best){localized($('pair-title'),'Camera pairs','Kamera çiftleri');const gain=step(value(best[scenario]))-step(value(current));
  if(!result.input.reference&&M.valid(gain))localized($('pair-summary'),same(best)?`${siteName(candidates[selected])}: the connected pair is already the best of three.`:`${siteName(candidates[selected])}: connecting ${pairName(best).toLowerCase()} adds ${fmt(gain)} ha over the current pair.`,same(best)?`${siteName(candidates[selected])}: bağlı çift üç çift içinde zaten en iyisi.`:`${siteName(candidates[selected])}: ${pairName(best).toLocaleLowerCase('tr')} bağlanırsa mevcut çifte göre +${fmt(gain)} ha.`);
  localized($('pair-gain'),result.input.reference?'Three-camera reference is active; pair gains use two cameras.':same(best)?'The current pair is best for this site.':`+${fmt(gain)} ha over the current pair.`,result.input.reference?'Üç kamera referansı etkin; çift kazançları iki kamerayı kullanır.':same(best)?'Bu konum için en iyi çift şu anda etkin.':`Mevcut çifte göre +${fmt(gain)} ha.`);
 }
}
function renderSensitivity(){const result=results[selected];C.sensitivityChart($('sensitivity'),{points:result?.heading_sensitivity||[],format:v=>area(v,result?.resolution_m),tick:v=>fmt(v),axis:tr('Visible forest by module heading','Modül yönüne göre görünür orman'),current:0});}

// --- Table and notes -----------------------------------------------------------
function appendRow(body,label,unit,values,cls=''){const row=el('tr',cls);[label,unit,...values].forEach((v,i)=>{const td=el(i===0?'th':'td','',v);if(i===0)td.scope='row';if(i===1)td.className='unit';if(v==='—')td.title='Not computed';row.append(td)});body.append(row);}
function renderTable(){
 const headers=$('comparison').querySelectorAll('thead th');candidates.forEach((c,i)=>headers[i+2].textContent=letters[i]+' · '+siteName(c));const body=$('comparison').querySelector('tbody');body.replaceChildren();
 const metrics=results.map(r=>r?.metrics?.[scenario]),res=results.map(r=>r?.resolution_m),split=metrics.map((m,i)=>M.blind(m,res[i])),values=key=>metrics.map((m,i)=>fmt(M.round(m?.[key],res[i]))),other=key=>results.map(r=>fmt(M.round(key(r),r?.resolution_m)));
 localized($('precision'),res.includes(120)?'Quick 120 m figures are rounded to 10 ha; detailed 40 m to whole hectares.':'Rounded to whole hectares.',res.includes(120)?'Hızlı 120 m değerleri 10 ha’ya, ayrıntılı 40 m değerleri tam hektara yuvarlanır.':'Tam hektara yuvarlanmıştır.');
 appendRow(body,'Visible forest','ha',values('visible_forest_ha'),'main-metric');
 appendRow(body,'Blind total','ha',split.map(s=>fmt(s.total)),'band');appendRow(body,'Outside FOV','ha',split.map(s=>fmt(s.outside)),'sub');appendRow(body,'Occluded in FOV','ha',split.map(s=>fmt(s.occluded)),'sub');
 appendRow(body,'Overlap ≥2 cams','ha',values('overlap_forest_ha'),'band');appendRow(body,'Water in view','ha',values('water_view_ha'));appendRow(body,'Water share','%',metrics.map(m=>fmt(M.share(m))));appendRow(body,'Visible priority forest','ha',other(r=>M.priorityValue(r,scenario)));
 appendRow(body,'Bare terrain · ground','ha',other(r=>r?.metrics?.bare_ground?.visible_forest_ha),'band');appendRow(body,'Canopy · ground','ha',other(r=>r?.metrics?.canopy_ground?.visible_forest_ha));appendRow(body,'Three-camera reference','ha',other(r=>r?.reference?.metrics?.[scenario]?.visible_forest_ha));
 $('uncertainty').replaceChildren();if(dataInfo){['Positive canopy cover is treated as opaque. Mean stand height is not a measured maximum crown height.','Smoke target is a fixed point above the obstruction surface, not a smoke-dispersion model.','Curvature included; refraction, haze, wind and optical detection are not modelled.',dataInfo.buildings_included?'Building heights included':'No building heights','Sectors show horizontal direction; cells use the full 3D field of view. North = EPSG:3067 grid north.'].forEach(note=>addText($('uncertainty'),'p',note));results.forEach((r,i)=>{if(r?.range_clipped)addText($('uncertainty'),'p',siteName(candidates[i])+': Areas are clipped to the prepared region when the range circle crosses its boundary.');if(r?.unknown_forest_ha)addText($('uncertainty'),'p',siteName(candidates[i])+`: ${fmt(r.unknown_forest_ha)} ha: Unknown-data forest is included in the blind total; it is not proven terrain/canopy obstruction.`)});}
}

// --- Map -----------------------------------------------------------------------
function offset(lat,lon,bearing,metres){const b=bearing*Math.PI/180;return [lat+metres*Math.cos(b)/111320,lon+metres*Math.sin(b)/(111320*Math.cos(lat*Math.PI/180))];}
function renderMap(){
 if(!map||!layers)return;layers.markers.clearLayers();layers.sectors.clearLayers();if(overlay){map.removeLayer(overlay);overlay=null;}
 const revision=++mapRenderRevision,result=results[selected];
 // The other site's field of view is deliberately dashed and unfilled: two coloured
 // coverage rasters would conceal each other where they overlap.
 results.forEach((r,index)=>{if(!r||index===selected)return;r.sectors?.filter(s=>s.active).forEach(s=>L.polygon(s.points,{color:token('--map-sector'),weight:1.5,opacity:.6,fillOpacity:.025,dashArray:'5 6',interactive:false,className:'other-footprint'}).addTo(layers.sectors));});
 if(result){const image=result.images?.[scenario];if(image){
   const rgb=value=>value.match(/[a-f0-9]{2}/gi).map(v=>parseInt(v,16));
   const source=Object.fromEntries(['visible','water'].map(k=>[k,rgb(token('--map-'+k))]));
   const display={visible:rgb(token('--display-visible')),water:rgb(token('--display-water'))};
   MapDisplay.image(image.url,source,display).then(url=>{if(revision!==mapRenderRevision)return;overlay=L.imageOverlay(url,image.bounds,{opacity:1,interactive:false}).addTo(map);}).catch(()=>{if(revision!==mapRenderRevision)return;lastError='Map overlay expired. Recalculate both sites.';state(lastError,true);banner(lastError,'',true);});
  }
  const input=result.input;
  result.sectors?.forEach((s,i)=>{L.polygon(s.points,{color:token(s.active?'--map-sector':'--map-outside'),weight:s.active?1.5:1,opacity:s.active?.9:.55,fillOpacity:0,dashArray:s.active?null:'4 6',interactive:false}).addTo(layers.sectors);
   const cam=input.cameras[i],at=offset(input.lat,input.lon,input.heading+cam.yaw,input.max_range*.62);const label=el('span','sector-label'+(s.active?'':' inactive'),camName(i)+(s.active?'':' · '+tr('disconnected','bağlı değil')));
   L.marker(at,{interactive:false,keyboard:false,icon:L.divIcon({className:'sector-icon',html:label.outerHTML,iconSize:null})}).addTo(layers.sectors)});
 }
 candidates.forEach((c,i)=>{if(!Number.isFinite(c.lat)||!Number.isFinite(c.lon))return;const marker=L.circleMarker([c.lat,c.lon],{radius:i===selected?7:5,color:token('--bg-0'),weight:2,fillColor:i===selected?token('--text'):token('--text-2'),fillOpacity:1}).addTo(layers.markers);
  marker.bindTooltip(letters[i]+' · '+siteName(c),{permanent:true,direction:matchMedia('(max-width:760px)').matches&&i===1?'right':'left',offset:[matchMedia('(max-width:760px)').matches&&i===1?8:-8,0],className:'candidate-label'+(i===selected?' selected':'')}).on('click',()=>selectSite(i,false))});
}
function revealSite(i){if(!map)return;const c=candidates[i];if(!Number.isFinite(c.lat))return;const bounds=L.latLng(c.lat,c.lon).toBounds(2*c.max_range);if(!map.getBounds().contains(bounds))map.fitBounds(bounds,{padding:[24,24],maxZoom:11});}
function render(){renderMap();renderSummary();renderAccounting();renderPairs();renderSensitivity();renderTable();}

// --- Requests ------------------------------------------------------------------
function validateControls(){let valid=true;for(const id of ['lat','lon']){const input=$(id),bad=!input.value||!input.checkValidity();input.setAttribute('aria-invalid',String(bad));$(id+'-error').textContent=bad?(id==='lat'?'Latitude must be between 59° and 62°.':'Longitude must be between 23° and 27°.'):'';if(bad)valid=false;}for(const input of document.querySelectorAll('#result-summary input[type=number]')){const bad=!input.value||!input.checkValidity();input.setAttribute('aria-invalid',String(bad));if(bad)valid=false;}return valid;}
function friendlyError(response,data){if(response.status===429)return 'Analysis rate limit reached. Retry in one minute.';if(response.status===503)return 'An analysis is running or data is unavailable. Retry shortly.';if(response.status===422){if(typeof data?.detail==='string')return data.detail;return 'Check the location, camera angles and model settings.';}return 'Could not calculate visibility. Retry shortly.';}
const pause=ms=>new Promise(done=>setTimeout(done,ms));
async function post(snapshot){
 for(let attempt=0;;attempt++){
  const response=await fetch('/api/analyze',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(snapshot)});let data;try{data=await response.json()}catch{throw Error('Could not calculate visibility. Retry shortly.')}
  // Another visitor holds the single analysis slot: wait as the server asks, then retry.
  if(response.status===503&&attempt<5&&/running/i.test(String(data?.detail))){await pause(1000*Math.min(5,Number(response.headers.get('Retry-After'))||2));continue;}
  if(!response.ok){const error=Error(friendlyError(response,data));error.status=response.status;throw error;}
  return data;
 }
}
async function run(both=true){clearTimeout(timer);if(!map){init();return;}readControls();if(!validateControls()){lastError='Check the highlighted settings.';status(lastError,true);renderSummary();return;}
 const indices=both?[0,1]:[selected];markStale(indices);if(busy){indices.forEach(i=>pending.add(i));return;}await calculate(indices);}
async function calculate(indices){busy=true;setBusy(true);status('Tracing sightlines…');renderSummary();
 const snapshots=indices.map(i=>({...structuredClone(candidates[i]),priority:structuredClone(priority)}));
 try{for(const [k,snapshot] of snapshots.entries()){const i=indices[k],data=await post(snapshot);
   results[i]=data;if(JSON.stringify({...candidates[i],priority})===JSON.stringify(snapshot))dirty.delete(i);
   render();}
  lastError='';banner();render();status('');
 }catch(e){lastError=e instanceof TypeError?'Could not reach the server. Retry shortly.':e.message;status(lastError,true);banner(lastError,results.some(Boolean)?'Results are for previous settings.':'',true);renderSummary();}
 finally{busy=false;setBusy(false);if(pending.size){const next=[...pending];pending.clear();calculate(next);}}
}

// --- Priority drawing --------------------------------------------------------
function updatePriority(){if(priorityLayer){map.removeLayer(priorityLayer);priorityLayer=null;}if(priority)priorityLayer=L.polygon(priority.map(p=>[p[1],p[0]]),{color:token('--accent'),weight:2,fillOpacity:.08,dashArray:'6 4',interactive:false}).addTo(map);$('clear-priority').hidden=!priority;}
function stopDrawing(){drawing=false;drawPoints=[];layers.draw.clearLayers();$('finish').hidden=true;$('draw').textContent='Draw priority forest';$('draw').classList.remove('active');map.doubleClickZoom.enable();document.body.classList.remove('drawing');$('draw-help').hidden=!priority;$('draw-help').textContent=priority?'Priority area included in ranking. Click to move the candidate.':'Click the map to move the selected candidate.';}
function finishDraw(){if(drawPoints.length<3){status('Select at least three points.',true);return;}priority=drawPoints.map(p=>[p.lng,p.lat]);stopDrawing();updatePriority();run(true);}
function toggleDraw(){if(!map)return;if(drawing){stopDrawing();return;}drawing=true;drawPoints=[];map.doubleClickZoom.disable();document.body.classList.add('drawing');$('finish').hidden=false;$('draw').textContent='Cancel drawing';$('draw').classList.add('active');$('draw-help').hidden=false;$('draw-help').textContent='Click area corners. Finish with the button or Enter.';status('Select corners of the priority forest area.');}

// --- Start -------------------------------------------------------------------
function dataSummary(){const pct=dataInfo.assumed_canopy_forest_pct;localized($('data-summary'),`NLS 2019 · CORINE 2024 · Luke MS-NFI 2023 height and cover. ${M.percent(pct,'en',2)} of forest cells use assumed canopy.`,`NLS 2019 · CORINE 2024 · Luke MS-NFI 2023 boy ve taç örtüsü. Orman hücrelerinin ${M.percent(pct,'tr',2)} kadarında varsayılan taç kullanılır.`);}
function mapState(text){$('map-state').hidden=!text;if(text)$('map-state-text').textContent=text;}
async function init(){let initializingMap=null;if(ready)return;ready=true;mapState('Loading regional map…');setBusy(true);
 try{const response=await fetch('/api/config');if(!response.ok)throw Error();const config=await response.json();candidates=config.presets;dataInfo=config.data;showControls();renderSummary();if(!config.ready)throw Error();
  dataSummary();
  const m=initializingMap=L.map('map',{attributionControl:true,zoomControl:false,zoomSnap:.5,zoomAnimation:false,fadeAnimation:false,markerZoomAnimation:false});
  layers={markers:L.layerGroup(),sectors:L.layerGroup(),draw:L.layerGroup()};
  const DrawControl=L.Control.extend({onAdd(){const controls=document.querySelector('.map-toolbar');L.DomEvent.disableClickPropagation(controls);L.DomEvent.disableScrollPropagation(controls);return controls;}});
  new DrawControl({position:'topleft'}).addTo(m);L.control.zoom({zoomInTitle:'Zoom in',zoomOutTitle:'Zoom out',position:'topleft'}).addTo(m);m.attributionControl.setPrefix(false);m.attributionControl.addAttribution('NLS 2019 · Syke 2024 · Luke 2023 | CC BY 4.0');
  const mapResponse=await fetch('/maps/map.json');if(!mapResponse.ok)throw Error();const mapConfig=await mapResponse.json();
  const interior=await MapDisplay.extent('/maps/background.png'),nw=m.project(L.latLng(mapConfig.bounds[1][0],mapConfig.bounds[0][1]),0),se=m.project(L.latLng(mapConfig.bounds[0][0],mapConfig.bounds[1][1]),0);
  const corner=(x,y)=>m.unproject(L.point(nw.x+(se.x-nw.x)*x,nw.y+(se.y-nw.y)*y),0);
  const safeBounds=L.latLngBounds(corner(interior.left,interior.bottom),corner(interior.right,interior.top));
  function constrainView(){const minimum=Math.ceil(m.getBoundsZoom(safeBounds,true)*2)/2;m.stop();m.setMinZoom(minimum);if(Number.isFinite(m.getZoom())){if(m.getZoom()<minimum)m.setZoom(minimum,{animate:false});m.panInsideBounds(safeBounds,{animate:false});}}
  m.options.maxBoundsViscosity=1;m.setMaxBounds(safeBounds);constrainView();
  m.fitBounds(candidates.map(c=>[c.lat,c.lon]),{padding:[60,60],maxZoom:Math.max(m.getMinZoom(),matchMedia('(max-width:760px)').matches?9:10),animate:false});
  const background=L.imageOverlay('/maps/background.png',mapConfig.bounds,{className:'base-map'}).addTo(m);const forests=L.imageOverlay('/maps/forest.png',mapConfig.bounds,{opacity:.45}),waters=L.imageOverlay('/maps/water.png',mapConfig.bounds,{opacity:.45});
  L.control.layers({'Local terrain map':background},{'Forest highlight':forests,'Water highlight':waters},{collapsed:true,position:'topleft'}).addTo(m);L.control.scale({imperial:false,position:'bottomright'}).addTo(m);
  for(const layer of Object.values(layers))layer.addTo(m);
  const labels=[['Helsinki',60.17,24.94],['Espoo',60.205,24.66],['Vantaa',60.294,25.04],['Nuuksio',60.32,24.51,true],['Sipoonkorpi',60.32,25.19,true]];
  labels.filter(([name])=>!candidates.some(c=>siteName(c)===name)).forEach(([name,lat,lon,forest])=>L.marker([lat,lon],{interactive:false,keyboard:false,icon:L.divIcon({className:'map-label'+(forest?' forest-label':''),html:name,iconSize:[100,20]})}).addTo(m));
  m.on('click',e=>{if(drawing){drawPoints.push(e.latlng);layers.draw.clearLayers();L.polyline(drawPoints,{color:token('--accent'),weight:2}).addTo(layers.draw);drawPoints.forEach(p=>L.circleMarker(p,{radius:4,color:token('--accent'),fillColor:token('--bg-0'),fillOpacity:1}).addTo(layers.draw));return;}readControls();candidates[selected].lat=e.latlng.lat;candidates[selected].lon=e.latlng.lng;showControls();run(false)});
  m.on('dblclick',()=>{if(drawing)finishDraw()});
  new ResizeObserver(()=>{m.invalidateSize({pan:false});constrainView();}).observe($('map'));
  map=m;mapState('');render();await run(true);
 }catch{ready=false;const failedMap=map||initializingMap;if(failedMap){const controls=document.querySelector('.map-toolbar');failedMap.remove();if(controls)document.querySelector('.map-shell').append(controls);}map=null;layers=null;mapState('Could not load regional map data. Use Recalculate both sites to retry.');lastError='Could not load regional map data. Use Recalculate both sites to retry.';status(lastError,true);banner(lastError,'',true);renderSummary();setBusy(false);}}

['lat','lon','height','resolution','max-range','smoke-height'].forEach(id=>$(id).addEventListener('change',()=>{readControls();later(300)}));
// Dragging the heading only redraws the sector guide; one analysis runs after release.
$('heading').addEventListener('input',()=>{readControls();markStale();});
$('heading').addEventListener('change',()=>{readControls();later(600)});
$('analyze').addEventListener('click',()=>run(true));$('retry').addEventListener('click',()=>run(true));
$('scenario').addEventListener('change',()=>{scenario=$('scenario').value;render()});
// Reference mode applies to both sites so the verdict always compares like with like.
$('reference').addEventListener('change',()=>{readControls();const on=$('reference').checked;candidates.forEach(c=>{c.reference=on;c.cameras.forEach((cam,i)=>cam.active=on||i<2)});cameraControls();markStale([0,1]);clearTimeout(timer);timer=setTimeout(()=>run(true),300)});
$('draw').addEventListener('click',toggleDraw);$('finish').addEventListener('click',finishDraw);$('clear-priority').addEventListener('click',()=>{priority=null;updatePriority();stopDrawing();run(true)});
document.addEventListener('keydown',e=>{if(drawing&&e.key==='Enter'){finishDraw();return;}if(drawing&&e.key==='Escape'){stopDrawing();return;}
 if(e.metaKey||e.ctrlKey||e.altKey||e.target.closest?.('input,select,textarea'))return;
 if(e.key==='1'||e.key==='2'){selectSite(+e.key-1);e.preventDefault();}else if(e.key==='p'||e.key==='P'){toggleDraw();e.preventDefault();}});
if(matchMedia('(max-width:760px)').matches)$('settings').open=false;
window.addEventListener('languagechange',()=>{if(candidates.length){showControls();render();}if(dataInfo)dataSummary();});
// Panel tabs: Compare (default), Breakdown (table), Data (sources and assumptions).
const tabs=[...document.querySelectorAll('[role=tab]')];
function showTab(tab){tabs.forEach(t=>{const on=t===tab;t.setAttribute('aria-selected',String(on));t.tabIndex=on?0:-1;$(t.getAttribute('aria-controls')).hidden=!on;});}
tabs.forEach((t,i)=>{t.addEventListener('click',()=>showTab(t));t.addEventListener('keydown',e=>{if(e.key==='ArrowRight'||e.key==='ArrowLeft'){const next=tabs[(i+(e.key==='ArrowRight'?1:tabs.length-1))%tabs.length];showTab(next);next.focus();e.preventDefault();}});});
init();
