// Ejecutar en una pestaña del panel de Mirakl (marketplace-dashboard) con la tienda de Duérmete abierta.
// Devuelve ventas como la portada del panel («Impuestos no incluidos» = sin IVA, portes incluidos; Carrefour, MdM y Brico van con IVA porque no lo separan) de: últimos 7 días, 7 días anteriores, últimos 30 días y mes en curso, INCLUYENDO HOY (igual que el panel),
// y el estado actual de la tienda (pendientes de envío, tardíos, incidencias, mensajes no leídos, saldos, alertas, ofertas activas).
// Opcional: window.__MES_CIERRE = 'YYYY-MM' antes de ejecutar para sacar también el mes cerrado (con y sin IVA).
(async () => {
  if (!/du[eé]rmete|dreaming online/i.test(document.title)) return JSON.stringify({ skip: document.title, host: location.host });   // otra tienda (p. ej. TUELEKTRO) o login: no usar
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
    const s = await fetch('/marketplace-dashboard/private/sales?' + q(a, b, 'false')).then(r => r.json()).catch(() => ({}));   // «Impuestos no incluidos» (= sin IVA), como la portada del panel; Carrefour, MdM y Brico no separan el IVA
    const c = await fetch('/marketplace-dashboard/private/order-count?' + new URLSearchParams({ startDate: `${a}T00:00:00.000${off(a)}`, endDate: `${b}T23:59:59.999${off(b)}` })).then(r => r.json()).catch(() => ({}));
    out[k] = [s.saleRevenue ?? null, c.ordersCount ? c.ordersCount.reduce((x, y) => x + y.value, 0) : null];
    if (k === 'd7') st.carrito = s.averageBasket ?? null;   // «Media Carr.» de la portada con el filtro «Últimos 7 días»
    if (k === 'mes') { const t = await fetch('/marketplace-dashboard/private/sales?' + q(a, b, 'true')).then(r => r.json()).catch(() => ({})); out.mes_con_iva = t.saleRevenue ?? null; }
  }
  // Estado de la tienda en este momento (lo que enseña la portada del panel)
  const get = (u) => fetch(u).then(r => r.ok ? r.json() : {}).catch(() => ({}));
  const cta = await get('/marketplace-dashboard/private/call-to-action');
  Object.assign(st, { envio: cta.orderInShippingCount ?? null, tardios: cta.lateOrderCount ?? null, incid: cta.inProgressIncidentCount ?? null,
    incid_new: cta.newIncidentCount ?? null, acept: cta.orderInWaitingAcceptance ?? null, devol: cta.returnInProgressCount ?? null,
    incid_disp: cta.disputedIncidentEnabled ? (cta.disputedIncidentCount ?? null) : null, devol_sol: cta.returnsEnabled ? (cta.returnWaitingAcceptanceCount ?? null) : null });
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
  // Control de calidad (bloque «Control de calidad» de la portada): valoración, KYC, reglas de premium/suspensión y estadísticas de 7 y 30 días
  const sd = await get('/marketplace-dashboard/private/shop-detail');
  const pr = await get('/marketplace-dashboard/private/platform-rules');
  const reglas = (l) => (l || []).map(x => [x.criterion, x.currentValue, x.threshold, x.satisfyRule, x.period]);
  const r2 = (v) => v == null ? null : Math.round(v * 100) / 100;   // el panel enseña las tasas con 2 decimales y los tiempos en d/h/min
  const stats = async ([a, b]) => { const s = await get('/marketplace-dashboard/private/quality-control/statistics?' + new URLSearchParams({ startDate: `${a}T00:00:00.000${off(a)}`, endDate: `${b}T23:59:59.999${off(b)}` }));
    return s.totalOrders == null ? null : { ped: s.totalOrders, rech: r2(s.autoRefusedRate), t_acept_s: s.acceptanceTimeInSeconds ?? null, acept: r2(s.acceptanceRate), cancel: r2(s.cancelationRate),
      incid: r2(s.incidentRate), resp_s: s.responseTimeInSeconds ?? null, tard: r2(s.lateShipmentRate), reemb: r2(s.refundRate), devol: s.isReturnsEnabledForPlatformModel ? r2(s.returnRate) : 'off',
      envio_s: s.timeToShipInSeconds ?? null, track: r2(s.trackingRate) }; };
  const kycTxt = String(sd.shopKyc?.reason || '').replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ');
  out.calidad = { nota: sd.grade ?? null, valoraciones: sd.evaluationsCount ?? null, premium: pr.premium ?? sd.premium ?? null, suspendida: pr.suspended ?? null, estado: sd.state ?? null,
    kyc: sd.shopKyc?.status ?? null, falta_2fa: /two-factor|dos factores|2FA/i.test(kycTxt),
    premium_reglas: reglas(pr.premiumRules), suspension_reglas: reglas(pr.suspensionRules), s7: await stats(R.d7), s30: await stats(R.d30) };
  return JSON.stringify(out);
})()
