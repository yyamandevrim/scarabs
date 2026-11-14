import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Window} from 'happy-dom';

const stationTitle = 'Test product — Observation node';
const html = readFileSync(new URL('../station/static/index.html', import.meta.url), 'utf8')
  .replaceAll('{{station_title}}', stationTitle).replaceAll('{{station_wordmark}}', 'Test product');
const script = readFileSync(new URL('../station/static/app.js', import.meta.url), 'utf8');
const camera = (name, active = true) => ({
  name, active, connected: active, kind: 'file', yaw: name === 'left' ? -70 : name === 'right' ? 70 : 0,
  tilt: 0, hfov: 80, vfov: 50, analyses: 10, analysis_ms: 54.8, inference_ms: 53.1,
  analysis_hz: 0.98, capture_fps: 25.5, pipeline_error: null
});
const event = (overrides = {}) => ({
  id: '0123456789abcdef0123456789abcdef', camera: 'left', opened_at: 1700000000,
  last_seen: 1700000005, closed_at: null, confidence: .88, decision: 'pending',
  decided_at: null, snapshot: '0123456789abcdef0123456789abcdef.jpg', clip: null,
  media_error: null, ...overrides
});
const flush = async () => { for (let i = 0; i < 4; i++) await new Promise(resolve => setImmediate(resolve)); };
async function panel(events = [], options = {}) {
  const window = new Window({url: 'http://127.0.0.1/', settings: {disableCSSFileLoading: true, disableJavaScriptFileLoading: true, enableImageFileLoading: false, handleDisabledFileLoadingAsSuccess: true}});
  const state = {events, status: {cameras: [camera('left'), camera('centre'), camera('right', false)], target_analysis_hz: 1, input_size: 640}, fail: false, postFail: false, posts: []};
  window.setTimeout = () => 1;
  window.clearTimeout = () => {};
  window.fetch = async (url, init) => {
    if (options.loading) return new Promise(() => {});
    if (state.fail) throw new Error('server lost');
    if (init?.method === 'POST') {
      if (state.postFail) throw new Error('write failed');
      const decision = JSON.parse(init.body).decision;
      state.posts.push({url, decision});
      state.events = state.events.map(item => url === `/api/events/${item.id}/decision` ? {...item, decision, decided_at: Date.now() / 1000} : item);
      return {ok: true, json: async () => ({ok: true, decision})};
    }
    if (url.startsWith('/api/events/pending')) {
      const params = new URL(url, 'http://127.0.0.1').searchParams;
      const order = params.get('order') || 'newest';
      const compare = (a,b) => a.opened_at-b.opened_at || a.id.localeCompare(b.id);
      let pending = state.events.filter(e => e.decision === 'pending').sort(compare);
      if (order === 'newest') pending.reverse();
      const total = pending.length;
      const cursor = params.get('cursor');
      if (cursor) {
        const anchor = JSON.parse(Buffer.from(cursor, 'base64url').toString());
        pending = pending.filter(e => order === 'newest' ? compare(e, anchor) < 0 : compare(e, anchor) > 0);
      }
      const items = pending.slice(0,200);
      const next = pending.length > 200 ? Buffer.from(JSON.stringify(items.at(-1))).toString('base64url') : null;
      return {ok:true, json: async () => structuredClone({events:items,pending_count:total,next_cursor:next})};
    }
    return {ok: true, json: async () => structuredClone(url === '/api/status' ? state.status : state.events.slice(0,200))};
  };
  window.document.write(html);
  window.eval(`${script}\nwindow.testRefresh = refresh;`);
  await flush();
  return {window, state, $: selector => window.document.querySelector(selector), refresh: async () => { await window.testRefresh(); await flush(); }};
}

