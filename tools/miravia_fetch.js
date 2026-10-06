// Ejecutar en la pestaña del Seller Center de Miravia (inicio: https://sellercenter.miravia.es/) con la tienda abierta.
// Devuelve: tienda activa, ventas canal Miravia (Business Advisor, con IVA) de 7 días, 7 días anteriores, mes en curso (suma diaria) y 30 días,
// y del texto del inicio: ingresos 30 días de AliExpress, pedidos pendientes, sin stock y avisos de bloqueo.
// Opcional: window.__MES_CIERRE = 'YYYY-MM' para sacar también el mes cerrado.
(async () => {
  const ymd = (d) => d.toISOString().slice(0, 10);
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Madrid' }));
  const day = (n) => { const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())); d.setUTCDate(d.getUTCDate() + n); return ymd(d); };
  const ayer = day(-1);
  const g = async (q) => { const j = await fetch('/ba/sycm/arise/dashboard/key/overview.json?' + q).then(r => r.json()).catch(() => ({})); const d = j.data || {};
    return [d.payAmount ? Math.round(d.payAmount.value * 100) / 100 : null, d.paidOrderAmount ? d.paidOrderAmount.value : null, d.uv ? d.uv.value : null]; };
  const rng = (t, a, b) => `dateType=${t}&dateRange=${a}%7C${b}`;
  const out = { fecha: day(0) };
  const txt = document.body.innerText;
  out.tienda = (txt.match(/Mi cuenta\s*\n[^\n]*\n([^\n]+)\nIngresos de los últimos 30 días/) || [])[1] || null;
  out.d7 = await g(rng('recent7', day(-7), ayer));
  out.p7 = await g(rng('recent7', day(-14), day(-8)));
  out.d30 = await g(rng('recent30', day(-30), ayer));
  let s = 0, o = 0, dd = ayer.slice(0, 8) + '01';
  while (dd <= ayer) { const r = await g(rng('day', dd, dd)); s += r[0] || 0; o += r[1] || 0; const x = new Date(dd + 'T00:00:00Z'); x.setUTCDate(x.getUTCDate() + 1); dd = ymd(x); }
  out.mtd = [Math.round(s * 100) / 100, o];
  if (window.__MES_CIERRE) { const [y, m] = window.__MES_CIERRE.split('-').map(Number); out.mes = await g(rng('month', `${window.__MES_CIERRE}-01`, ymd(new Date(Date.UTC(y, m, 0))))); }
  const num = (re) => { const m = txt.match(re); return m ? parseFloat(m[1].replace(',', '.')) : null; };
  out.ae_d30 = num(/AliExpress\s*\nIngresos de los últimos 30 días:\s*([\d.,]+)/);
  out.mv_d30_inicio = num(/Miravia\s*\nIngresos de los últimos 30 días:\s*([\d.,]+)/);
  out.pendientes = num(/Pedidos\s*\n(\d+)\s*\nPedidos pendientes/);
  out.sin_stock = num(/Sin stock\s*\n(\d+)/);
  out.top_sin_stock = num(/Tiene (\d+) productos más vendidos de los últimos 7 días actualmente sin stock/);
  out.aviso_bloqueo = /bloqueados en España/.test(txt) ? 'Todos los productos de esta tienda están bloqueados en España' : null;
  return JSON.stringify(out);
})()
