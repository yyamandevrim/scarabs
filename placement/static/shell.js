'use strict';
// Shared shell behaviour: the browser-time clock and health chip states.
(function(root){
 function startClock(element,locale){
  if(!element)return;
  const tick=()=>{const now=new Date();element.textContent=now.toLocaleTimeString(typeof locale==='function'?locale():locale,{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false});};
  tick();
  // Align to the second boundary; one cheap text update per second.
  setTimeout(()=>{tick();setInterval(tick,1000);},1000-new Date().getMilliseconds());
 }
 function health(item,state,value){
  if(!item)return;
  const dot=item.querySelector('.dot');item.classList.toggle('fail',state==='fail');item.classList.toggle('smoke',state==='smoke');
  if(dot)dot.className='dot'+(state?' '+state:'');
  const v=item.querySelector('.v');if(v&&value!==undefined)v.textContent=value;
 }
 root.AcornShell={startClock,health};
})(globalThis);