test('loading never claims no events or a connected station', async () => {
  const p = await panel([], {loading: true});
  assert.match(p.$('#events').textContent, /yükleniyor/);
  assert.equal(p.$('#events').getAttribute('aria-busy'), 'true');
  assert.match(p.$('#connection').textContent, /bağlanılıyor/);
  assert.equal(p.$('#cameras').children.length, 2);
  assert.doesNotMatch(p.$('#events').textContent, /Henüz/);
  assert.ok(p.$('#event-panel').compareDocumentPosition(p.$('.observation')) & 4);
  assert.equal(p.window.document.title, stationTitle);
});

test('normal has two feeds, one inactive status row, local demo labels and measured figures', async () => {
  const p = await panel();
  assert.equal(p.$('#cameras').children.length, 2);
  assert.match(p.$('#inactive-cameras').textContent, /Sağ.*takılı, bağlı değil/);
  assert.equal(p.window.document.querySelectorAll('.source-label').length, 2);
  assert.match(p.$('.source-label').textContent, /Kayıtlı demo/);
  assert.match(p.$('.camera-info').textContent, /Ölçülen.*54,8 ms/);
  assert.match(p.$('#events').textContent, /Henüz duman şüphesi kaydı yok/);
  assert.equal(p.$('#system-warning').hidden, true);
  assert.equal(p.window.document.title, stationTitle);
});

test('pending count excludes decisions, includes closed records still awaiting a decision', async () => {
  const p = await panel([event({closed_at: 1700000010}), event({id: 'other', decision: 'rejected', decided_at: 1700000010})]);
  assert.equal(p.$('#event-count').textContent, '1 karar bekliyor');
  assert.equal(p.$('#history-count').textContent, '(1)');
  assert.match(p.window.document.title, /\(1\) Duman şüphesi/);
  assert.ok(p.window.document.title.endsWith(stationTitle));
  assert.equal(p.$('.camera').classList.contains('suspected'), true); // other record remains open
});

test('open suspicion identifies the source camera and stops marking it once closed', async () => {
  const p = await panel([event()]);
  assert.match(p.$('.camera-state').textContent, /Duman şüphesi · %88/);
  assert.equal(p.$('.camera').classList.contains('suspected'), true);
  p.state.events[0].closed_at = 1700000010;
  await p.refresh();
  assert.equal(p.$('.camera').classList.contains('suspected'), false);
});

for (const [decision, selector, label] of [['confirmed', '.confirm', 'Operatör doğruladı'], ['rejected', '.reject', 'Operatör reddetti']]) {
  test(`${decision} persists then replaces both buttons with decision, time and change action`, async () => {
    const p = await panel([event()]);
    p.$(selector).click();
    await flush();
    assert.equal(p.state.posts[0].decision, decision);
    assert.equal(p.$('#event-count').textContent, '0 karar bekliyor');
    assert.equal(p.$('#events .event'), null);
    assert.equal(p.$('#history').open, true);
    assert.match(p.$('.decision').textContent, new RegExp(`${label} · \\d`));
    assert.equal(p.$('.confirm'), null);
    assert.equal(p.$('.reject'), null);
    assert.equal(p.$('.event').classList.contains('decided'), true);
    assert.match(p.$('.inline-status').textContent, /kaydedildi/);
    await p.refresh();
    assert.match(p.$('.decision').textContent, new RegExp(label));
    p.$('.change').click();
    assert.ok(p.$('.confirm'));
    assert.ok(p.$('.reject'));
    p.$('.cancel').click();
    assert.ok(p.$('.change'));
    assert.equal(p.$('.confirm'), null);
  });
}

test('failed decision stays pending, shows retry feedback, and restores controls', async () => {
  const p = await panel([event()]);
  p.state.postFail = true;
  p.$('.confirm').click();
  await flush();
  assert.match(p.$('.inline-status').textContent, /kaydedilemedi/);
  assert.equal(p.$('.confirm').disabled, false);
  assert.equal(p.$('#event-count').textContent, '1 karar bekliyor');
  p.state.postFail = false;
  p.$('.reject').click();
  await flush();
  assert.match(p.$('.decision').textContent, /reddetti/);
});

