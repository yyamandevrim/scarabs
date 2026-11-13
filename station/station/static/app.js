'use strict';
const labels = {left:'Sol',centre:'Orta',right:'Sağ'};
const decisions = {pending:'Değerlendirme bekliyor',confirmed:'Operatör doğruladı',rejected:'Operatör reddetti'};
const cameraElements = new Map();
let eventSignature = '';
const text = (tag, value, className) => { const e=document.createElement(tag); e.textContent=value; if(className)e.className=className; return e; };
const num = (value,digits=1) => Number.isFinite(value)?value.toFixed(digits):'—';
async function json(url,options){const r=await fetch(url,options);if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json();}
function cameraCard(camera){
  const card=document.createElement('article');
  const top=text('div','','camera-top');
  top.append(text('h3',`${labels[camera.name]} · ${camera.yaw}°`),text('span','','badge'));
  const wrap=text('div','','image-wrap');
  const image=document.createElement('img');image.alt=`${labels[camera.name]} kamera görüntüsü`;image.hidden=true;
  const placeholder=text('p','','placeholder');wrap.append(image,placeholder);
  const info=text('div','','camera-info');
  card.append(top,wrap,info);document.querySelector('#cameras').append(card);
  const item={card,badge:top.lastChild,image,placeholder,info,busy:false};
  image.onload=()=>{item.busy=false;};image.onerror=()=>{item.busy=false;image.hidden=true;placeholder.hidden=false;placeholder.textContent='Görüntü bekleniyor…';};
  cameraElements.set(camera.name,item);return item;
}
function updateCamera(camera){
  const item=cameraElements.get(camera.name)||cameraCard(camera);
  item.card.className=`camera ${camera.status}`;
  item.badge.className=`badge ${camera.status}`;item.badge.textContent=camera.status_text;
  item.placeholder.hidden=camera.connected;
  item.image.hidden=!camera.connected;
  item.placeholder.textContent=camera.active?'Bağlantı koptu · yeniden deneniyor':'Takılı, bağlı değil · bu giriş etkin değil';
  item.info.replaceChildren(text('p',`Eğim ${camera.tilt}° · Yatay / dikey görüş ${camera.hfov}° / ${camera.vfov}°`));
  if(camera.active){
    item.info.append(text('p',`Ölçülen analiz: ${num(camera.analysis_ms)} ms · çıkarım: ${num(camera.inference_ms)} ms`));
    item.info.append(text('p',`Ölçülen analiz hızı: ${num(camera.analysis_hz,2)} /sn · görüntü hızı: ${num(camera.capture_fps)} kare/sn`));
    if(camera.pipeline_error)item.info.append(text('p','Analiz hatası · yerel günlükleri kontrol edin'));
    if(camera.connected&&!item.busy){item.busy=true;item.image.src=`/api/cameras/${camera.name}/frame.jpg?t=${Date.now()}`;}
  }else{item.info.append(text('p','İki giriş sınırı · etkin kamera çifti yapılandırmadan seçilir'));}
}
async function decide(id,decision,button){
  button.disabled=true;
  try{await json(`/api/events/${id}/decision`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({decision})});eventSignature='';document.querySelector('#action-status').textContent='Karar bu cihazda kaydedildi.';}
  catch(e){document.querySelector('#action-status').textContent='Karar kaydedilemedi. Yeniden deneyin.';}
  finally{button.disabled=false;}
}
function renderEvents(events){
  const signature=JSON.stringify(events);if(signature===eventSignature)return;eventSignature=signature;
  const target=document.querySelector('#events');target.replaceChildren();document.querySelector('#event-count').textContent=events.length;
  if(!events.length){target.append(text('p','Henüz duman şüphesi kaydı yok.','empty'));return;}
  for(const event of events){
    const row=text('article','','event');
    if(event.snapshot){const a=document.createElement('a');a.href=`/events/${event.snapshot}`;a.target='_blank';a.rel='noopener';const img=document.createElement('img');img.src=a.href;img.alt='Duman şüphesi işaretlenmiş olay görüntüsü';a.append(img);row.append(a);}else row.append(text('p','Görüntü kaydı bekleniyor'));
    const content=document.createElement('div');content.append(text('h3','Duman şüphesi'),text('p',`${labels[event.camera]} kamera · ${new Date(event.opened_at*1000).toLocaleString('tr-TR')}`),text('p',`Model güven skoru: %${Math.round(event.confidence*100)} · ${event.closed_at?'gözlem sona erdi':'izleme sürüyor'}`),text('p',`Son gözlem: ${new Date(event.last_seen*1000).toLocaleTimeString('tr-TR')}`));
    if(event.clip){const link=text('a','Olay klibini indir (.avi)');link.href=`/events/${event.clip}`;content.append(link);}else content.append(text('p',event.media_error?'Klip kaydedilemedi':'Olay klibi hazırlanıyor…'));
    const actions=text('div','','actions');actions.append(text('p',decisions[event.decision],'decision'));
    for(const [choice,label]of [['confirmed','Doğrula'],['rejected','Reddet']]){const button=text('button',label,choice==='rejected'?'reject':'');button.addEventListener('click',()=>decide(event.id,choice,button));actions.append(button);}
    row.append(content,actions);target.append(row);
  }
}
async function refresh(){
  try{
    const [status,events]=await Promise.all([json('/api/status'),json('/api/events')]);
    status.cameras.forEach(updateCamera);renderEvents(events);
    document.querySelector('#connection').textContent='Yerel istasyona bağlı · görüntüler saniyede bir yenilenir';
    document.querySelector('#settings').textContent=`Hedef analiz: ${status.target_analysis_hz} /sn/kamera · model girişi ${status.input_size}px`;
  }catch(e){document.querySelector('#connection').textContent='İstasyonla bağlantı koptu · yeniden deneniyor';for(const item of cameraElements.values()){item.image.hidden=true;item.placeholder.hidden=false;item.placeholder.textContent='İstasyonla bağlantı koptu';item.busy=false;}}
  setTimeout(refresh,1000);
}
refresh();
