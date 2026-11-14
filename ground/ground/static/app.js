'use strict';
let language = localStorage.getItem('acorn-ground-language') || 'en';
let current = null, selectedStation = null, selectedEvent = null, demo = false, updating = false;
let evidenceKey = '', alertSignature = '', feedNames = [], wifiRefreshing = false;
let modeRevision = 0, mediaRevision = 0, modePending = false;
const P=GroundPresentation;
const $ = id => document.getElementById(id);
const strings = {
 en:{lastReportedCameras:'Camera state · last received packet',configuredHeading:'Configured module heading',packetDetails:'Packet details',liveFeeds:'Camera feeds · Wi-Fi',lowBudget:'Last packet reported a low duty budget; current sender state is unknown',scheduled:'Scheduled contact wait',holding:'Calculated duty-cycle wait',nextContact:'Next contact expected within',viewEvidence:'View saved evidence · Wi-Fi',evidenceFor:'Saved evidence for alert',changeLanguage:'Change language',compassLabel:'Station sectors and approximate direction; distance is not measured',ground:'Ground',observation:'Remote observation',enableDemo:'Show Wi-Fi demo',directions:'Approximate directions',directionNote:'Direction from configured heading and camera field of view. No distance or fire location is measured.',alerts:'Received alerts',linkDetails:'Link details · calculated radio values',linkNote:"Airtime uses configured PHY settings. Remaining duty budget is the sender’s calculated value at its latest packet, not a live measurement. Sequence gaps cannot reveal losses before the first packet or after the last. No delivery is guaranteed.",ackNote:'Acknowledgements stay on this laptop. They do not send a decision to the station. Battery: not measured.',demoTitle:'Imagery & evidence · Wi-Fi only',demoNote:'Close-range demo connection. Images and clips are not carried by LoRa.',waiting:'Waiting for a LoRa packet…',empty:'No alerts received. Listening for smoke suspicions and local flame-sensor triggers.',recorded:'Recorded footage',simulated:'Simulated sensor',unknownSource:'Sensor source not reported',smoke:'Smoke suspicion',flame:'Flame-sensor trigger',shortRange:'Local short-range sensor · no camera confirmation',ack:'Acknowledge locally',acked:'Acknowledged locally',collect:'Collect evidence over Wi-Fi',selected:'Show direction',pending:'Pending station review',confirmed:'Station operator: confirmed suspicion',rejected:'Station operator: rejected suspicion',online:'Heard recently',stale:'Stale · station may be unreachable',lost:'Link lost · last received data only',lastHeard:'Last heard',ago:'s ago',station:'Station',left:'Left',centre:'Centre',right:'Right',inactive:'mounted, inactive',connected:'active',disconnected:'lost',unknown:'Camera status not received',confidence:'confidence at alert',box:'Box size',saved:'Evidence saved on this laptop over Wi-Fi',noEvidence:'Select “Collect evidence over Wi-Fi” on a received alert to keep its snapshot and clip here.',wifiError:'Wi-Fi unavailable. Check station address, secret and close-range connection.',collecting:'Collecting evidence over Wi-Fi…',collected:'Evidence saved. Enable the Wi-Fi demo to view it here.',unready:'No evidence ready yet; try again after the clip has finished.',packets:'Packets received',gaps:'Missing sequence numbers',duplicates:'Duplicate datagrams',size:'Last packet size',airtime:'Calculated airtime',budget:'Calculated budget at TX',uptime:'Reported uptime',pendingCount:'Reported pending',unknownValue:'Not received',direction:'Approximate direction',serverLost:'Ground server unavailable · reconnecting',noSectors:'Waiting for camera configuration',sensorOnly:'Local sensor trigger',north:'N',south:'S',east:'E',west:'W',download:'Download clip',snapshot:'Saved snapshot · Wi-Fi',clip:'Saved event clip · Wi-Fi'},
 tr:{lastReportedCameras:'Kamera durumu · son alınan paket',configuredHeading:'Yapılandırılmış modül yönü',packetDetails:'Paket ayrıntıları',liveFeeds:'Kamera görüntüleri · Wi-Fi',lowBudget:'Son pakette yayın bütçesi düşüktü; vericinin güncel durumu bilinmiyor',scheduled:'Planlanan paket bekleniyor',holding:'Hesaplanan görev döngüsü beklemesi',nextContact:'Beklenen sonraki paket en geç',viewEvidence:'Kayıtlı kanıtı göster · Wi-Fi',evidenceFor:'Kanıtın ait olduğu uyarı',changeLanguage:'Dili değiştir',compassLabel:'İstasyon sektörleri ve yaklaşık yön; mesafe ölçülmez',ground:'Yer istasyonu',observation:'Uzaktan gözlem',enableDemo:'Wi-Fi demosunu göster',directions:'Yaklaşık yönler',directionNote:'Yön, yapılandırılmış modül yönü ve kamera görüş açısından hesaplanır. Mesafe veya yangın konumu ölçülmez.',alerts:'Alınan uyarılar',linkDetails:'Bağlantı ayrıntıları · hesaplanan radyo değerleri',linkNote:'Havada kalma süresi, ayarlı radyo parametrelerinden hesaplanır. Kalan yayın bütçesi, vericinin son pakette hesapladığı değerdir; canlı ölçüm değildir. İlk paketten önceki ve son paketten sonraki kayıplar bilinemez. Teslimat garantisi yoktur.',ackNote:'Alındı bilgisi bu bilgisayarda kalır; istasyona karar göndermez. Pil: ölçülmüyor.',demoTitle:'Görüntü ve kayıt · yalnızca Wi-Fi',demoNote:'Yakın mesafe demo bağlantısı. Görüntü ve klipler LoRa ile iletilmez.',waiting:'LoRa paketi bekleniyor…',empty:'Uyarı alınmadı. Duman şüphesi ve yerel alev sensörü tetiklemeleri bekleniyor.',recorded:'Kayıtlı görüntü',simulated:'Simüle edilen sensör',unknownSource:'Sensör kaynağı bildirilmedi',smoke:'Duman şüphesi',flame:'Alev sensörü tetiklendi',shortRange:'Yerel kısa menzilli sensör · kamera doğrulaması değildir',ack:'Yerelde alındı işaretle',acked:'Yerelde alındı',collect:'Kanıtı Wi-Fi ile kaydet',selected:'Yönü göster',pending:'İstasyonda inceleme bekliyor',confirmed:'İstasyon operatörü: şüpheyi doğruladı',rejected:'İstasyon operatörü: şüpheyi reddetti',online:'Yakın zamanda alındı',stale:'Veri eski · istasyona erişilemiyor olabilir',lost:'Bağlantı kayıp · yalnızca son alınan veri',lastHeard:'Son paket',ago:'sn önce',station:'İstasyon',left:'Sol',centre:'Orta',right:'Sağ',inactive:'takılı, bağlı değil',connected:'etkin',disconnected:'bağlantı koptu',unknown:'Kamera durumu alınmadı',confidence:'uyarı anındaki güven',box:'Kutu boyutu',saved:'Kanıt bu bilgisayara Wi-Fi ile kaydedildi',noEvidence:'Görüntü ve klibi saklamak için alınan uyarıda “Kanıtı Wi-Fi ile kaydet” düğmesini kullanın.',wifiError:'Wi-Fi erişilemiyor. İstasyon adresini, parolayı ve yakın bağlantıyı kontrol edin.',collecting:'Kanıt Wi-Fi ile kaydediliyor…',collected:'Kanıt kaydedildi. Görmek için Wi-Fi demosunu açın.',unready:'Kanıt henüz hazır değil; klip tamamlandığında tekrar deneyin.',packets:'Alınan paket',gaps:'Eksik sıra numarası',duplicates:'Yinelenen veri paketi',size:'Son paket boyutu',airtime:'Hesaplanan havada kalma süresi',budget:'Yayında hesaplanan bütçe',uptime:'Bildirilen çalışma süresi',pendingCount:'Bildirilen bekleyen olay',unknownValue:'Alınmadı',direction:'Yaklaşık yön',serverLost:'Yer istasyonu sunucusuna erişilemiyor · yeniden bağlanıyor',noSectors:'Kamera yapılandırması bekleniyor',sensorOnly:'Yerel sensör tetiklemesi',north:'K',south:'G',east:'D',west:'B',download:'Klibi indir',snapshot:'Kaydedilen görüntü · Wi-Fi',clip:'Kaydedilen olay klibi · Wi-Fi'}
};
const t = key => strings[language][key] || key;
const time = epoch => new Date(epoch*1000).toLocaleString(language==='tr'?'tr-TR':'en-GB',{hour:'2-digit',minute:'2-digit',second:'2-digit',day:'2-digit',month:'short'});
function node(tag, text, cls){const e=document.createElement(tag);if(text!==undefined)e.textContent=text;if(cls)e.className=cls;return e;}
async function api(path, options){const r=await fetch(path,options);if(!r.ok)throw Error('Request failed');return r.json();}
function translated(){document.documentElement.lang=language;document.title='ACORN — '+t('ground');document.querySelectorAll('[data-i18n]').forEach(e=>e.textContent=t(e.dataset.i18n));$('language').textContent=language==='en'?'Türkçe':'English';for(const id of ['collection-message','wifi-message']){const element=$(id),key=Object.keys(strings.en).find(key=>Object.values(strings).some(dictionary=>dictionary[key]===element.textContent));if(key)element.textContent=t(key);}alertSignature='';evidenceKey='';feedNames=[];if(current)render();if(demo)void wifi().catch(()=>{});}
$('language').onclick=()=>{language=language==='en'?'tr':'en';localStorage.setItem('acorn-ground-language',language);translated();};
$('station-select').onchange=e=>{selectedStation=Number(e.target.value);selectedEvent=null;alertSignature='';render();};
function station(){return current?.stations.find(s=>s.id===selectedStation);}
function alerts(){return (current?.alerts||[]).filter(a=>a.station===selectedStation);}
function render(){
 $('transport-label').textContent=P.transport(current.transport,language);
 $('transport-label').classList.toggle('lost',!!current.link&&!current.link.ready);
 document.querySelector('.workspace').setAttribute('aria-label',language==='tr'?'LoRa gözlemleri':'LoRa observations');
 $('language').setAttribute('aria-label',t('changeLanguage'));$('station-select').setAttribute('aria-label',t('station'));$('compass').setAttribute('aria-label',t('compassLabel'));
 const all=current.stations;
 if(!all.some(s=>s.id===selectedStation))selectedStation=all[0]?.id??null;
 const select=$('station-select');
 if([...select.options].map(x=>x.value).join(',')!==all.map(s=>String(s.id)).join(',')){select.replaceChildren(...all.map(s=>{const o=node('option',`${t('station')} ${s.id}`);o.value=s.id;return o;}));}
 for(const o of select.options)o.textContent=`${t('station')} ${o.value}`;
 if(selectedStation!==null)select.value=selectedStation;
 const s=station();
 $('station-state').textContent=s?`${t('station')} ${s.id} · ${t(s.state)} · ${t('lastHeard')} ${Math.floor(s.age)} ${t('ago')}`:t('waiting');
 if(['holding','scheduled'].includes(s?.state))$('station-state').textContent+=` · ${t('nextContact')} ${P.number(Math.ceil(s.next_contact_in),language)} ${language==='tr'?'sn':'s'}`;
 if(s?.duty_hint&&!s.contact_after)$('station-state').textContent+=` · ${t('lowBudget')}`;
 $('station-state').className=s?.state||'';
 $('camera-status').replaceChildren();$('camera-status').dataset.label=t('lastReportedCameras');
 $('heading-label').hidden=!s?.status;$('heading-label').textContent=s?.status?`${t('configuredHeading')} ${P.number(s.status.heading_cd/100,language)}°`:'';
 if(s?.status){['left','centre','right'].forEach((name,i)=>{const active=s.status.active&(1<<i),lost=s.status.lost&(1<<i);$('camera-status').append(node('span',`${t(name)} · ${t(!active?'inactive':lost?'disconnected':'connected')}`,lost?'lost':''));});}
 else $('camera-status').append(node('span',t('unknown')));
 const list=alerts();
 if(!list.some(a=>a.event_id===selectedEvent))selectedEvent=list.find(a=>a.kind==='smoke'&&(current.local_evidence||[]).some(e=>e.station===a.station&&e.event_id===a.event_id))?.event_id??list[0]?.event_id??null;
 $('alert-count').textContent=list.length;
 const signature=JSON.stringify([list,current.local_evidence,selectedEvent,language]);
 if(signature!==alertSignature){
 alertSignature=signature;$('alerts').replaceChildren();
 if(!list.length)$('alerts').append(node('p',t('empty'),'empty'));
 const ordered=[...list.filter(a=>a.event_id===selectedEvent),...list.filter(a=>a.event_id!==selectedEvent)];
 ordered.forEach(a=>{const article=node('article',undefined,`alert ${a.event_id===selectedEvent?'selected':''} ${a.decision==='pending'?'pending':'decided'}`);
 article.dataset.eventId=a.event_id;
 article.append(node('h4',t(a.kind==='smoke'?'smoke':'flame'),'alert-title'));
 if(a.recorded)article.append(node('small',t('recorded')));
 if(a.source==='simulated')article.append(node('small',t('simulated')));
 if(a.source==='unknown')article.append(node('small',t('unknownSource')));
 if(a.kind==='smoke'){
 article.append(node('div',P.bearing(a.bearing_cd/100,language),'bearing'));
 article.append(node('div',`${t(['left','centre','right'][a.camera])} · ${P.percent(a.confidence,language)} ${t('confidence')}`,'alert-meta'));

 }else article.append(node('p',t('shortRange'),'alert-meta'));
 const when=node('time',time(a.timestamp));when.dateTime=new Date(a.timestamp*1000).toISOString();article.append(when,node('span',t(a.decision),`alert-state ${a.decision==='pending'?'pending':''}`));
 const packet=node('details',undefined,'alert-details');packet.append(node('summary',t('packetDetails')));
 if(a.kind==='smoke')packet.append(node('p',`${t('box')}: ${P.percent(a.width/255*100,language)} × ${P.percent(a.height/255*100,language)}`));
 packet.append(node('p',a.event_id,'event-id'));article.append(packet);
 const actions=node('div',undefined,'alert-actions');
 if(a.kind==='smoke'&&a.event_id!==selectedEvent){const b=node('button',t('selected'));b.onclick=()=>{selectedEvent=a.event_id;render();evidenceKey='';};actions.append(b);}
 if(a.acknowledged_at)actions.append(node('small',t('acked')));
 else {const b=node('button',t('ack'));b.onclick=async()=>{await api(`/api/alerts/${a.station}/${a.event_id}/ack`,{method:'POST'});await refresh();};actions.append(b);}
 const saved=(current.local_evidence||[]).find(e=>e.station===a.station&&e.event_id===a.event_id);
 if(saved){article.append(node('small',t('saved')));const view=node('button',t('viewEvidence'));view.onclick=async()=>{selectedEvent=a.event_id;evidenceKey='';$('demo-toggle').checked=true;await setDemo(true);render();};actions.append(view);}
 if(a.kind==='smoke'){const collect=node('button',t('collect'));collect.onclick=async()=>{collect.disabled=true;$('collection-message').textContent=t('collecting');try{const result=await api(`/api/evidence/${a.station}/${a.event_id}/collect`,{method:'POST'});selectedEvent=a.event_id;evidenceKey='';$('collection-message').textContent=t(result.files.length?(demo?'saved':'collected'):'unready');await refresh();if(demo)await evidence();}catch{$('collection-message').textContent=t('wifiError');}finally{collect.disabled=false;}};actions.append(collect);}article.append(actions);$('alerts').append(article);});
 }
 $('link-details').replaceChildren();
 const metrics=s?[[t('packets'),s.packets],[t('gaps'),s.missed],[t('duplicates'),s.duplicates],[t('size'),`${s.last_size} B`],[t('airtime'),`${P.number(s.airtime*1000,language,1)} ms`],[t('budget'),`${s.remaining===undefined?'—':P.number(s.remaining,language,2)} s`],[t('uptime'),s.status?`${s.status.uptime} s`:t('unknownValue')],[t('pendingCount'),s.status?.pending??t('unknownValue')]]:[];
 metrics.forEach(([label,value])=>{const e=node('div',undefined,'metric');e.append(node('span',label),node('strong',String(value)));$('link-details').append(e);});draw();
}
function draw(){
 const canvas=$('compass'),rect=canvas.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,2);
 canvas.width=rect.width*dpr;canvas.height=rect.height*dpr;
 const ctx=canvas.getContext('2d');ctx.scale(dpr,dpr);
 const w=rect.width,h=rect.height,cx=w/2,cy=h/2,r=Math.min(w/2-42,h/2-48);
 if(r<1)return;
 const polar=(angle,rad)=>[cx+Math.sin(angle*Math.PI/180)*rad,cy-Math.cos(angle*Math.PI/180)*rad];
 const line=(angle,from,to)=>{const a=polar(angle,from),b=polar(angle,to);ctx.beginPath();ctx.moveTo(...a);ctx.lineTo(...b);ctx.stroke();};
 ctx.textAlign='center';ctx.textBaseline='middle';ctx.lineWidth=1;
 // Only an azimuth scale: concentric range rings would suggest an unmeasured distance.
 ctx.beginPath();ctx.arc(cx,cy,r,0,2*Math.PI);ctx.strokeStyle='#33475a';ctx.stroke();
 for(let deg=0;deg<360;deg+=5){ctx.strokeStyle=deg%30===0?'#a7b4bf':'#33475a';line(deg,r+2,r+(deg%30===0?13:6));}
 ctx.font='12px "IBM Plex Sans"';
 for(let deg=0;deg<360;deg+=30){if(deg%90){const p=polar(deg,r+29);ctx.fillStyle='#a7b4bf';ctx.fillText(`${deg}°`,...p);}}
 ctx.font='500 14px "IBM Plex Sans"';
 [[0,t('north')],[90,t('east')],[180,t('south')],[270,t('west')]].forEach(([deg,label])=>{ctx.fillStyle='#e3e9ee';ctx.fillText(label,...polar(deg,r+29));});
 const s=station();
 if(s?.status){
  const st=s.status;
  ['left','centre','right'].forEach((name,i)=>{
   const heading=st.heading_cd/100+st.yaw[i]/100,half=st.hfov[i]/2,active=st.active&(1<<i),lost=st.lost&(1<<i);
   ctx.beginPath();ctx.moveTo(cx,cy);ctx.arc(cx,cy,r-9,(heading-half-90)*Math.PI/180,(heading+half-90)*Math.PI/180);ctx.closePath();
   ctx.fillStyle=lost?'#f0594e0c':active?'#8fc3e312':'#8697a505';ctx.fill();
   ctx.strokeStyle=lost?'#f0594e':active?'#8fc3e359':'#33475a';ctx.setLineDash(active&&!lost?[]:[4,5]);ctx.stroke();ctx.setLineDash([]);
   ctx.fillStyle=lost?'#f0594e':active?'#a7b4bf':'#8697a5';ctx.font='13px "IBM Plex Sans"';ctx.fillText(t(name),...polar(heading,r*.63));
  });
  // Short, quiet arrow is the configured module heading, never a compass measurement.
  const heading=st.heading_cd/100,tip=polar(heading,31),left=polar(heading-145,10),right=polar(heading+145,10);
  ctx.beginPath();ctx.moveTo(...tip);ctx.lineTo(...left);ctx.lineTo(...right);ctx.closePath();ctx.fillStyle='#e3e9ee';ctx.fill();
 }
 else{ctx.fillStyle='#a7b4bf';ctx.font='13px "IBM Plex Sans"';ctx.fillText(t('noSectors'),cx,cy+r*.5);}
 const a=alerts().find(a=>a.event_id===selectedEvent);
 if(a?.kind==='smoke'){
  const angle=(Math.round(a.bearing_cd/100)%360),point=polar(angle,r-9),colour=a.decision==='rejected'?'#a7b4bf':'#f2a93b';
  ctx.strokeStyle=colour;ctx.lineWidth=2;line(angle,15,r-9);ctx.lineWidth=1;
  ctx.beginPath();ctx.arc(...point,5,0,Math.PI*2);ctx.fillStyle=colour;ctx.fill();
  const p=polar(angle,r*.43);ctx.font='500 16px "IBM Plex Sans"';ctx.fillText(P.bearing(angle,language),p[0]+(p[0]<cx?-24:24),p[1]+22);
 }
 ctx.beginPath();ctx.arc(cx,cy,5,0,2*Math.PI);ctx.fillStyle='#e3e9ee';ctx.fill();
 ctx.font='13px "IBM Plex Sans"';ctx.fillStyle='#e3e9ee';ctx.fillText(s?`${t('station')} ${s.id}`:'ACORN',cx,cy+48);

}
function applyDemo(enabled){
 if(demo!==enabled)mediaRevision++;
 demo=enabled;$('demo-toggle').checked=demo;$('demo').hidden=!demo;
 $('workspace').classList.toggle('with-wifi',demo);draw();
 if(!demo){$('live-feeds').replaceChildren();$('evidence').replaceChildren();feedNames=[];evidenceKey='';}
}
async function setDemo(enabled){
 const revision=++modeRevision;modePending=true;applyDemo(false);
 try{
  const result=await api('/api/demo',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled})});
  if(revision!==modeRevision)return;
  applyDemo(result.enabled===true);
 }catch(error){if(revision===modeRevision)applyDemo(false);throw error;}
 finally{if(revision===modeRevision){modePending=false;modeRevision++;}}
 if(demo)await wifi();
}
$('demo-toggle').onchange=async e=>{try{await setDemo(e.target.checked);}catch{$('station-state').textContent=t('serverLost');}};
async function evidence(){if(!demo||!selectedEvent)return;const sid=selectedStation,eid=selectedEvent,revision=mediaRevision;const key=`${sid}/${eid}/${language}`;if(evidenceKey===key)return;const saved=await api(`/api/evidence/${sid}/${eid}`);if(!demo||revision!==mediaRevision||sid!==selectedStation||eid!==selectedEvent)return;evidenceKey=key;const area=$('evidence');area.replaceChildren(node('p',`${t('evidenceFor')}: ${time(alerts().find(a=>a.event_id===eid)?.timestamp||0)} · ${eid.slice(0,8)}`),node('p',saved.files.length?t('saved'):t('noEvidence')));const identity=node('details',undefined,'alert-details');identity.append(node('summary',t('packetDetails')),node('p',eid,'event-id'));area.append(identity);const media=node('div',undefined,'media');for(const file of [...saved.files].sort((a,b)=>Number(b.endsWith('.webm'))-Number(a.endsWith('.webm')))){const figure=node('figure');const url=`/api/evidence/${sid}/${eid}/${file}`;figure.append(node('figcaption',t(file.endsWith('.jpg')?'snapshot':'clip')));if(file.endsWith('.jpg')){const img=node('img');img.src=url;img.alt=t('snapshot');figure.append(img);}else if(file.endsWith('.webm')){const video=node('video');video.controls=true;video.preload='metadata';video.src=url;figure.append(video);}const a=node('a',t('download'));a.href=url;a.download=file;if(!file.endsWith('.jpg'))figure.append(a);if(file.endsWith('.jpg')){const disclosure=node('details');disclosure.append(node('summary',t('snapshot')),figure);media.append(disclosure);}else media.append(figure);}area.append(media);}
async function updateWifi(){if(!demo)return;const revision=mediaRevision;if(!document.querySelector('.wifi-feeds').open){await evidence();return;}try{const data=await api('/api/demo/status');if(!demo||revision!==mediaRevision)return;const names=data.cameras.filter(c=>c.active).map(c=>c.name);if(names.join()!==feedNames.join()){$('live-feeds').replaceChildren();feedNames=names;for(const name of names){const figure=node('figure');figure.append(node('figcaption',`${t('station')} ${data.wifi_station_id} · ${t(name)} · Wi-Fi${data.cameras.find(c=>c.name===name).kind==='file'?' · '+t('recorded'):''}`));const img=node('img');img.id=`live-${name}`;img.alt=`${t(name)} · Wi-Fi`;figure.append(img);$('live-feeds').append(figure);}}for(const name of names)$(`live-${name}`).src=`/api/demo/cameras/${name}.jpg?t=${Date.now()}`;if($('wifi-message').textContent===t('wifiError'))$('wifi-message').textContent='';}catch{if(demo&&revision===mediaRevision){$('wifi-message').textContent=t('wifiError');applyDemo(false);}return;}if(demo&&revision===mediaRevision)await evidence();}
async function wifi(){
 if(!demo||wifiRefreshing)return;
 const revision=mediaRevision;wifiRefreshing=true;
 try{await updateWifi();}
 catch{if(revision===mediaRevision){$('wifi-message').textContent=t('wifiError');applyDemo(false);}}
 finally{wifiRefreshing=false;}
}
async function refresh(){
 if(updating)return;
 updating=true;const revision=modeRevision;
 try{
  const [state,mode]=await Promise.all([
   api('/api/state'),
   api('/api/demo').then(mode=>{
    // A pre-POST poll cannot overwrite the result of that newer mutation.
    // Apply off immediately, even if the independent packet-state read is slow.
    if(revision===modeRevision&&!modePending&&mode.enabled!==true)applyDemo(false);
    return mode;
   })
  ]);
  current=state;render();
  if(revision===modeRevision&&!modePending){applyDemo(mode.enabled===true);void wifi();}
 }catch{
  if(revision===modeRevision&&!modePending)applyDemo(false);
  $('station-state').textContent=t('serverLost');$('station-state').className='lost';
 }finally{updating=false;}
}
document.querySelector('.wifi-feeds').addEventListener('toggle',()=>{if(demo)wifi();});
window.addEventListener('resize',draw);translated();void refresh();setInterval(refresh,1500);