test('an older in-flight poll cannot undo a successful operator decision', async () => {
  const p = await panel([event()]);
  const fetch = p.window.fetch;
  let release;
  p.window.fetch = async (url, init) => {
    const response = await fetch(url, init);
    if (url !== '/api/events') return response;
    const snapshot = await response.json();
    await new Promise(resolve => { release = resolve; });
    return {ok: true, json: async () => snapshot};
  };
  const polling = p.refresh();
  await flush();
  p.$('.confirm').click();
  await flush();
  release();
  await polling;
  assert.match(p.$('.decision').textContent, /Operatör doğruladı/);
  assert.equal(p.$('.confirm'), null);
});

test('poll updates retain focused controls and an in-progress correction', async () => {
  const p = await panel([event({decision: 'confirmed', decided_at: 1700000010})]);
  p.$('.change').click();
  const button = p.$('.reject');
  button.focus();
  p.state.events[0].last_seen++;
  await p.refresh();
  assert.equal(p.$('.reject'), button);
  assert.equal(p.window.document.activeElement, button);
});

test('camera drop warns of reduced coverage, clears its measurements and leaves the other feed working', async () => {
  const p = await panel();
  p.state.status.cameras[1].connected = false;
  await p.refresh();
  assert.equal(p.$('#system-warning').hidden, false);
  assert.match(p.$('#system-warning').textContent, /Gözlem kapsamı azaldı · 1\/2.*Orta/);
  const dropped = p.$('.camera.disconnected');
  assert.match(dropped.textContent, /Bağlantı koptu/);
  assert.equal(dropped.querySelector('img').hidden, true);
  assert.equal(dropped.querySelector('.camera-info').textContent, 'Ölçülen · —');
  assert.match(p.$('.camera:not(.disconnected) .camera-info').textContent, /54,8 ms/);
  p.state.status.cameras[1].connected = true;
  await p.refresh();
  assert.equal(p.$('#system-warning').hidden, true);
});

test('all active sources lost states observation unavailable', async () => {
  const p = await panel();
  p.state.status.cameras.forEach(item => { item.connected = false; });
  await p.refresh();
  assert.match(p.$('#system-warning').textContent, /Gözlem kullanılamıyor · 0\/2/);
});

test('JPEG failure also reduces coverage until an image loads again', async () => {
  const p = await panel();
  p.$('.camera img').onerror();
  assert.match(p.$('#system-warning').textContent, /Gözlem kapsamı azaldı · 1\/2/);
  p.$('.camera img').onload();
  assert.equal(p.$('#system-warning').hidden, true);
});

test('server loss removes connected states, stale figures, empty all-clear and decision controls; recovery restores them', async () => {
  const p = await panel([event()]);
  p.state.fail = true;
  await p.refresh();
  assert.match(p.$('#system-warning').textContent, /İstasyon yanıt vermiyor.*Son veri/);
  assert.equal(p.$('#connection').textContent, 'İstasyon bağlantısı yok');
  assert.equal(p.$('#pending-summary').textContent, 'Kayıtlara erişilemiyor');
  assert.equal(p.window.document.title, `Bağlantı yok — ${stationTitle}`);
  assert.equal(p.$('.camera-state').textContent, 'Durum bilinmiyor');
  assert.equal(p.$('.camera-info').textContent, 'Ölçülen · —');
  assert.equal(p.$('.camera img').getAttribute('src'), null);
  assert.match(p.$('#events').textContent, /Bağlantı bekleniyor/);
  assert.doesNotMatch(p.$('#events').textContent, /Henüz/);
  assert.equal(p.$('.confirm'), null);
  assert.equal(p.$('#history').hidden, true);
  p.state.fail = false;
  await p.refresh();
  assert.equal(p.$('#system-warning').hidden, true);
  assert.ok(p.$('.confirm'));
  assert.equal(p.$('#events').getAttribute('aria-busy'), 'false');
});

