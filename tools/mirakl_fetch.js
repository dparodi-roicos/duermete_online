// Ejecutar en una pestaña del panel de Mirakl (marketplace-dashboard) con la tienda de Duérmete abierta.
// Devuelve ventas e ingresos de: últimos 7 días, 7 días anteriores, últimos 30 días y mes en curso, INCLUYENDO HOY (igual que el panel),
// y el estado actual de la tienda (pendientes de envío, tardíos, incidencias, mensajes no leídos, saldos, alertas, ofertas activas).
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
  const hoy = day(0);
  // Igual que el panel de Mirakl: «Últimos 7/30 días» incluyen hoy
  const R = { d7: [day(-6), hoy], p7: [day(-13), day(-7)], d30: [day(-29), hoy], mtd: [hoy.slice(0, 8) + '01', hoy] };
  if (window.__MES_CIERRE) { const [y, m] = window.__MES_CIERRE.split('-').map(Number); const last = new Date(Date.UTC(y, m, 0)); R.mes = [`${window.__MES_CIERRE}-01`, ymd(last)]; }
  const q = (a, b, tax) => new URLSearchParams({ startDate: `${a}T00:00:00.000${off(a)}`, endDate: `${b}T23:59:59.999${off(b)}`, includeShippingCharges: 'true', includeTaxes: tax, showDebited: 'YES', showShipped: 'ALL' });
  const out = { tienda: document.title, host: location.host, rangos: { d7: R.d7, p7: R.p7, d30: R.d30, mtd: R.mtd } };
  const st = {};
  for (const [k, [a, b]] of Object.entries(R)) {
    const s = await fetch('/marketplace-dashboard/private/sales?' + q(a, b, 'false')).then(r => r.json()).catch(() => ({}));
    const c = await fetch('/marketplace-dashboard/private/order-count?' + new URLSearchParams({ startDate: `${a}T00:00:00.000${off(a)}`, endDate: `${b}T23:59:59.999${off(b)}` })).then(r => r.json()).catch(() => ({}));
    out[k] = [s.saleRevenue ?? null, c.ordersCount ? c.ordersCount.reduce((x, y) => x + y.value, 0) : null];
    if (k === 'd30') st.carrito = s.averageBasket ?? null;
    if (k === 'mes') { const t = await fetch('/marketplace-dashboard/private/sales?' + q(a, b, 'true')).then(r => r.json()).catch(() => ({})); out.mes_con_iva = t.saleRevenue ?? null; }
  }
  // Estado de la tienda en este momento (lo que enseña la portada del panel)
  const get = (u) => fetch(u).then(r => r.ok ? r.json() : {}).catch(() => ({}));
  const cta = await get('/marketplace-dashboard/private/call-to-action');
  Object.assign(st, { envio: cta.orderInShippingCount ?? null, tardios: cta.lateOrderCount ?? null, incid: cta.inProgressIncidentCount ?? null,
    incid_new: cta.newIncidentCount ?? null, acept: cta.orderInWaitingAcceptance ?? null, devol: cta.returnInProgressCount ?? null });
  const ib = await get('/inbox/threads/stats?computeTotalMessageCount=false&critical=COUNT&maxToCount=1001&operatorInbox=false'); // misma consulta que la portada
  st.msgs = ib.unreadThreadCount ?? null; st.msgs_crit = ib.criticalThreads ? ib.criticalThreads.count : null;
  const bal = await get('/marketplace-dashboard/private/balance');
  Object.assign(st, { pend: bal.pending ?? null, pagar: bal.payable ?? null, ult_pago: bal.lastPayment ?? null, ult_pago_f: bal.lastPaymentDate ?? null, prox_fact: bal.nextBillingDate ?? null });
  const al = await get('/marketplace-dashboard/private/shop-alerting');
  st.alerta = al.kind ? { k: al.kind, r: al.rules || [] } : null;
  const po = await get('/marketplace-dashboard/private/performance-overview?' + q(R.d7[0], R.d7[1], 'false'));
  const pe = (po.performanceOverviewEntries || []).filter(x => x.activeOffersCount != null);
  st.ofertas = pe.length ? pe[pe.length - 1].activeOffersCount : null;
  st.hora = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' }).format(new Date());
  out.estado = st;
  return JSON.stringify(out);
})()
