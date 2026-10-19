// Research database: renders window.STUDIES with technology, condition and study-type filters, and CSV export.
// research.html?t=<technology>&c=<condition> opens the list pre-filtered (the home page links use it).
(function(){
  // Strongest designs first (reviews, then trials, then the rest), newest first within each.
  const rank = d => /meta|systematic/i.test(d) ? 0 : d === 'RCT' ? 1 : d === 'Clinical study' ? 2 : d === 'Review' ? 3 : 4;
  const all = (window.STUDIES || []).slice().sort((a, b) => rank(a.design) - rank(b.design) || (+b.year) - (+a.year));
  const conditions = window.CONDITIONS || [];
  const label = Object.fromEntries(conditions);
  const techs = [['pemf', 'PEMF'], ['shockwave', 'Shockwave'], ['combined', 'PEMF and shockwave']];
  const techLabel = Object.fromEntries(techs);
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
  const params = new URLSearchParams(location.search);
  let type = 'all';
  let cond = params.get('c') || 'all';
  let tech = params.get('t') || 'all';
  if (cond !== 'all' && !label[cond]) cond = 'all';
  if (tech !== 'all' && !techLabel[tech]) tech = 'all';

  function button(box, text, pressed, onclick){
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = text;
    b.setAttribute('aria-pressed', pressed);
    b.onclick = () => { box.querySelectorAll('button').forEach(x => x.setAttribute('aria-pressed', x === b)); onclick(); render(); };
    box.appendChild(b);
  }
  const tbox = document.getElementById('tfilters');
  if (tbox) {
    button(tbox, 'All (' + all.length + ')', tech === 'all', () => { tech = 'all'; });
    techs.forEach(([key, text]) => {
      const n = all.filter(s => (s.technology || 'pemf') === key).length;
      if (n) button(tbox, text + ' (' + n + ')', key === tech, () => { tech = key; });
    });
  }
  const cbox = document.getElementById('cfilters');
  if (cbox) {
    button(cbox, 'All conditions', cond === 'all', () => { cond = 'all'; });
    conditions.forEach(([key, text]) => {
      const n = all.filter(s => s.condition === key).length;
      if (n) button(cbox, text + ' (' + n + ')', key === cond, () => { cond = key; });
    });
  }
  const fbox = document.getElementById('filters');
  groups.forEach(([key, text, test]) => {
    const n = all.filter(test).length;
    if (n) button(fbox, text + ' (' + n + ')', key === type, () => { type = key; });
  });

  function render(){
    const test = groups.find(g => g[0] === type)[2];
    const rows = all.filter(s => test(s) && (cond === 'all' || s.condition === cond) && (tech === 'all' || (s.technology || 'pemf') === tech));
    count.textContent = rows.length + (rows.length === 1 ? ' study' : ' studies');
    const url = new URL(location.href);
    if (cond === 'all') url.searchParams.delete('c'); else url.searchParams.set('c', cond);
    if (tech === 'all') url.searchParams.delete('t'); else url.searchParams.set('t', tech);
    history.replaceState(null, '', url);
    list.innerHTML = rows.map(s =>
      '<li><div class="meta"><b>' + esc(s.design) + '</b>' + esc(s.year || '') + (s.n ? ' · ' + num(s.n) + ' participants' : '') +
      '<span class="cond">' + esc(techLabel[s.technology || 'pemf']) + (s.condition ? ' · ' + esc(label[s.condition] || '') : '') + '</span></div>' +
      '<div><p class="desc">' + esc(s.description) + '</p><p class="inst">' + esc(s.location) + (s.journal ? ' · <i>' + esc(s.journal) + '</i>' : '') + '</p>' +
      (s.summary ? '<details><summary>Summary and why it matters</summary><p>' + esc(s.summary) + '</p><p><b>Why it matters:</b> ' + esc(s.importance) + '</p></details>' : '') +
      '</div>' +
      '<div class="lnk">' + (s.slug ? '<a class="more" href="studies/' + esc(s.slug) + '.html">Study page</a>' : '') +
      '<a class="more out" href="' + esc(s.link) + '" target="_blank" rel="noopener">Original</a></div></li>'
    ).join('') || '<li><p class="desc">No studies match these filters.</p></li>';
  }
  render();

  document.getElementById('csv').onclick = () => {
    const q = v => '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"';
    const head = ['Technology','Condition','Study type','Year','Participants','Finding','Summary','Why it matters','Institution','Journal','Link'];
    const lines = all.map(s => [techLabel[s.technology || 'pemf'], label[s.condition], s.design, s.year, s.n, s.description, s.summary, s.importance, s.location, s.journal, s.link].map(q).join(','));
    const a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob(['﻿' + [head.join(','), ...lines].join('\n')], {type:'text/csv;charset=utf-8;'}));
    a.download = 'PEMF_shockwave_research_PainFree.csv'; document.body.appendChild(a); a.click(); a.remove();
  };
})();
