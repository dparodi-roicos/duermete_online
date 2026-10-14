// Amazon Seller Central ES · ventas CON IVA tal cual el «Panel de ventas» (Informes de empresa → Panel de ventas → «Ventas de productos pedidos»).
// Ejecutar en una pestaña de https://sellercentral.amazon.es/ (cuenta «Duérmete Online · España») con `await ` delante.
// Opcional: window.__MES_CIERRE = 'YYYY-MM' antes de ejecutar para sacar también ese mes completo.
// Devuelve [ventas, líneas de pedido, unidades] de: d7 = [HOY−6, HOY], p7 = [HOY−13, HOY−7], mtd = «En lo que va de mes» (incluye hoy),
// y de días cerrados d7c = [HOY−7, AYER] y mtdc = [día 1, AYER] (para el TACOS, que se calcula con la publicidad hasta ayer).
(async () => {
  const cuenta = (document.querySelector('.dropdown-account-switcher-header-label, #ngstrim-gaps-account-switcher, .partner-dropdown-button')?.innerText || '').replace(/\s+/g, ' ').trim();
  if (!/du[eé]rmete/i.test(cuenta)) return JSON.stringify({ skip: cuenta || document.title });
  const tok = document.querySelector('meta[name="anti-csrftoken-a2z"]')?.content;
  const Q = 'query salesDashboardDataQuery($input: GetSalesDashboardDataInput) { getSalesDashboardData(input: $input) { snapshotBarResponse { orderedProductSales unitsOrdered totalOrderItems } } }';
  const call = async (mode, a, b) => {
    const r = await fetch('/business-reports/api', { method: 'POST', headers: { 'content-type': 'application/json', accept: 'application/json', 'anti-csrftoken-a2z': tok },
      body: JSON.stringify({ operationName: 'salesDashboardDataQuery', variables: { input: { dashboardMode: mode, breakdownType: 'MARKETPLACE_TOTAL', fulfillment: 'BOTH', fromDate: a, endDate: b, isSundayStart: false } }, query: Q }) }).then(r => r.json());
    const s = r.data.getSalesDashboardData.snapshotBarResponse;
    return [s.orderedProductSales, s.totalOrderItems, s.unitsOrdered];
  };
  const ymd = (d) => d.toISOString().slice(0, 10);
  const now = new Date(new Date().toLocaleString('en-US', { timeZone: 'Europe/Madrid' }));
  const day = (n) => { const d = new Date(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())); d.setUTCDate(d.getUTCDate() + n); return ymd(d); };
  const hoy = day(0), m1 = hoy.slice(0, 8) + '01';
  const out = { cuenta, rangos: { d7: [day(-6), hoy], p7: [day(-13), day(-7)], mtd: [m1, hoy], ads_d7: [day(-7), day(-1)], ads_mtd: [m1 < hoy ? m1 : day(-1), day(-1)] } };
  out.d7 = await call('CUSTOM', day(-6), hoy);
  out.p7 = await call('CUSTOM', day(-13), day(-7));
  out.mtd = await call('MONTH_TO_DATE', hoy, hoy);
  out.d7c = await call('CUSTOM', day(-7), day(-1));
  out.mtdc = m1 < hoy ? await call('CUSTOM', m1, day(-1)) : [0, 0, 0];
  if (window.__MES_CIERRE) { const [y, m] = window.__MES_CIERRE.split('-').map(Number); out.mes = await call('CUSTOM', `${window.__MES_CIERRE}-01`, ymd(new Date(Date.UTC(y, m, 0)))); }
  out.hora = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' }).format(new Date());
  return JSON.stringify(out);
})()
