import {fixture,bearing,encodeSmoke,encodeStatus,yaws,cameraNames} from './radio-packet.js';
const $=id=>document.getElementById(id),ns='http://www.w3.org/2000/svg';
const polar=(angle,r)=>[200+Math.sin(angle*Math.PI/180)*r,200-Math.cos(angle*Math.PI/180)*r];
const svg=(tag,attrs,text)=>{const node=document.createElementNS(ns,tag);for(const [k,v]of Object.entries(attrs))node.setAttribute(k,v);if(text!==undefined)node.textContent=text;return node;};
for(let angle=0;angle<360;angle+=5){const a=polar(angle,158),b=polar(angle,angle%30===0?170:164);$('compass-scale').append(svg('line',{x1:a[0],y1:a[1],x2:b[0],y2:b[1],class:angle%30===0?'major-tick':'minor-tick'}));if(angle%30===0){const p=polar(angle,187);$('compass-scale').append(svg('text',{x:p[0],y:p[1],class:angle%90===0?'cardinal':'degree'},({0:'N',90:'E',180:'S',270:'W'})[angle]||angle+'°'));}}
$('compass-scale').append(svg('circle',{cx:200,cy:200,r:156,class:'compass-ring'}));
for(const [camera,yaw]of Object.entries(yaws)){const a=polar(yaw-60,150),b=polar(yaw+60,150),middle=polar(yaw,100);$('compass-sectors').append(svg('path',{d:`M200 200 L${a} A150 150 0 0 1 ${b} Z`,class:'compass-sector'}),svg('text',{x:middle[0],y:middle[1],class:'sector-name'},cameraNames[camera]));}
let sending=false,sequence=0,rotation=0,received=false,statusCount=0,statusTimer=null,sectionVisible=false;
function preview(){const camera=$('radio-camera').value,bytes=encodeSmoke(camera,sequence),angle=Math.round(bearing(camera))%360;
 $('packet-kind').innerHTML='Smoke suspicion · version 2 · <b>42 bytes</b>';$('packet-bytes-label').textContent='See all 42 bytes';$('packet-layout').textContent='18-byte header + 22-byte smoke body + 2-byte CRC-16';
 const fields=[['Station ID',String(fixture.station)],['Camera',cameraNames[camera]+' · '+(yaws[camera]>0?'+':'')+yaws[camera]+'°'],['Approximate bearing',angle+'°'],['Model score',Math.round(fixture.score*100)+'%'],['Event time',new Date(fixture.timestamp*1000).toISOString().slice(11,19)+' UTC'],['Event UUID',fixture.event]];
 $('packet-fields').replaceChildren(...fields.map(([label,value])=>{const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;row.append(dt,dd);return row;}));
 $('packet-hex').textContent=[...bytes].map(b=>b.toString(16).padStart(2,'0').toUpperCase()).join(' ');return {camera,angle};}
$('radio-camera').addEventListener('change',()=>{$('send-alert').textContent='Spot smoke on '+cameraNames[$('radio-camera').value].toLowerCase();if(received)$('radio-progress').textContent='Station reports continue. Choose a camera to spot smoke.';});
function arrive({camera,angle}){
 sending=false;received=true;$('radio-demo').classList.remove('sending');$('radio-demo').classList.add('received');$('send-alert').disabled=false;$('radio-camera').disabled=false;$('send-alert').textContent='Spot smoke on '+cameraNames[camera].toLowerCase();$('radio-progress').textContent='Smoke report received at the centre. Connect over Wi-Fi to collect its evidence.';$('ground-demo-state').textContent='Station 1 · smoke report received';$('queue-empty').hidden=true;$('demo-alert-count').textContent=String(statusCount+1);
 rotation+=((angle-rotation+540)%360)-180;$('compass-bearing').removeAttribute('hidden');$('compass-bearing').style.transform='rotate('+rotation+'deg)';$('demo-compass').setAttribute('aria-label','Ground azimuth compass, smoke suspicion at approximately '+angle+' degrees');
 const article=document.createElement('article');article.className='demo-alert';const title=document.createElement('h4');title.textContent='Smoke suspicion';const value=document.createElement('p');value.className='alert-bearing';value.textContent='≈ '+angle+'°';const meta=document.createElement('p');meta.textContent=cameraNames[camera]+' · '+Math.round(fixture.score*100)+'% model score';const state=document.createElement('p');state.className='alert-review';state.textContent='Pending station review';const collect=document.createElement('button');collect.id='collect-evidence';collect.textContent='Collect evidence over Wi-Fi';collect.addEventListener('click',()=>{$('radio-evidence').hidden=false;collect.textContent='Evidence collected · Wi-Fi';$('evidence-video').play().catch(()=>{});});article.append(title,value,meta,state,collect);$('demo-alerts').replaceChildren(article);
}
$('send-alert').addEventListener('click',()=>{if(sending)return;sending=true;$('radio-evidence').hidden=true;$('evidence-video').pause();const packet=preview();sequence++;$('send-alert').disabled=true;$('radio-camera').disabled=true;$('radio-progress').textContent='Sending the 42-byte smoke report…';$('ground-demo-state').textContent='Listening for a packet';$('radio-demo').classList.remove('received');$('radio-demo').classList.add('sending');setTimeout(()=>arrive(packet),matchMedia('(prefers-reduced-motion: reduce)').matches?80:1400);});
$('close-evidence').addEventListener('click',()=>{$('radio-evidence').hidden=true;$('evidence-video').pause();$('collect-evidence')?.focus();});
const mediaObserver=new IntersectionObserver(entries=>{for(const entry of entries)if(!entry.isIntersecting)entry.target.pause();},{threshold:.1});mediaObserver.observe($('evidence-video'));document.addEventListener('visibilitychange',()=>{if(document.hidden)$('evidence-video').pause();});
function statusReport(){
 if(sending||document.hidden||!sectionVisible)return;statusCount++;
 const bytes=encodeStatus(sequence++,fixture.timestamp+12*(statusCount-1),100+12*(statusCount-1));
 $('status-report').textContent='Status received · 40 B · report '+statusCount;$('demo-alert-count').textContent=String(statusCount+(received?1:0));
 if(received)return;
 $('packet-kind').innerHTML='Status · version 2 · <b>40 bytes</b>';$('packet-bytes-label').textContent='See all 40 bytes';$('packet-layout').textContent='18-byte header + 20-byte status body + 2-byte CRC-16';
 const fields=[['Station ID','1'],['Process uptime',(100+12*(statusCount-1))+' s'],['Pending review','1 smoke suspicion'],['Camera configuration','Three bearings reported'],['Module heading','0°'],['Next contact window','15 s']];
 $('packet-fields').replaceChildren(...fields.map(([label,value])=>{const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;row.append(dt,dd);return row;}));
 $('packet-hex').textContent=[...bytes].map(b=>b.toString(16).padStart(2,'0').toUpperCase()).join(' ');
}
function syncReports(){clearInterval(statusTimer);if(sectionVisible&&!document.hidden){if(!statusCount)statusReport();statusTimer=setInterval(statusReport,12000);}}
new IntersectionObserver(([entry])=>{sectionVisible=entry.isIntersecting;syncReports();},{threshold:.05}).observe($('radio-demo'));
document.addEventListener('visibilitychange',syncReports);
sectionVisible=true;statusReport();sectionVisible=false;
