'use strict';
const stationTitle = document.title;
const labels = {left: 'Left', centre: 'Center', right: 'Right'};
const decisions = {confirmed: 'Operator confirmed suspicion', rejected: 'Operator rejected suspicion'};
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
let pendingCount = 0;
let pendingOrder = 'newest';
let pendingCursor = null;
let pendingNextCursor = null;
let pendingTrail = [];
let pendingNavigation = false;
const $ = selector => document.querySelector(selector);
const text = (tag, value, className) => {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
};
const num = (value, digits = 1) => Number.isFinite(value)
  ? value.toLocaleString('en-GB', {minimumFractionDigits: digits, maximumFractionDigits: digits}).replace('-', '−') : '—';
const parameter = value => Number.isFinite(value) ? value.toLocaleString('en-GB', {maximumFractionDigits: 3}) : '—';
const time = value => value ? new Date(value * 1000).toLocaleTimeString('en-GB') : '—';
const dateTime = value => new Date(value * 1000).toLocaleString('en-GB', {day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit'});
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
  image.alt = `${labels[camera.name]} camera feed`;
  image.hidden = true;
  const placeholder = text('p', 'Waiting for image…', 'placeholder');
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
  item.state.textContent = !online ? 'Status unknown' : !connected ? 'Connection lost' : suspicion.length
    ? `Smoke suspicion · ${Math.round(Math.max(...suspicion.map(event => event.confidence)) * 100)}%` : 'Receiving images';
  item.source.textContent = camera.kind === 'file' ? 'Recorded demo · local analysis' : 'Live camera · local analysis';
  if (!connected) {
    item.image.hidden = true;
    item.image.removeAttribute('src');
    item.busy = false;
    item.placeholder.hidden = false;
    item.placeholder.textContent = online ? 'Image unavailable · retrying' : 'Waiting for station data…';
  }
  item.info.replaceChildren();
  if (connected && !camera.pipeline_error) {
    const device = currentStatus?.measured_on?.board_model || currentStatus?.measured_on?.cpu_model;
    item.info.append(text('span', device ? `Measured · ${device}` : 'Measured', 'metric-label'));
    const values = text('p', '', 'metric-values');
    const measured = camera.analyses > 0;
    for (const value of [
      `Analysis ${num(measured ? camera.analysis_ms : null)} ms`,
      `inference ${num(measured ? camera.inference_ms : null)} ms`,
      `${num(camera.analyses > 1 ? camera.analysis_hz : null, 2)} analyses/s`,
      `${num(camera.capture_fps)} frames/s`
    ]) values.append(text('span', value));
    item.info.append(values);
  } else {
    item.info.append(text('p', camera.pipeline_error && online ? 'Analysis unavailable · check local logs' : 'Measured · —', camera.pipeline_error && online ? 'pipeline-error' : ''));
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
  $('#coverage').textContent = `${receiving.length}/${active.length} active inputs receiving images`;
  const warning = $('#system-warning');
  const failed = active.filter(camera => !receiving.includes(camera));
  const pipelineFailed = receiving.filter(camera => camera.pipeline_error);
  const runtimeFailed = currentStatus.runtime?.error;
  const retentionFailed = currentStatus.runtime?.retention_error;
  warning.hidden = !failed.length && !pipelineFailed.length && !runtimeFailed && !retentionFailed && active.length > 0;
  if (!warning.hidden) {
    const title = !receiving.length ? 'Observation unavailable' : failed.length ? 'Reduced observation coverage' : pipelineFailed.length || runtimeFailed ? 'Analysis outage' : 'Record maintenance outage';
    const reason = failed.length ? `${failed.map(camera => labels[camera.name]).join(', ')} camera connection lost. Retrying.`
      : runtimeFailed ? 'Images available; smoke analysis stopped. Check local logs.'
      : pipelineFailed.length ? `${pipelineFailed.map(camera => labels[camera.name]).join(', ')} camera images available; smoke analysis is not running.`
      : retentionFailed ? 'Old records could not be removed; retrying. Smoke analysis continues.' : 'No active camera inputs.';
    warning.replaceChildren(text('strong', `${title} · ${receiving.length}/${active.length} inputs`), text('span', reason));
  }
}
// Real radios show their read-back state; nothing but "radio connected" looks healthy.
function renderRadio(lora) {
  const element = $('#lora-link');
  if (!lora || typeof lora !== 'object' || !lora.label) { element.hidden = true; return; }
  element.hidden = false;
  const real = lora.transport === 'meshtastic';
  const parts = [lora.label];
  if (real && lora.ready) parts.push(`${lora.region} · ${lora.sub_band} MHz · delivery not confirmed`);
  else if (real && lora.detail) parts.push(lora.detail);
  if (lora.error) parts.push(lora.error);
  element.textContent = parts.join(' · ');
  element.className = real && !lora.ready || lora.error ? 'lost' : '';
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
    .map(camera => {
      const tile = text('article', '', 'camera inactive');
      tile.append(text('h3', `${labels[camera.name]} · ${num(camera.yaw, 0)}°`),
        text('p', 'mounted, inactive'), text('span', `${status.cameras.filter(c => c.active).length} of 2 inputs active · inactive slot`, 'inactive-note'));
      return tile;
    }));
  $('#geometry').replaceChildren(...status.cameras.map(camera => text('p',
    `${labels[camera.name]}: tilt ${num(camera.tilt, 0)}° · horizontal/vertical FOV ${num(camera.hfov, 0)}° / ${num(camera.vfov, 0)}°`)));
  $('#settings').textContent = `Configured target: ${num(status.target_analysis_hz, 2)} analyses/s/camera · model input ${status.input_size}px. Select the camera pair in configuration.`;
  const profile = status.analysis_profile;
  $('#analysis-profile').textContent = profile ? profile.name === 'demo'
    ? 'Demo profile · Tuned for nearby smoke; may miss small, distant smoke.'
    : 'Field profile · Larger model input for small, distant smoke; slower analysis.'
    : 'Analysis profile unavailable';
  $('#profile-parameters').textContent = profile
    ? `Model ${profile.input_size}px · confidence threshold ${parameter(profile.confidence * 100)}% · target ${parameter(profile.interval_seconds)} s/camera · event timeout ${parameter(profile.event_timeout_seconds)} s`
    : '';
  if (profile) $('#profile-parameters').textContent += profile.detector_view === 'center_crop'
    ? ' · Center square only; outer strips of the preview are not analysed.'
    : profile.detector_view === 'centre_zoom'
      ? ' · Center zoom: two small center crops only; outer strips of the preview are not analysed.'
      : ' · Full camera frame.';
  renderModule(status.mcu);
  renderRadio(status.lora);
  $('#measured-on').textContent = status.measured_on?.label || 'Measurement device unavailable';
  updateCoverage();
}
function renderModule(mcu) {
  const sensor = mcu?.flame_sensor;
  const state = $('#flame-status');
  $('#mcu-mode').hidden = !mcu?.simulated && mcu?.mode !== 'off';
  $('#mcu-mode').textContent = mcu?.simulated ? 'Simulation' : mcu?.mode === 'off' ? 'Not configured' : '';
  state.textContent = sensor?.status_text || 'Flame-sensor status unknown';
  state.className = sensor?.triggered ? 'triggered' : sensor?.configured && !sensor.connected ? 'lost' : '';
  $('#flame-note').textContent = sensor?.note || 'Local short-range infrared sensor. It does not confirm camera smoke suspicions.';
  const shown = mcu?.led?.shown;
  $('#led-swatch').dataset.colour = shown?.colour || 'unknown';
  const colours = {green: 'Green', amber: 'Amber', blue: 'Blue', red: 'Red', 'red→green→blue': 'Red → green → blue'};
  const patterns = {steady: 'steady', 'double blink every 1.2 s': 'double blink every 1.2 s', 'slow blink, 1 s on / 1 s off': '1 s on / 1 s off', 'fast blink, 5 per second': '5 blinks per second', 'short flash every 2 s': 'short flash every 2 s', 'one 0.75 s lamp test at power-up': '0.75 s lamp test at startup'};
  $('#led-status').textContent = shown ? `Status LED: ${colours[shown.colour] || shown.colour || '—'} · ${patterns[shown.pattern] || shown.pattern || '—'} · ${shown.text}` : 'Status LED: unavailable';
  $('#sensor-reading').textContent = sensor?.connected && Number.isFinite(sensor.level_permille) ? `Relative infrared level: ${num(sensor.level_permille, 0)}/1000 · uncalibrated; not a distance or flame size.` : '';
  $('#led-requested').textContent = mcu?.led?.requested ? `Station-requested LED state: ${mcu.led.requested.text}. The state above is read from the microcontroller.` : '';
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
  image.alt = 'Event image with smoke suspicion marked';
  image.loading = 'lazy';
  evidence.append(image);
  const player = text('div', '', 'clip-player');
  const video = document.createElement('video');
  video.controls = true;
  video.muted = true;
  video.playsInline = true;
  video.preload = 'none';
  video.setAttribute('aria-label', 'Smoke suspicion event clip');
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
  const noImage = text('p', 'Waiting for saved image…', 'event-detail');
  const detail = text('p', '', 'event-detail');
  const clipBar = text('div', '', 'clip-bar');
  const clipLabel = text('span', '', 'clip-label');
  const clip = text('a', '', 'evidence-link');
  clipBar.append(clipLabel, clip);
  const clipStatus = text('p', '', 'event-detail clip-status');
  const actions = text('div', '', 'actions');
  const disclosure = text('span', 'Open record', 'event-disclosure');
  row.addEventListener('toggle', () => {disclosure.textContent = row.open ? 'Collapse record' : 'Open record';});
  summary.append(title, meta, disclosure);
  const body = text('div', '', 'event-body');
  body.append(player, evidence, noImage, clipBar, clipStatus, detail, actions);
  row.append(body);
  const item = {row, title, meta, player, video, evidence, image, noImage, detail, clipBar, clipLabel, clip, clipStatus, actions, event, playbackFailed: null, mode: '', saving: false, savedUntil: 0};
  eventElements.set(event.id, item);
  return item;
}
function sourceLabel(event) {
  const camera = currentStatus?.cameras.find(candidate => candidate.name === event.camera);
  return (event.source_kind || camera?.kind) === 'usb' ? 'Camera recording' : (event.source_kind || camera?.kind) === 'file' ? 'Recorded demo' : 'Event recording';
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
    item.clipLabel.textContent = `${sourceLabel(event)} · event clip`;
    item.clip.textContent = `Download (.${extension})`;
    item.clip.setAttribute('href', clipUrl);
    item.clip.setAttribute('download', event.clip);
  }
  item.clipStatus.classList.remove('error');
  if (!clipUrl) {
    item.clipStatus.textContent = event.media_error ? 'Clip could not be saved · marked image above' : 'Preparing event clip…';
    item.clipStatus.classList.toggle('error', !!event.media_error);
  } else if (playable) {
    item.clipStatus.textContent = '';
  } else if (extension === 'webm') {
    item.clipStatus.textContent = 'This browser cannot play the clip · marked image shown; clip available to download';
  } else {
    item.clipStatus.textContent = 'This clip cannot play in the browser (.avi) · marked image shown; download the clip to play it locally';
  }
  item.clipStatus.hidden = !item.clipStatus.textContent;
}
function renderActions(item, event) {
  const mode = event.decision === 'pending' || editing.has(event.id) ? 'editing' : 'decided';
  const signature = `${mode}:${event.decision}:${event.decided_at}`;
  if (item.mode === signature) return;
  item.mode = signature;
  item.actions.replaceChildren();
  item.actions.append(text('p', mode === 'editing' ? 'Awaiting decision' : `${decisions[event.decision]} · ${time(event.decided_at)}`, 'decision'));
  if (mode === 'editing') {
    for (const [choice, label] of [['confirmed', 'Confirm suspicion'], ['rejected', 'Reject suspicion']]) {
      const button = text('button', label, choice === 'rejected' ? 'reject' : 'confirm');
      button.type = 'button';
      button.addEventListener('click', () => decide(event.id, choice));
      item.actions.append(button);
    }
    if (event.decision !== 'pending') {
      item.actions.firstChild.textContent = 'Change decision';
      const cancel = text('button', 'Cancel', 'cancel');
      cancel.type = 'button';
      cancel.onclick = () => { editing.delete(event.id); renderEvents(currentEvents, true); item.actions.querySelector('button')?.focus(); };
      item.actions.append(cancel);
    }
  } else {
    const change = text('button', 'Change', 'change');
    change.type = 'button';
    change.setAttribute('aria-label', `Change decision for ${labels[event.camera]} camera`);
    change.onclick = () => { editing.add(event.id); renderEvents(currentEvents, true); item.actions.querySelector('button')?.focus(); };
    item.actions.append(change);
  }
  const message = text('p', '', 'inline-status');
  message.setAttribute('role', 'status');
  if (item.savedUntil > Date.now()) message.textContent = 'Saved on this device.';
  item.actions.append(message);
}
let queuePointerInside = false;
let queuedEvents = null;
let nextReviewId = null;
const queuePanel = $('#event-panel');
function queueIsEngaged() { return queuePointerInside || queuePanel.contains(document.activeElement); }
function flushQueue() {
  if (queuedEvents && online && !queueIsEngaged()) { const events=queuedEvents;queuedEvents=null;renderEvents(events); }
}
queuePanel.addEventListener('pointerenter', () => { queuePointerInside=true; });
queuePanel.addEventListener('pointerleave', () => { queuePointerInside=false;flushQueue(); });
queuePanel.addEventListener('focusout', () => { queueMicrotask(flushQueue); });
function renderPendingTotal(events) {
  $('#event-count').textContent = `${pendingCount} awaiting decision`;
  $('#event-count').classList.toggle('has-pending', pendingCount > 0);
  $('#pending-summary').textContent = 'Review records';
  $('#pending-summary').classList.remove('has-pending');
  document.title = pendingCount ? `(${pendingCount}) Smoke suspicion — ${[...new Set(events.filter(event=>event.decision==='pending').map(event => labels[event.camera]))].join(', ')} — ${stationTitle}` : stationTitle;
}
function renderEvents(events, deliberate=false) {
  renderPendingTotal(events);
  if (!deliberate && $('#events').getAttribute('aria-busy') !== 'true' && eventElements.size && queueIsEngaged()) {
    queuedEvents=events;
    const arrivals=events.filter(event=>event.decision==='pending'&&!eventElements.has(event.id)).length;
    $('#queue-arrivals').hidden=!arrivals;
    $('#queue-arrivals').textContent=`${arrivals} new records · shown when you leave the list`;
    return;
  }
  queuedEvents=null;
  $('#queue-arrivals').hidden=true;
  const pending = events.filter(event => event.decision === 'pending').sort((a,b)=>pendingOrder === 'newest' ? b.opened_at-a.opened_at || b.id.localeCompare(a.id) : a.opened_at-b.opened_at || a.id.localeCompare(b.id));
  const history = events.filter(event => event.decision !== 'pending');
  if (nextReviewId) {
    const next = eventElements.get(nextReviewId);
    if (next && pending.some(event => event.id === nextReviewId)) next.row.open = true;
    nextReviewId = null;
  }
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
    const first = event === pending[0], last = event === pending[pending.length-1];
    const newest = pendingOrder === 'newest' ? first && !pendingCursor : last && !pendingNextCursor;
    const oldest = pendingOrder === 'oldest' ? first && !pendingCursor : last && !pendingNextCursor;
    const position = isPending && newest ? 'Newest · ' : isPending && oldest ? 'Oldest awaiting review · ' : '';
    item.title.textContent = `${position}${labels[event.camera]} camera · Smoke suspicion`;
    item.row.dataset.queuePosition = isPending && event === pending[pending.length-1] && pending.length > 1 ? 'oldest' : isPending && event === pending[0] ? 'newest' : '';
    const keepVisible = pending.indexOf(event) < 3 || event === pending[pending.length-1] || item.row.open || item.row.contains(document.activeElement);
    item.row.hidden = isPending && !showOlderPending && !keepVisible;
    item.meta.textContent = `${dateTime(event.opened_at)} · latest observation confidence ${Math.round(event.confidence * 100)}%`;
    item.event = event;
    renderClip(item, event);
    item.detail.textContent = `${event.closed_at ? 'Observation ended' : 'Monitoring continues'} · last observed ${time(event.last_seen)}`;
    renderActions(item, event);
    const target = isPending ? $('#events') : $('#history-events');
    // Keep existing rows and controls in place while measurements poll.
    const group = isPending ? pending : history;
    const index = group.indexOf(event);
    if (target.children[index] !== item.row) target.insertBefore(item.row, target.children[index] || null);
  }
  if (!pending.length) $('#events').append(text('p', pendingCount ? 'No records awaiting review on this page. Open the newest or previous page.' : events.length ? 'No records awaiting review.' : 'No smoke suspicion records yet.', 'empty'));
  const olderCount = [...$('#events').children].filter(row => row.hidden).length;
  $('#queue-controls').hidden = pendingCount < 2;
  $('#queue-next-page').hidden = !pendingNextCursor;
  $('#queue-prev-page').hidden = !pendingTrail.length;
  $('#older-toggle').hidden = !olderCount && !showOlderPending;
  $('#older-toggle').textContent = showOlderPending ? 'Collapse older records' : `Show ${olderCount} older records`;
  $('#older-toggle').setAttribute('aria-expanded', String(showOlderPending));
  $('#events').setAttribute('aria-busy', 'false');
  $('#history').hidden = !history.length;
  $('#history-count').textContent = `(${history.length})`;
  if (!pending.length && history.length && !$('#history').dataset.initialized) {
    $('#history').open = true;
    $('#history').dataset.initialized = 'true';
  }
}
let pendingJump = null;
async function loadPendingPage(order, cursor = null, trail = [], jump = null) {
  pendingJump = jump;
  pendingOrder = order;
  pendingCursor = cursor;
  pendingTrail = trail;
  decisionRevision++;
  await refresh(true);
}
async function jumpToPending(oldest) {
  const loaded = currentEvents.filter(event=>event.decision==='pending');
  if (pendingCount > loaded.length || pendingCursor) {
    await loadPendingPage(oldest ? 'oldest' : 'newest', null, [], oldest);
    return;
  }
  focusPending(oldest);
}
function focusPending(oldest) {
  const pending = currentEvents.filter(event=>event.decision==='pending').sort((a,b)=>a.opened_at-b.opened_at || a.id.localeCompare(b.id));
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
$('#queue-next-page').onclick = () => {
  if (pendingNextCursor) loadPendingPage(pendingOrder, pendingNextCursor, [...pendingTrail, pendingCursor]);
};
$('#queue-prev-page').onclick = () => {
  if (pendingTrail.length) loadPendingPage(pendingOrder, pendingTrail.at(-1), pendingTrail.slice(0,-1));
};
$('#older-toggle').onclick = () => {showOlderPending=!showOlderPending;renderEvents(currentEvents, true);};
async function decide(id, decision) {
  const item = eventElements.get(id);
  if (!item || item.saving || !online) return;
  item.saving = true;
  item.actions.querySelectorAll('button').forEach(button => { button.disabled = true; });
  const message = item.actions.querySelector('.inline-status');
  message.classList.remove('error');
  message.textContent = 'Saving…';
  try {
    await json(`/api/events/${id}/decision`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({decision})});
    decisionRevision++;
    if (item.event.decision === 'pending') pendingCount = Math.max(0, pendingCount-1);
    editing.delete(id);
    item.row.open = true;
    const nextPending=currentEvents.find(event=>event.id!==id&&event.decision==='pending');
    if(nextPending&&eventElements.has(nextPending.id)){
      if(queueIsEngaged())nextReviewId=nextPending.id;
      else eventElements.get(nextPending.id).row.open=true;
    }
    item.savedUntil = Date.now() + 4000;
    // A successful write is authoritative even if the next polling request fails.
    currentEvents = currentEvents.map(event => event.id === id ? {...event, decision, decided_at: Date.now() / 1000} : event);
    if (online) {
      renderPendingTotal(currentEvents);
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
    message.textContent = 'Decision could not be saved. Try again.';
  } finally {
    item.saving = false;
    item.actions.querySelectorAll('button').forEach(button => { button.disabled = false; });
  }
}
function serverLost() {
  online = false;
  document.title = `No connection — ${stationTitle}`;
  $('#connection').textContent = 'Station disconnected';
  $('#connection').className = 'lost';
  $('#pending-summary').textContent = 'Records unavailable';
  $('#queue-controls').hidden = true;
  $('#older-toggle').hidden = true;
  $('#pending-summary').classList.remove('has-pending');
  const warning = $('#system-warning');
  warning.hidden = false;
  warning.replaceChildren(text('strong', 'Station not responding · retrying'),
    text('span', lastUpdate ? `Last data received ${time(lastUpdate)}. Images, measurements and decision list are out of date.` : 'Images, measurements and decision list are unavailable.'));
  $('#coverage').textContent = 'Input status unknown';
  $('#measured-on').textContent = 'Measurement device unavailable';
  $('#analysis-profile').textContent = 'Analysis profile unknown · station disconnected';
  $('#profile-parameters').textContent = '';
  $('#led-swatch').dataset.colour = 'unknown';
  renderModule(null);
  for (const item of cameraElements.values()) updateCamera(item.camera, false);
  $('#cameras').setAttribute('aria-busy', 'true');
  $('#event-count').textContent = 'Records unavailable';
  $('#event-count').classList.remove('has-pending');
  $('#events').replaceChildren(text('p', 'Waiting for connection… The decision list will reload.', 'empty'));
  $('#events').setAttribute('aria-busy', 'true');
  $('#history').hidden = true;
}
async function refresh(deliberate = false) {
  if (refreshing) { if (deliberate) pendingNavigation = true; return; }
  refreshing = true;
  const revision = decisionRevision;
  try {
    const params = new URLSearchParams({order:pendingOrder});
    if (pendingCursor) params.set('cursor',pendingCursor);
    const [status, history, page] = await Promise.all([json('/api/status'), json('/api/events'), json(`/api/events/pending?${params}`)]);
    const events = [...page.events, ...history.filter(event => event.decision !== 'pending')];
    // A poll started before a successful write must not restore the old decision.
    if (revision !== decisionRevision) return;
    currentStatus = status;
    pendingCount = page.pending_count;
    pendingNextCursor = page.next_cursor;
    currentEvents = events;
    online = true;
    lastUpdate = Date.now() / 1000;
    $('#connection').textContent = `Station connected · ${time(lastUpdate)}`;
    $('#connection').className = '';
    renderEvents(events, deliberate);
    renderStatus(status);
    if (pendingJump !== null) { const oldest = pendingJump; pendingJump = null; focusPending(oldest); }
  } catch (error) { serverLost(); }
  finally { refreshing = false; if (pendingNavigation) { pendingNavigation=false; await refresh(true); } }
}
async function poll() {
  await refresh();
  setTimeout(poll, 1000);
}
poll();