test('USB sources use a live label and any configured active pair works', async () => {
  const p = await panel();
  p.state.status.cameras = [camera('left', false), {...camera('centre'), kind: 'usb'}, camera('right')];
  await p.refresh();
  assert.equal(p.$('#cameras').children.length, 2);
  assert.match(p.$('#inactive-cameras').textContent, /Sol/);
  assert.equal(p.$('.source-label').textContent, 'Canlı kamera · yerel analiz');
});

test('pipeline errors are a failure warning, not a measured zero or a healthy analysis', async () => {
  const p = await panel();
  p.state.status.cameras[0].pipeline_error = 'inference failed';
  await p.refresh();
  assert.match(p.$('#system-warning').textContent, /Analiz kesintisi/);
  assert.match(p.$('.camera-info').textContent, /Analiz kullanılamıyor/);
});

const webm = '0123456789abcdef0123456789abcdef.webm';
async function clipPanel(clip, canPlay = 'maybe', events) {
  const p = await panel(events || [event({clip})]);
  p.window.HTMLMediaElement.prototype.canPlayType = () => canPlay;
  p.window.HTMLMediaElement.prototype.pause = function () { this.pausedByPanel = true; };
  await p.refresh();
  return p;
}

test('WebM clip plays inline with the annotated snapshot as poster, recorded-demo label and download', async () => {
  const p = await clipPanel(webm);
  const video = p.$('.event video');
  assert.equal(p.$('.clip-player').hidden, false);
  assert.equal(video.getAttribute('src'), `/events/${webm}`);
  assert.equal(video.getAttribute('poster'), '/events/0123456789abcdef0123456789abcdef.jpg');
  assert.equal(video.controls, true);
  assert.equal(p.$('.event .evidence').hidden, true);
  assert.equal(p.$('.clip-label').textContent, 'Kayıtlı demo · olay klibi');
  assert.equal(p.$('.event .evidence-link').getAttribute('href'), `/events/${webm}`);
  assert.equal(p.$('.event .evidence-link').getAttribute('download'), webm);
  assert.equal(p.$('.event .evidence-link').textContent, 'İndir (.webm)');
  assert.equal(p.$('.clip-status').hidden, true);
  assert.doesNotMatch(p.$('.event').textContent, /yangın/i);
});

test('polling keeps the same video element and never reloads the clip being watched', async () => {
  const p = await clipPanel(webm);
  const video = p.$('.event video');
  let reloads = 0;
  const setAttribute = video.setAttribute.bind(video);
  video.setAttribute = (name, value) => { if (name === 'src') reloads++; setAttribute(name, value); };
  p.state.events[0].last_seen += 3;
  await p.refresh();
  await p.refresh();
  assert.equal(p.$('.event video'), video);
  assert.equal(reloads, 0);
});

test('legacy AVI events show the snapshot, an honest message and the download, without a player', async () => {
  const p = await clipPanel('0123456789abcdef0123456789abcdef.avi');
  assert.equal(p.$('.clip-player').hidden, true);
  assert.equal(p.$('.event video').getAttribute('src'), null);
  assert.equal(p.$('.event .evidence').hidden, false);
  assert.match(p.$('.clip-status').textContent, /tarayıcıda oynatılamaz \(\.avi\).*indirilip/);
  assert.equal(p.$('.event .evidence-link').textContent, 'İndir (.avi)');
  assert.equal(p.$('#event-count').textContent, '1 karar bekliyor');
});

test('a browser without VP8 support, or a decode error, falls back to snapshot plus download', async () => {
  const unsupported = await clipPanel(webm, '');
  assert.equal(unsupported.$('.clip-player').hidden, true);
  assert.equal(unsupported.$('.event .evidence').hidden, false);
  assert.match(unsupported.$('.clip-status').textContent, /Bu tarayıcı klibi oynatamıyor/);
  const p = await clipPanel(webm);
  p.$('.event video').dispatchEvent(new p.window.Event('error'));
  assert.equal(p.$('.clip-player').hidden, true);
  assert.equal(p.$('.event .evidence').hidden, false);
  assert.match(p.$('.clip-status').textContent, /oynatamıyor/);
  await p.refresh();
  assert.equal(p.$('.clip-player').hidden, true, 'a failed clip is not retried on every poll');
});

