// Research database: renders window.STUDIES with study-type filters and CSV export.
(function(){
  const all = (window.STUDIES || []).slice();
  const groups = [
    ['all', 'All', () => true],
    ['reviews', 'Reviews and meta-analyses', s => /meta|systematic/i.test(s.design)],
    ['trials', 'Randomized trials', s => s.design === 'RCT'],
    ['other', 'Other studies', s => !/meta|systematic/i.test(s.design) && s.design !== 'RCT'],
  ];
  const esc = s => String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
  const num = n => (n == null || n === '') ? '' : Number(n).toLocaleString('en-US');
  const list = document.getElementById('list');
  const count = document.getElementById('count');
  const filters = document.getElementById('filters');
  let current = 'all';

  groups.forEach(([key, label, test]) => {
    const n = all.filter(test).length;
    if (!n) return;
    const b = document.createElement('button');
    b.type = 'button'; b.dataset.k = key;
    b.textContent = label + ' (' + n + ')';
    b.setAttribute('aria-pressed', key === current);
    b.onclick = () => { current = key; filters.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); render(); };
    filters.appendChild(b);
  });

  function render(){
    const test = groups.find(g => g[0] === current)[2];
    const rows = all.filter(test);
    count.textContent = rows.length + (rows.length === 1 ? ' study' : ' studies');
    list.innerHTML = rows.map(s =>
      '<li><div class="meta"><b>' + esc(s.design) + '</b>' + esc(s.year || '') + (s.n ? ' · ' + num(s.n) + ' participants' : '') + '</div>' +
      '<div><p class="desc">' + esc(s.description) + '</p><p class="inst">' + esc(s.location) + (s.journal ? ' · <i>' + esc(s.journal) + '</i>' : '') + '</p></div>' +
      '<div class="lnk"><a class="more out" href="' + esc(s.link) + '" target="_blank" rel="noopener">Read the study</a></div></li>'
    ).join('');
  }
  render();

  document.getElementById('csv').onclick = () => {
    const q = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const head = ['Study type','Year','Participants','Finding','Institution','Journal','Link'];
    const lines = all.map(s => [s.design, s.year, s.n, s.description, s.location, s.journal, s.link].map(q).join(','));
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + [head.join(','), ...lines].join('\n')], {type:'text/csv;charset=utf-8;'}));
    a.download = 'PEMF_research_PainFree.csv'; document.body.appendChild(a); a.click(); a.remove();
  };
})();
