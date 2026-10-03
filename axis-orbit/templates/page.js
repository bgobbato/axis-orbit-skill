(() => {
  const els = [...document.querySelectorAll('.count')];
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const fmt = (v, src) => {
    const dec = (src.split('.')[1] || '').length;
    const s = v.toFixed(dec);
    return src.includes(',') ? Number(s).toLocaleString('en-US', {minimumFractionDigits: dec}) : s;
  };
  const run = el => {
    const src = el.dataset.final, target = parseFloat(src.replace(/,/g, ''));
    const t0 = performance.now(), dur = 2000;
    const tick = now => {
      const p = Math.min(1, (now - t0) / dur), e = 1 - Math.pow(1 - p, 3);
      el.textContent = p < 1 ? fmt(target * e, src) : src;
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  };
  const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { run(e.target); io.unobserve(e.target); } }), {threshold: .6});
  els.forEach(el => io.observe(el));
})();