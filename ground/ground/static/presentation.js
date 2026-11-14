'use strict';
(function(root){
 const number=(value,lang='en',digits=0)=>new Intl.NumberFormat(lang==='tr'?'tr-TR':'en-GB',{maximumFractionDigits:digits}).format(value);
 const percent=(value,lang)=>lang==='tr'?'%'+number(value,lang):number(value,lang)+'%';
 const bearing=(degrees,lang)=>`≈ ${number((Math.round(degrees)%360+360)%360,lang)}°`;
 const transport=(label,lang)=>lang!=='tr'?label:label==='LoRa link (simulated transport)'?'LoRa bağlantısı (simüle edilen iletim)':label==='LoRa link (serial adapter unimplemented / untested)'?'LoRa bağlantısı (seri bağdaştırıcı uygulanmadı / test edilmedi)':label;
 root.GroundPresentation={number,percent,bearing,transport};
})(globalThis);