test('clip states: pending encode, failed encode and live camera label', async () => {
  const p = await clipPanel(null);
  assert.match(p.$('.clip-status').textContent, /hazırlanıyor/);
  assert.equal(p.$('.clip-bar').hidden, true);
  p.state.events[0].media_error = 'encoder failed';
  await p.refresh();
  assert.match(p.$('.clip-status').textContent, /Klip kaydedilemedi/);
  assert.equal(p.$('.clip-status').classList.contains('error'), true);
  p.state.events[0].clip = webm;
  p.state.events[0].media_error = null;
  p.state.status.cameras[0].kind = 'usb';
  await p.refresh();
  assert.equal(p.$('.clip-label').textContent, 'Kamera kaydı · olay klibi');
});

test('deciding pauses a playing clip', async () => {
  const p = await clipPanel(webm);
  const video = p.$('.event video');
  Object.defineProperty(video, 'paused', {configurable: true, get: () => false});
  p.$('.confirm').click();
  await flush();
  assert.equal(video.pausedByPanel, true);
});

test('large queue starts with one open record and polling preserves the reviewed disclosure', async () => {
  const p = await panel(Array.from({length: 60}, (_, i) => event({id: `queue-${i}`, opened_at: 1700000000 - i * 60})));
  assert.equal(p.$('#event-count').textContent, '60 karar bekliyor');
  assert.equal(p.window.document.querySelectorAll('#events .event[open]').length, 1);
  const reviewed = p.$('[data-event-id="queue-12"]');
  p.$('#events .event').open = false;
  reviewed.open = true;
  p.state.events.unshift(event({id: 'new-arrival'}));
  await p.refresh();
  assert.equal(reviewed.open, true);
  assert.equal(p.$('[data-event-id="new-arrival"]').open, false);
  assert.equal(p.window.document.querySelectorAll('#events .event[open]').length, 1);
});

test('machine label accompanies measurements and confidence is explicitly latest', async () => {
  const p = await panel([event()]);
  p.state.status.measured_on = {label: 'Ölçüm bu cihazda: Test CPU · Linux · UNO Q değil'};
  await p.refresh();
  assert.match(p.$('#measured-on').textContent, /Test CPU/);
  assert.match(p.$('.event-meta').textContent, /son gözlem güveni %88/);
});

test('local flame and observed LED are separate from smoke events and go unknown on server loss', async () => {
  const p = await panel();
  p.state.status.mcu = {mode: 'simulated', simulated: true,
    flame_sensor: {configured: true, connected: true, triggered: true, status_text: 'Alev sensörü tetiklendi', level_permille: 700, note: 'Yerel kısa menzilli sensör; kamera duman şüphesini doğrulamaz.'},
    led: {shown: {colour: 'red', pattern: 'fast blink, 5 per second', text: 'Alev sensörü tetiklendi'}, requested: {text: 'Normal gözlem'}}};
  await p.refresh();
  assert.equal(p.$('#flame-status').textContent, 'Alev sensörü tetiklendi');
  assert.match(p.$('.sensor-scope').textContent, /kısa menzilli.*doğrulamaz/);
  assert.equal(p.$('#mcu-mode').textContent, 'Simülasyon');
  assert.match(p.$('#led-status').textContent, /Kırmızı.*saniyede 5/);
  assert.doesNotMatch(p.$('#led-status').textContent, /Normal gözlem/);
  assert.match(p.$('#led-requested').textContent, /Normal gözlem/);
  assert.match(p.$('#sensor-reading').textContent, /700\/1000.*kalibre edilmemiştir/);
  assert.equal(p.$('#event-count').textContent, '0 karar bekliyor');
  p.state.fail = true;
  await p.refresh();
  assert.match(p.$('#flame-status').textContent, /bilinmiyor/);
  assert.equal(p.$('#led-status').textContent, 'Durum LED’i: okunamıyor');
  assert.equal(p.$('#sensor-reading').textContent, '');
});

