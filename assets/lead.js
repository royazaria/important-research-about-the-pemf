// Contact form: posts to the shared lead endpoint on painfreeusa.health, which emails the PainFree inbox.
(function(){
  const ENDPOINT = 'https://painfreeusa.health/api/lead';
  const CONTACT_EMAIL = 'jackaa22@gmail.com';
  const f = document.getElementById('leadForm');
  if (!f) return;
  const btn = f.querySelector('button[type=submit]');
  const status = document.getElementById('formStatus');
  const v = n => (f.elements[n] && f.elements[n].value || '').trim();
  f.addEventListener('submit', async e => {
    e.preventDefault();
    f.querySelectorAll('.field').forEach(x => x.classList.remove('bad'));
    const missing = ['name','phone','email','city'].filter(n => !v(n) || (n === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v(n))));
    if (missing.length) {
      missing.forEach(n => f.elements[n].closest('.field').classList.add('bad'));
      status.className = 'note err'; status.textContent = 'Please fill in the highlighted fields.';
      f.elements[missing[0]].focus(); return;
    }
    btn.disabled = true; btn.textContent = 'Sending…';
    const data = { site: 'pemf-research.com' };
    ['role','name','phone','email','city','country','message','company_site'].forEach(n => data[n] = v(n));
    try {
      const r = await fetch(ENDPOINT, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(data)});
      if (!r.ok) throw new Error(r.status);
      const first = data.name.split(' ')[0].replace(/[<>&"]/g, '');
      f.innerHTML = '<div class="sent"><h3>Thank you, ' + first + '.</h3><p>We have your message and will get back to you.</p></div>';
    } catch (err) {
      btn.disabled = false; btn.textContent = 'Send';
      const body = 'I am: ' + data.role + '\nName: ' + data.name + '\nPhone: ' + data.phone + '\nEmail: ' + data.email + '\nCity: ' + data.city + '\nCountry: ' + data.country + '\n\n' + data.message;
      status.className = 'note err';
      status.innerHTML = 'Something went wrong on our side. Please <a href="mailto:' + CONTACT_EMAIL + '?subject=' + encodeURIComponent('PainFree inquiry') + '&body=' + encodeURIComponent(body) + '">email us instead</a>.';
    }
  });
})();
