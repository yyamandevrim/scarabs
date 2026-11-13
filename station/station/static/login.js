'use strict';
document.getElementById('login').addEventListener('submit', async event => {
  event.preventDefault();
  const button = event.target.querySelector('button');
  const secret = document.getElementById('secret');
  const message = document.getElementById('message');
  button.disabled = true;
  try {
    const response = await fetch('/api/auth/login', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({secret:secret.value})});
    secret.value = '';
    if (response.ok) { window.location.assign('/'); return; }
    message.textContent = response.status === 429 ? 'Çok fazla deneme. Beş dakika bekleyin. / Wait five minutes.' : response.status === 503 ? 'İstasyonda ACORN_PANEL_SECRET ayarlayın. / Set ACORN_PANEL_SECRET on the station.' : 'Parola yanlış. / Incorrect secret.';
  } catch { message.textContent = 'İstasyona erişilemiyor. / Station unavailable.'; }
  finally { button.disabled = false; }
});