test('pending total has one visible home and older records disclose without hiding a watched clip', async () => {
  const events = Array.from({length: 60}, (_, i) => event({id: `ordered-${i}`, opened_at: 1700000000 - i * 60}));
  const p = await panel(events);
  assert.equal(p.$('#pending-summary').textContent, 'Kayıtları incele');
  assert.equal(p.$('#event-count').textContent, '60 karar bekliyor');
  assert.equal(p.window.document.querySelectorAll('#events .event:not([hidden])').length, 4);
  assert.equal(p.$('#older-toggle').textContent, 'Önceki 56 kaydı göster');
  assert.match(p.$('[data-event-id="ordered-0"] h3').textContent, /^En yeni/);
  assert.match(p.$('[data-event-id="ordered-59"] h3').textContent, /^En eski yanıtsız/);
  p.$('#older-toggle').click();
  assert.equal(p.window.document.querySelectorAll('#events .event[hidden]').length, 0);
  const reviewing = p.$('[data-event-id="ordered-20"]');
  reviewing.open = true;
  const video = reviewing.querySelector('video');
  p.$('#older-toggle').click();
  assert.equal(reviewing.hidden, false);
  await p.refresh();
  assert.equal(reviewing.querySelector('video'), video);
  assert.equal(reviewing.open, true);
  p.$('#queue-oldest').click();
  assert.equal(p.$('[data-event-id="ordered-59"]').open, true);
  assert.equal(p.$('[data-event-id="ordered-59"]').hidden, false);
});

test('new arrivals cannot move a decision target while pointer is in the queue', async () => {
  const old = event();
  const p = await panel([old]);
  const target=p.$('[data-event-id="'+old.id+'"]');
  p.$('#event-panel').dispatchEvent(new p.window.Event('pointerenter'));
  p.state.events.unshift(event({id:'new-arrival',opened_at:old.opened_at+55}));
  await p.refresh();
  assert.equal(p.$('#events').firstElementChild,target);
  const video=target.querySelector('video');let pauses=0;Object.defineProperty(video,'paused',{value:false,configurable:true});video.pause=()=>{pauses++;};
  target.querySelector('button.reject').click();await flush();
  assert.match(p.state.posts[0].url,new RegExp(old.id));
  assert.equal(pauses,1);
});

test('keyboard focus defers new cards, then leaving applies arrivals with a notice', async()=>{
  const old=event();const p=await panel([old]);
  const target=p.$('[data-event-id="'+old.id+'"]');target.querySelector('button.reject').focus();
  p.state.events.unshift(event({id:'keyboard-arrival',opened_at:old.opened_at+55}));await p.refresh();
  assert.equal(p.$('#events').firstElementChild,target);
  assert.equal(p.$('#queue-arrivals').hidden,false);
  p.$('#pending-summary').focus();await flush();
  assert.equal(p.$('#events').firstElementChild.dataset.eventId,'keyboard-arrival');
  assert.equal(p.$('#queue-arrivals').hidden,true);
});

test('profile explains its intended smoke scale and effective configuration beside measured timings', async () => {
  const p = await panel();
  p.state.status.analysis_profile = {name:'field',input_size:640,confidence:.25,analysis_hz:1/6,interval_seconds:6,event_timeout_seconds:36,required_detections:3,window_analyses:5};
  await p.refresh();
  assert.match(p.$('#analysis-profile').textContent, /Saha profili/);
  assert.match(p.$('#analysis-profile').textContent, /küçük.*uzak/i);
  assert.match(p.$('#profile-parameters').textContent, /640.*%25.*6 sn.*36 sn/);
  p.state.status.analysis_profile = {...p.state.status.analysis_profile,name:'demo',input_size:192,confidence:.35,interval_seconds:1,event_timeout_seconds:12};
  await p.refresh();
  assert.match(p.$('#analysis-profile').textContent, /Demo profili.*yakın/i);
  assert.match(p.$('#profile-parameters').textContent, /192.*%35.*1 sn/);
  p.state.fail = true; await p.refresh();
  assert.match(p.$('#analysis-profile').textContent, /bilinmiyor/);
});

