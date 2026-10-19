// Research database: renders window.STUDIES with study-type and condition filters, and CSV export.
// research.html?c=<condition> opens the list filtered to one condition (the home page links use it).
(function(){
  const all = (window.STUDIES || []).slice();
  const conditions = window.CONDITIONS || [];
  const label = Object.fromEntries(conditions);
  const groups = [
    ['all', 'All types', () => true],
    ['reviews', 'Reviews and meta-analyses', s => /meta|systematic/i.test(s.design)],
    ['trials', 'Randomized trials', s => s.design === 'RCT'],
    ['other', 'Other studies', s => !/meta|systematic/i.test(s.design) && s.design !== 'RCT'],
  ];
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const num = n => (n == null || n === '') ? '' : Number(n).toLocaleString('en-US');
  const list = document.getElementById('list');
  const count = document.getElementById('count');
  const filters = document.getElementById('filters');
  const cfilters = document.getElementById('cfilters');
  let type = 'all';
  let cond = new URLSearchParams(location.search).get('c') || 'all';
  if (cond !== 'all' && !label[cond]) cond = 'all';

  function button(box, text, pressed, onclick){
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = text;
    b.setAttribute('aria-pressed', pressed);
    b.onclick = () => { box.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); onclick(); render(); };
    box.appendChild(b);
  }
  groups.forEach(([key, text, test]) => {
    const n = all.filter(test).length;
    if (n) button(filters, text + ' (' + n + ')', key === type, () => { type = key; });
  });
  if (cfilters) {
    button(cfilters, 'All conditions', cond === 'all', () => { cond = 'all'; });
    conditions.forEach(([key, text]) => {
      const n = all.filter(s => s.condition === key).length;
      if (n) button(cfilters, text + ' (' + n + ')', key === cond, () => { cond = key; });
    });
  }

  function render(){
    const test = groups.find(g => g[0] === type)[2];
    const rows = all.filter(s => test(s) && (cond === 'all' || s.condition === cond));
    count.textContent = rows.length + (rows.length === 1 ? ' study' : ' studies');
    const url = new URL(location.href);
    if (cond === 'all') url.searchParams.delete('c'); else url.searchParams.set('c', cond);
    history.replaceState(null, '', url);
    list.innerHTML = rows.map(s =>
      '<li><div class="meta"><b>' + esc(s.design) + '</b>' + esc(s.year || '') + (s.n ? ' · ' + num(s.n) + ' participants' : '') +
      (s.condition ? '<span class="cond">' + esc(label[s.condition] || '') + '</span>' : '') + '</div>' +
      '<div><p class="desc">' + esc(s.description) + '</p><p class="inst">' + esc(s.location) + (s.journal ? ' · <i>' + esc(s.journal) + '</i>' : '') + '</p></div>' +
      '<div class="lnk"><a class="more out" href="' + esc(s.link) + '" target="_blank" rel="noopener">Read the study</a></div></li>'
    ).join('') || '<li><p class="desc">No studies match both filters.</p></li>';
  }
  render();

  document.getElementById('csv').onclick = () => {
    const q = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const head = ['Condition','Study type','Year','Participants','Finding','Institution','Journal','Link'];
    const lines = all.map(s => [label[s.condition], s.design, s.year, s.n, s.description, s.location, s.journal, s.link].map(q).join(','));
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + [head.join(','), ...lines].join('\n')], {type:'text/csv;charset=utf-8;'}));
    a.download = 'PEMF_research_PainFree.csv'; document.body.appendChild(a); a.click(); a.remove();
  };
})();
