'use strict';
const stationTitle = document.title;
const labels = {left: 'Sol', centre: 'Orta', right: 'Sağ'};
const decisions = {confirmed: 'Operatör doğruladı', rejected: 'Operatör reddetti'};
const cameraElements = new Map();
const eventElements = new Map();
const editing = new Set();
let online = false;
let currentStatus = null;
let currentEvents = [];
let lastUpdate = null;
let refreshing = false;
let showOlderPending = false;
let decisionRevision = 0;
const $ = selector => document.querySelector(selector);
const text = (tag, value, className) => {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
};
const num = (value, digits = 1) => Number.isFinite(value)
  ? value.toLocaleString('tr-TR', {minimumFractionDigits: digits, maximumFractionDigits: digits}).replace('-', '−') : '—';
const time = value => value ? new Date(value * 1000).toLocaleTimeString('tr-TR') : '—';
const dateTime = value => new Date(value * 1000).toLocaleString('tr-TR', {day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'});
async function json(url, options = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch(url, {...options, signal: controller.signal});
    if (response.status === 401) { window.location.assign('/login'); throw new Error('Login required'); }
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return await response.json();
  } finally { clearTimeout(timeout); }
}
function cameraCard(camera) {
  const card = text('article', '', 'camera');
  const top = text('div', '', 'camera-top');
  const title = text('h3', '');
  const state = text('span', '', 'camera-state');
  top.append(title, state);
  const wrap = text('div', '', 'image-wrap');
  const image = document.createElement('img');
  image.alt = `${labels[camera.name]} kamera görüntüsü`;
  image.hidden = true;
  const placeholder = text('p', 'Görüntü bekleniyor…', 'placeholder');
  wrap.append(image, placeholder);
  const source = text('p', '', 'source-label');
  const info = text('div', '', 'camera-info');
  card.append(top, wrap, source, info);
  const item = {card, title, state, image, placeholder, source, info, busy: false, frameFailed: false, camera};
  image.onload = () => {
    item.busy = false;
    if (!online || !item.camera.connected) return;
    const recovered = item.frameFailed;
    item.frameFailed = false;
    image.hidden = false;
    placeholder.hidden = true;
    if (recovered) updateCamera(item.camera, false);
    updateCoverage();
  };
  image.onerror = () => {
    item.busy = false;
    if (!online || !item.camera.connected) return;
    item.frameFailed = true;
    updateCamera(item.camera, false);
    updateCoverage();
  };
  cameraElements.set(camera.name, item);
  return item;
}
function updateCamera(camera, requestFrame = true) {
  const item = cameraElements.get(camera.name) || cameraCard(camera);
  item.camera = camera;
  const connected = online && camera.connected && !item.frameFailed;
  const suspicion = currentEvents.filter(event => event.camera === camera.name && !event.closed_at);
  item.card.className = `camera${!online ? ' unavailable' : !connected ? ' disconnected' : ''}${online && suspicion.length ? ' suspected' : ''}`;
  item.title.textContent = `${labels[camera.name]} · ${num(camera.yaw, 0)}°`;
  item.state.textContent = !online ? 'Durum bilinmiyor' : !connected ? 'Bağlantı koptu' : suspicion.length
    ? `Duman şüphesi · %${Math.round(Math.max(...suspicion.map(event => event.confidence)) * 100)}` : 'Görüntü alınıyor';
  item.source.textContent = camera.kind === 'file' ? 'Kayıtlı demo · yerel analiz' : 'Canlı kamera · yerel analiz';
  if (!connected) {
    item.image.hidden = true;
    item.image.removeAttribute('src');
    item.busy = false;
    item.placeholder.hidden = false;
    item.placeholder.textContent = online ? 'Görüntü alınamıyor · yeniden deneniyor' : 'İstasyon verisi bekleniyor…';
  }
  item.info.replaceChildren();
  if (connected && !camera.pipeline_error) {
    const device = currentStatus?.measured_on?.board_model || currentStatus?.measured_on?.cpu_model;
    item.info.append(text('span', device ? `Ölçülen · ${device}` : 'Ölçülen', 'metric-label'));
    const values = text('p', '', 'metric-values');
    const measured = camera.analyses > 0;
    for (const value of [
      `Analiz ${num(measured ? camera.analysis_ms : null)} ms`,
      `çıkarım ${num(measured ? camera.inference_ms : null)} ms`,
      `${num(measured ? camera.analysis_hz : null, 2)} analiz/sn`,
      `${num(camera.capture_fps)} kare/sn`
    ]) values.append(text('span', value));
    item.info.append(values);
  } else {
    item.info.append(text('p', camera.pipeline_error && online ? 'Analiz kullanılamıyor · yerel günlükleri kontrol edin' : 'Ölçülen · —', camera.pipeline_error && online ? 'pipeline-error' : ''));
  }
  if (online && camera.connected && requestFrame && !item.busy) {
    item.busy = true;
    item.image.src = `/api/cameras/${camera.name}/frame.jpg?t=${Date.now()}`;
  }
  return item;
}
function updateCoverage() {
  if (!online || !currentStatus) return;
  const active = currentStatus.cameras.filter(camera => camera.active);
  const receiving = active.filter(camera => camera.connected && !cameraElements.get(camera.name)?.frameFailed);
  $('#coverage').textContent = `${receiving.length}/${active.length} etkin giriş görüntü alıyor`;
  const warning = $('#system-warning');
  const failed = active.filter(camera => !receiving.includes(camera));
  const pipelineFailed = receiving.filter(camera => camera.pipeline_error);
  warning.hidden = !failed.length && !pipelineFailed.length && active.length > 0;
  if (!warning.hidden) {
    const title = !receiving.length ? 'Gözlem kullanılamıyor' : failed.length ? 'Gözlem kapsamı azaldı' : 'Analiz kesintisi';
    const reason = failed.length ? `${failed.map(camera => labels[camera.name]).join(', ')} kamera bağlantısı koptu. Yeniden deneniyor.`
      : pipelineFailed.length ? `${pipelineFailed.map(camera => labels[camera.name]).join(', ')} kamerada görüntü var; duman analizi çalışmıyor.` : 'Etkin kamera girişi yok.';
    warning.replaceChildren(text('strong', `${title} · ${receiving.length}/${active.length} giriş`), text('span', reason));
  }
}
function renderStatus(status) {
  const active = status.cameras.filter(camera => camera.active);
  $('#cameras').querySelectorAll('.loading').forEach(element => element.remove());
  for (const [name, item] of cameraElements) {
    if (!active.some(camera => camera.name === name)) { item.card.remove(); cameraElements.delete(name); }
  }
  for (const camera of active) {
    const item = updateCamera(camera);
    if (item.card.parentNode !== $('#cameras')) $('#cameras').append(item.card);
  }
  $('#cameras').setAttribute('aria-busy', 'false');
  $('#inactive-cameras').replaceChildren(...status.cameras.filter(camera => !camera.active)
    .map(camera => text('p', `${labels[camera.name]} · ${num(camera.yaw, 0)}° · takılı, bağlı değil`)));
  $('#geometry').replaceChildren(...status.cameras.map(camera => text('p',
    `${labels[camera.name]}: eğim ${num(camera.tilt, 0)}° · yatay/dikey görüş ${num(camera.hfov, 0)}° / ${num(camera.vfov, 0)}°`)));
  $('#settings').textContent = `Yapılandırılan hedef: ${num(status.target_analysis_hz, 0)} analiz/sn/kamera · model girişi ${status.input_size}px. Giriş çifti yapılandırmadan seçilir.`;
  renderModule(status.mcu);
  $('#measured-on').textContent = status.measured_on?.label || 'Ölçüm cihazı bilgisi alınamadı';
  updateCoverage();
}
function renderModule(mcu) {
  const sensor = mcu?.flame_sensor;
  const state = $('#flame-status');
  $('#mcu-mode').textContent = mcu?.simulated ? 'Simülasyon' : mcu?.mode === 'off' ? 'Yapılandırılmamış' : '';
  state.textContent = sensor?.status_text || 'Alev sensörü durumu bilinmiyor';
  state.className = sensor?.triggered ? 'triggered' : sensor?.configured && !sensor.connected ? 'lost' : '';
  $('#flame-note').textContent = sensor?.note || 'Modüldeki kısa menzilli kızılötesi sensör. Kamera duman şüphesini doğrulamaz.';
  const shown = mcu?.led?.shown;
  const colours = {green: 'Yeşil', amber: 'Kehribar', blue: 'Mavi', red: 'Kırmızı', 'red→green→blue': 'Kırmızı → yeşil → mavi'};
  const patterns = {steady: 'sabit', 'double blink every 1.2 s': '1,2 sn’de çift yanıp sönme', 'slow blink, 1 s on / 1 s off': '1 sn açık / 1 sn kapalı', 'fast blink, 5 per second': 'saniyede 5 kez yanıp sönme', 'short flash every 2 s': '2 sn’de kısa yanıp sönme', 'one 0.75 s lamp test at power-up': 'başlangıçta 0,75 sn lamba testi'};
  $('#led-status').textContent = shown ? `Durum LED’i: ${colours[shown.colour] || shown.colour || '—'} · ${patterns[shown.pattern] || shown.pattern || '—'} · ${shown.text}` : 'Durum LED’i: okunamıyor';
  $('#sensor-reading').textContent = sensor?.connected && Number.isFinite(sensor.level_permille) ? `Bağıl kızılötesi düzeyi: ${num(sensor.level_permille, 0)}/1000 · kalibre edilmemiştir; mesafe veya alev boyutu değildir.` : '';
  $('#led-requested').textContent = mcu?.led?.requested ? `İstasyonun istediği LED durumu: ${mcu.led.requested.text}. Yukarıdaki durum mikrodenetleyiciden okunur.` : '';
}
function eventRow(event) {
  const row = text('details', '', 'event');
  const summary = document.createElement('summary');
  summary.className = 'event-summary';
  row.append(summary);
  row.dataset.eventId = event.id;
  const title = text('h3', '');
  const meta = text('p', '', 'event-meta');
  const evidence = text('a', '', 'evidence');
  evidence.target = '_blank'; evidence.rel = 'noopener';
  const image = document.createElement('img');
  image.alt = 'Duman şüphesi işaretlenmiş olay görüntüsü';
  image.loading = 'lazy';
  evidence.append(image);
  const player = text('div', '', 'clip-player');
  const video = document.createElement('video');
  video.controls = true;
  video.muted = true;
  video.playsInline = true;
  video.preload = 'none';
  video.setAttribute('aria-label', 'Duman şüphesi olay klibi');
  video.addEventListener('error', () => {
    // A decoder that refuses the clip falls back to the snapshot and download.
    item.playbackFailed = video.getAttribute('src');
    renderClip(item, item.event);
  });
  row.addEventListener('toggle', () => {
    if (row.open && video.preload !== 'metadata') video.preload = 'metadata';
  });
  player.append(video);
  player.hidden = true;
  const noImage = text('p', 'Görüntü kaydı bekleniyor…', 'event-detail');
  const detail = text('p', '', 'event-detail');
  const clipBar = text('div', '', 'clip-bar');
  const clipLabel = text('span', '', 'clip-label');
  const clip = text('a', '', 'evidence-link');
  clipBar.append(clipLabel, clip);
  const clipStatus = text('p', '', 'event-detail clip-status');
  const actions = text('div', '', 'actions');
  summary.append(title, meta);
  const body = text('div', '', 'event-body');
  body.append(player, evidence, noImage, clipBar, clipStatus, detail, actions);
  row.append(body);
  const item = {row, title, meta, player, video, evidence, image, noImage, detail, clipBar, clipLabel, clip, clipStatus, actions, event, playbackFailed: null, mode: '', saving: false, savedUntil: 0};
  eventElements.set(event.id, item);
  return item;
}
function sourceLabel(event) {
  const camera = currentStatus?.cameras.find(candidate => candidate.name === event.camera);
  return (event.source_kind || camera?.kind) === 'usb' ? 'Kamera kaydı' : (event.source_kind || camera?.kind) === 'file' ? 'Kayıtlı demo' : 'Olay kaydı';
}
function renderClip(item, event) {
  const clipUrl = event.clip ? `/events/${event.clip}` : null;
  const extension = event.clip?.split('.').pop();
  // WebM/VP8 plays inline; legacy or fallback AVI stays a download beside the snapshot.
  const playable = extension === 'webm' && item.playbackFailed !== clipUrl && item.video.canPlayType('video/webm; codecs="vp8"') !== '';
  const snapshotUrl = event.snapshot ? `/events/${event.snapshot}` : null;
  item.player.hidden = !playable;
  item.evidence.hidden = playable || !snapshotUrl;
  item.noImage.hidden = playable || !!snapshotUrl;
  if (snapshotUrl) {
    item.evidence.setAttribute('href', snapshotUrl);
    if (item.image.getAttribute('src') !== snapshotUrl) item.image.src = snapshotUrl;
    if (item.video.getAttribute('poster') !== snapshotUrl) item.video.setAttribute('poster', snapshotUrl);
  }
  if (playable) {
    // Polling must never restart a clip the operator is watching.
    if (item.video.getAttribute('src') !== clipUrl) item.video.setAttribute('src', clipUrl);
  } else if (item.video.getAttribute('src')) {
    item.video.pause?.();
    item.video.removeAttribute('src');
  }
  item.clipBar.hidden = !clipUrl;
  if (clipUrl) {
    item.clipLabel.textContent = `${sourceLabel(event)} · olay klibi`;
    item.clip.textContent = `İndir (.${extension})`;
    item.clip.setAttribute('href', clipUrl);
    item.clip.setAttribute('download', event.clip);
  }
  item.clipStatus.classList.remove('error');
  if (!clipUrl) {
    item.clipStatus.textContent = event.media_error ? 'Klip kaydedilemedi · işaretli görüntü yukarıda' : 'Olay klibi hazırlanıyor…';
    item.clipStatus.classList.toggle('error', !!event.media_error);
  } else if (playable) {
    item.clipStatus.textContent = '';
  } else if (extension === 'webm') {
    item.clipStatus.textContent = 'Bu tarayıcı klibi oynatamıyor · işaretli görüntü gösteriliyor, klip indirilebilir';
  } else {
    item.clipStatus.textContent = 'Bu klip tarayıcıda oynatılamaz (.avi) · işaretli görüntü gösteriliyor, klip indirilip yerel oynatıcıda açılabilir';
  }
  item.clipStatus.hidden = !item.clipStatus.textContent;
}
function renderActions(item, event) {
  const mode = event.decision === 'pending' || editing.has(event.id) ? 'editing' : 'decided';
  const signature = `${mode}:${event.decision}:${event.decided_at}`;
  if (item.mode === signature) return;
  item.mode = signature;
  item.actions.replaceChildren();
  item.actions.append(text('p', mode === 'editing' ? 'Karar bekliyor' : `${decisions[event.decision]} · ${time(event.decided_at)}`, 'decision'));
  if (mode === 'editing') {
    for (const [choice, label] of [['confirmed', 'Doğrula'], ['rejected', 'Reddet']]) {
      const button = text('button', label, choice === 'rejected' ? 'reject' : 'confirm');
      button.type = 'button';
      button.addEventListener('click', () => decide(event.id, choice));
      item.actions.append(button);
    }
    if (event.decision !== 'pending') {
      item.actions.firstChild.textContent = 'Kararı değiştir';
      const cancel = text('button', 'Vazgeç', 'cancel');
      cancel.type = 'button';
      cancel.onclick = () => { editing.delete(event.id); renderEvents(currentEvents, true); item.actions.querySelector('button')?.focus(); };
      item.actions.append(cancel);
    }
  } else {
    const change = text('button', 'Değiştir', 'change');
    change.type = 'button';
    change.setAttribute('aria-label', `${labels[event.camera]} kamera kararını değiştir`);
    change.onclick = () => { editing.add(event.id); renderEvents(currentEvents, true); item.actions.querySelector('button')?.focus(); };
    item.actions.append(change);
  }
  const message = text('p', '', 'inline-status');
  message.setAttribute('role', 'status');
  if (item.savedUntil > Date.now()) message.textContent = 'Bu cihazda kaydedildi.';
  item.actions.append(message);
}
let queuePointerInside = false;
let queuedEvents = null;
const queuePanel = $('#event-panel');
function queueIsEngaged() { return queuePointerInside || queuePanel.contains(document.activeElement); }
function flushQueue() {
  if (queuedEvents && online && !queueIsEngaged()) { const events=queuedEvents;queuedEvents=null;renderEvents(events); }
}
queuePanel.addEventListener('pointerenter', () => { queuePointerInside=true; });
queuePanel.addEventListener('pointerleave', () => { queuePointerInside=false;flushQueue(); });
queuePanel.addEventListener('focusout', () => { queueMicrotask(flushQueue); });
function renderEvents(events, deliberate=false) {
  if (!deliberate && eventElements.size && queueIsEngaged()) {
    queuedEvents=events;
    const arrivals=events.filter(event=>event.decision==='pending'&&!eventElements.has(event.id)).length;
    $('#queue-arrivals').hidden=!arrivals;
    $('#queue-arrivals').textContent=`${arrivals} yeni kayıt · listeden ayrıldığınızda gösterilecek`;
    return;
  }
  queuedEvents=null;
  $('#queue-arrivals').hidden=true;
  const pending = events.filter(event => event.decision === 'pending').sort((a,b)=>b.opened_at-a.opened_at);
  const history = events.filter(event => event.decision !== 'pending');
  $('#event-count').textContent = `${pending.length} karar bekliyor`;
  $('#event-count').classList.toggle('has-pending', pending.length > 0);
  $('#pending-summary').textContent = 'Kayıtları incele';
  $('#pending-summary').classList.remove('has-pending');
  document.title = pending.length ? `(${pending.length}) Duman şüphesi — ${[...new Set(pending.map(event => labels[event.camera]))].join(', ')} — ${stationTitle}` : stationTitle;
  $('#events').querySelectorAll('.empty').forEach(element => element.remove());
  for (const [id, item] of eventElements) {
    if (!events.some(event => event.id === id)) { item.row.remove(); eventElements.delete(id); editing.delete(id); }
  }
  for (const event of [...pending, ...history]) {
    const isNew = !eventElements.has(event.id);
    const item = eventElements.get(event.id) || eventRow(event);
    const isPending = event.decision === 'pending';
    item.row.className = `event ${isPending ? 'pending' : editing.has(event.id) ? 'editing' : 'decided'}`;
    if (isNew && isPending && pending.indexOf(event) === 0 && ![...eventElements.values()].some(other => other !== item && other.row.open)) item.row.open = true;
    if (item.row.classList.contains('decided') && !item.video.paused) item.video.pause?.();
    const position = isPending && event === pending[0] ? 'En yeni · ' : isPending && event === pending[pending.length-1] ? 'En eski yanıtsız · ' : '';
    item.title.textContent = `${position}${labels[event.camera]} kamera · Duman şüphesi`;
    item.row.dataset.queuePosition = isPending && event === pending[pending.length-1] && pending.length > 1 ? 'oldest' : isPending && event === pending[0] ? 'newest' : '';
    const keepVisible = pending.indexOf(event) < 3 || event === pending[pending.length-1] || item.row.open || item.row.contains(document.activeElement);
    item.row.hidden = isPending && !showOlderPending && !keepVisible;
    item.meta.textContent = `${dateTime(event.opened_at)} · son gözlem güveni %${Math.round(event.confidence * 100)}`;
    item.event = event;
    renderClip(item, event);
    item.detail.textContent = `${event.closed_at ? 'Gözlem sona erdi' : 'İzleme sürüyor'} · son gözlem ${time(event.last_seen)}`;
    renderActions(item, event);
    const target = isPending ? $('#events') : $('#history-events');
    // Keep existing rows and controls in place while measurements poll.
    const group = isPending ? pending : history;
    const index = group.indexOf(event);
    if (target.children[index] !== item.row) target.insertBefore(item.row, target.children[index] || null);
  }
  if (!pending.length) $('#events').append(text('p', events.length ? 'Karar bekleyen kayıt yok.' : 'Henüz duman şüphesi kaydı yok.', 'empty'));
  const olderCount = [...$('#events').children].filter(row => row.hidden).length;
  $('#queue-controls').hidden = pending.length < 2;
  $('#older-toggle').hidden = !olderCount && !showOlderPending;
  $('#older-toggle').textContent = showOlderPending ? 'Eski kayıtları daralt' : `Önceki ${olderCount} kaydı göster`;
  $('#older-toggle').setAttribute('aria-expanded', String(showOlderPending));
  $('#events').setAttribute('aria-busy', 'false');
  $('#history').hidden = !history.length;
  $('#history-count').textContent = `(${history.length})`;
  if (!pending.length && history.length && !$('#history').dataset.initialized) {
    $('#history').open = true;
    $('#history').dataset.initialized = 'true';
  }
}
function jumpToPending(oldest) {
  const pending = currentEvents.filter(event=>event.decision==='pending').sort((a,b)=>a.opened_at-b.opened_at);
  const event = oldest ? pending[0] : pending[pending.length-1];
  if (!event) return;
  const item = eventElements.get(event.id);
  item.row.open = true;
  renderEvents(currentEvents, true);
  item.row.scrollIntoView?.({block:'nearest'});
  item.row.querySelector('summary').focus({preventScroll:true});
}
$('#queue-newest').onclick = () => jumpToPending(false);
$('#queue-oldest').onclick = () => jumpToPending(true);
$('#older-toggle').onclick = () => {showOlderPending=!showOlderPending;renderEvents(currentEvents, true);};
async function decide(id, decision) {
  const item = eventElements.get(id);
  if (!item || item.saving || !online) return;
  item.saving = true;
  item.actions.querySelectorAll('button').forEach(button => { button.disabled = true; });
  const message = item.actions.querySelector('.inline-status');
  message.classList.remove('error');
  message.textContent = 'Kaydediliyor…';
  try {
    await json(`/api/events/${id}/decision`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({decision})});
    decisionRevision++;
    editing.delete(id);
    item.row.open = true;
    const nextPending=currentEvents.find(event=>event.id!==id&&event.decision==='pending');
    if(nextPending&&eventElements.has(nextPending.id)&&!queueIsEngaged())eventElements.get(nextPending.id).row.open=true;
    item.savedUntil = Date.now() + 4000;
    // A successful write is authoritative even if the next polling request fails.
    currentEvents = currentEvents.map(event => event.id === id ? {...event, decision, decided_at: Date.now() / 1000} : event);
    if (online) {
      if(queueIsEngaged()){if(!item.video.paused)item.video.pause?.();item.event=currentEvents.find(event=>event.id===id);renderActions(item,item.event);queuedEvents=currentEvents;}
      else renderEvents(currentEvents, true);
      $('#history').open = true;
      item.actions.querySelector('button')?.focus({preventScroll: true});
    }
    setTimeout(() => {
      if (item.savedUntil <= Date.now()) item.actions.querySelector('.inline-status').textContent = '';
    }, 4000);
  } catch (error) {
    message.classList.add('error');
    message.textContent = 'Karar kaydedilemedi. Yeniden deneyin.';
  } finally {
    item.saving = false;
    item.actions.querySelectorAll('button').forEach(button => { button.disabled = false; });
  }
}
function serverLost() {
  online = false;
  document.title = `Bağlantı yok — ${stationTitle}`;
  $('#connection').textContent = 'İstasyon bağlantısı yok';
  $('#connection').className = 'lost';
  $('#pending-summary').textContent = 'Kayıtlara erişilemiyor';
  $('#queue-controls').hidden = true;
  $('#older-toggle').hidden = true;
  $('#pending-summary').classList.remove('has-pending');
  const warning = $('#system-warning');
  warning.hidden = false;
  warning.replaceChildren(text('strong', 'İstasyon yanıt vermiyor · yeniden deneniyor'),
    text('span', lastUpdate ? `Son veri ${time(lastUpdate)}. Görüntü, ölçüm ve karar listesi güncel değil.` : 'Görüntü, ölçüm ve karar listesi alınamıyor.'));
  $('#coverage').textContent = 'Giriş durumları bilinmiyor';
  $('#measured-on').textContent = 'Ölçüm cihazı bilgisi alınamıyor';
  renderModule(null);
  for (const item of cameraElements.values()) updateCamera(item.camera, false);
  $('#cameras').setAttribute('aria-busy', 'true');
  $('#event-count').textContent = 'Kayıtlar alınamıyor';
  $('#event-count').classList.remove('has-pending');
  $('#events').replaceChildren(text('p', 'Bağlantı bekleniyor… Karar listesi yeniden yüklenecek.', 'empty'));
  $('#events').setAttribute('aria-busy', 'true');
  $('#history').hidden = true;
}
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  const revision = decisionRevision;
  try {
    const [status, events] = await Promise.all([json('/api/status'), json('/api/events')]);
    // A poll started before a successful write must not restore the old decision.
    if (revision !== decisionRevision) return;
    currentStatus = status;
    currentEvents = events;
    online = true;
    lastUpdate = Date.now() / 1000;
    $('#connection').textContent = `İstasyon bağlı · ${time(lastUpdate)}`;
    $('#connection').className = '';
    renderEvents(events);
    renderStatus(status);
  } catch (error) { serverLost(); }
  finally { refreshing = false; }
}
async function poll() {
  await refresh();
  setTimeout(poll, 1000);
}
poll();