test('mounted inactive camera is a tile without a frame request and LED state uses a static swatch', async () => {
  const p = await panel();
  const tile = p.$('#inactive-cameras .camera');
  assert.match(tile.textContent, /Sağ.*takılı, bağlı değil/);
  assert.equal(tile.querySelector('img'), null);
  p.state.status.mcu = {simulated:true,flame_sensor:{status_text:'Alev sensörü normal'},led:{shown:{colour:'amber',pattern:'steady',text:'Duman şüphesi operatör kararı bekliyor'}}};
  await p.refresh();
  assert.match(p.$('#mcu-mode').textContent, /Simülasyon/);
  assert.equal(p.$('#led-swatch').dataset.colour, 'amber');
});

test('after a decision, leaving the queue opens the next pending record without moving the clicked target', async () => {
  const first = event({id:'first',opened_at:1700000010});
  const second = event({id:'second',opened_at:1700000000});
  const p = await panel([first,second]);
  p.$('#event-panel').dispatchEvent(new p.window.Event('pointerenter'));
  const clicked = p.$('[data-event-id="first"] .confirm');
  clicked.click(); await flush();
  assert.ok(p.$('[data-event-id="first"]').contains(clicked) || p.$('[data-event-id="first"] .decision'));
  assert.equal(p.$('[data-event-id="second"]').open,false);
  p.$('#event-panel').dispatchEvent(new p.window.Event('pointerleave'));
  p.window.document.activeElement?.blur(); await flush();
  assert.equal(p.$('[data-event-id="second"]').open,true);
  assert.match(p.$('[data-event-id="second"] summary').textContent,/Kaydı daralt/);
});

test('one completed analysis reports its time but waits for a second analysis before showing a measured rate', async () => {
  const p = await panel();
  p.state.status.cameras[0].analyses = 1;
  p.state.status.cameras[0].analysis_hz = 0;
  await p.refresh();
  assert.match(p.$('.camera-info').textContent,/54,8 ms/);
  assert.match(p.$('.camera-info').textContent,/— analiz\/sn/);
  p.state.status.cameras[0].analyses = 2;
  p.state.status.cameras[0].analysis_hz = 1/6;
  await p.refresh();
  assert.match(p.$('.camera-info').textContent,/0,17 analiz\/sn/);
});


test('old pending behind newest 200 decided records remains reviewable with truthful total', async () => {
  const old = event({id:'hidden-old', opened_at:1, clip:webm});
  const p = await panel([...Array.from({length:200}, (_,i) => event({id:`decided-${i}`,opened_at:1000-i,decision:'rejected'})), old]);
  assert.equal(p.$('#event-count').textContent, '1 karar bekliyor');
  const row = p.$('[data-event-id="hidden-old"]');
  assert.ok(row && row.parentNode === p.$('#events'));
  row.querySelector('.confirm').click(); await flush();
  assert.equal(p.$('#event-count').textContent, '0 karar bekliyor');
  assert.equal(p.state.posts[0].url, '/api/events/hidden-old/decision');
});

