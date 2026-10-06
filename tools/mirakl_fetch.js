// Ejecutar en una pestaña del panel de Mirakl (marketplace-dashboard) con la tienda de Duérmete abierta.
// Devuelve ventas e ingresos de: últimos 7 días cerrados, 7 días anteriores, últimos 30 días y mes en curso (hasta ayer).
// Opcional: window.__MES_CIERRE = 'YYYY-MM' antes de ejecutar para sacar también el mes cerrado (con y sin IVA).
(async () => {
  const lisboa = /worten/.test(location.host);
  const tz = lisboa ? 'Europe/Lisbon' : 'Europe/Madrid';
  const off = (ymd) => { // offset +HH:MM de la zona en esa fecha
    const s = new Intl.DateTimeFormat('en-US', { timeZone: tz, timeZoneName: 'longOffset' }).formatToParts(new Date(ymd + 'T12:00:00Z')).find(p => p.type === 'timeZoneName').value;
    const m = s.match(/GMT([+-]\d{2}):?(\d{2})?/); return m ? `${m[1]}:${m[2] || '00'}` : '+00:00';
  };
  const ymd = (d) => d.toISOString().slice(0, 10);
  const today = new Date(new Date().toLocaleString('en-US', { timeZone: tz }));
  const day = (n) => { const d = new Date(Date.UTC(today.getFullYear(), today.getMonth(), today.getDate())); d.setUTCDate(d.getUTCDate() + n); return ymd(d); };
  const ayer = day(-1);
  const R = { d7: [day(-7), ayer], p7: [day(-14), day(-8)], d30: [day(-30), ayer], mtd: [ayer.slice(0, 8) + '01', ayer] };
  if (window.__MES_CIERRE) { const [y, m] = window.__MES_CIERRE.split('-').map(Number); const last = new Date(Date.UTC(y, m, 0)); R.mes = [`${window.__MES_CIERRE}-01`, ymd(last)]; }
  const q = (a, b, tax) => new URLSearchParams({ startDate: `${a}T00:00:00.000${off(a)}`, endDate: `${b}T23:59:59.999${off(b)}`, includeShippingCharges: 'true', includeTaxes: tax, showDebited: 'YES', showShipped: 'ALL' });
  const out = { tienda: document.title, host: location.host, rangos: R };
  for (const [k, [a, b]] of Object.entries(R)) {
    const s = await fetch('/marketplace-dashboard/private/sales?' + q(a, b, 'false')).then(r => r.json()).catch(() => ({}));
    const c = await fetch('/marketplace-dashboard/private/order-count?' + new URLSearchParams({ startDate: `${a}T00:00:00.000${off(a)}`, endDate: `${b}T23:59:59.999${off(b)}` })).then(r => r.json()).catch(() => ({}));
    out[k] = [s.saleRevenue ?? null, c.ordersCount ? c.ordersCount.reduce((x, y) => x + y.value, 0) : null];
    if (k === 'mes') { const t = await fetch('/marketplace-dashboard/private/sales?' + q(a, b, 'true')).then(r => r.json()).catch(() => ({})); out.mes_con_iva = t.saleRevenue ?? null; }
  }
  return JSON.stringify(out);
})()