test('bounded pending pages reach all 405 records and global oldest/newest with stable decisions and video', async () => {
  const p = await panel(Array.from({length:405}, (_,i) => event({id:`pending-${String(i).padStart(3,'0')}`,opened_at:1000-i,clip:webm})));
  assert.equal(p.$('#event-count').textContent, '405 karar bekliyor');
  assert.equal(p.window.document.querySelectorAll('#events .event').length,200);
  assert.equal(p.$('#queue-next-page').hidden, false);
  const watched = p.$('#events .event video');
  await p.refresh(); assert.equal(p.$('#events .event video'),watched);
  p.$('#queue-next-page').click(); await flush();
  assert.ok(p.$('[data-event-id="pending-200"]'));
  assert.equal(p.window.document.querySelectorAll('#events .event').length,200);
  p.$('#queue-next-page').click(); await flush();
  assert.ok(p.$('[data-event-id="pending-404"]'));
  assert.equal(p.$('#queue-next-page').hidden, true);
  p.$('#queue-oldest').click(); await flush();
  assert.equal(p.$('#events .event').dataset.eventId,'pending-404');
  assert.equal(p.$('#events .event').open,true);
  p.$('#events .confirm').click(); await flush();
  assert.equal(p.$('#event-count').textContent, '404 karar bekliyor');
  p.$('#queue-newest').click(); await flush();
  assert.equal(p.$('#events .event').dataset.eventId,'pending-000');
  assert.equal(p.$('#event-count').textContent, '404 karar bekliyor');
});

test('jump to oldest during an in-flight poll focuses the newly loaded global page', async () => {
  const p = await panel(Array.from({length:405}, (_,i) => event({id:`pending-${String(i).padStart(3,'0')}`,opened_at:1000-i})));
  const original = p.window.fetch;
  let release;
  p.window.fetch = (url, init) => {
    if (url === '/api/status' && !release) return new Promise(resolve => {release=()=>resolve(original(url,init));});
    return original(url,init);
  };
  const polling = p.refresh(); await flush();
  p.$('#queue-oldest').click(); await flush();
  release(); await polling; await flush();
  const oldest = p.$('#events .event');
  assert.equal(oldest.dataset.eventId, 'pending-404');
  assert.equal(oldest.open, true);
  assert.ok(p.window.document.activeElement === oldest.querySelector('summary'), 'focus must follow the newly loaded page');
});


test('successful poll restores attached usable queue while pointer remains across connection loss', async () => {
  const p = await panel([event()]);
  const panelElement = p.$('#event-panel');
  const row = p.$('#events .event');
  panelElement.dispatchEvent(new p.window.Event('pointerenter'));
  p.state.fail = true; await p.refresh();
  assert.equal(row.isConnected, false);
  assert.equal(p.$('#events').getAttribute('aria-busy'), 'true');
  p.state.fail = false; await p.refresh();
  assert.match(p.$('#connection').textContent, /İstasyon bağlı/);
  assert.ok(p.$('#events .event') === row, 'recovery reattaches the existing row');
  assert.equal(row.isConnected, true);
  assert.equal(p.$('#events').getAttribute('aria-busy'), 'false');
  assert.ok(p.$('#events .confirm'));
  assert.equal(p.$('#queue-arrivals').hidden, true);
  // Subsequent ordinary arrivals still defer under the held pointer.
  p.state.events.unshift(event({id:'after-recovery',opened_at:1700000100}));
  await p.refresh();
  assert.equal(p.$('#events').firstElementChild, row);
  assert.equal(p.$('#queue-arrivals').hidden, false);
});


test('runtime death and retention faults are visible separately from live camera capture', async () => {
  const p = await panel();
  p.state.status.runtime = {state:'failed',analysis_running:false,error:'Analysis loop stopped unexpectedly',retention_error:null};
  await p.refresh();
  assert.equal(p.$('#system-warning').hidden, false);
  assert.match(p.$('#system-warning').textContent,/Analiz kesintisi/);
  p.state.status.runtime = {state:'running',analysis_running:true,error:null,retention_error:'Retention unavailable'};
  await p.refresh();
  assert.match(p.$('#system-warning').textContent,/Kayıt bakımı/);
  assert.match(p.$('.camera-info').textContent,/54,8 ms/);
  p.state.status.runtime.retention_error = null; await p.refresh();
  assert.equal(p.$('#system-warning').hidden, true);
});
