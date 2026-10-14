// Amazon Seller Central ES · estado de la cuenta, listings, Buy Box y SellerFlex.
// Ejecutar en una pestaña de https://sellercentral.amazon.es/ (cuenta «Duérmete Online · España») con `await ` delante.
// Devuelve JSON con: cuenta, estado (salud de la cuenta), listings (recuentos), buybox, sellerflex.
(async () => {
  const cuenta = (document.querySelector('.dropdown-account-switcher-header-label, #ngstrim-gaps-account-switcher, .partner-dropdown-button')?.innerText || '').replace(/\s+/g, ' ').trim();
  if (!/du[eé]rmete/i.test(cuenta)) return JSON.stringify({ skip: cuenta || document.title });
  const tok = document.querySelector('meta[name="anti-csrftoken-a2z"]')?.content;
  // --- Inventario (misma consulta que «Gestión de todo el inventario», solo los campos necesarios)
  const Q = `query getListingsV2($pagination: PaginationInput, $multiSelectFilters: [MultiSelectFilter], $sortRequest: SortRequest) { listingsV2(pagination: $pagination usecase: MANAGE_INVENTORY_VIEW multiSelectFilters: $multiSelectFilters sortRequest: $sortRequest features: ["EML_CDQ_ENABLED"]) { count listings { coreListingFields { asin sku fulfillmentChannel } listingData { title last30DayUnitsSold last30DayGms } availability { quantity inbound } status { status statusText } pricing { competitionState { buyBoxPrice { price { amount } shipping { amount } } } } offers { ... on Offer3P { price { price { amount } } salePrice { price { amount } } } } } } }`;
  const page = async (st, from, size) => {
    const r = await fetch('/myinventory/gql', { method: 'POST', headers: { accept: 'application/json', 'content-type': 'application/json', 'anti-csrftoken-a2z': tok },
      body: JSON.stringify({ operationName: 'getListingsV2', query: Q, variables: { pagination: { from, size }, sortRequest: { key: 'CREATE_DATE', order: 'DESCENDING' },
        multiSelectFilters: [{ key: 'LISTING_STATUS', values: [st] }, { key: 'FULFILLMENT', values: ['AllChannels'] }, { key: 'CONDITION', values: [] }] } }) }).then(r => r.json());
    if (!r.data) throw new Error(JSON.stringify(r.errors || r).slice(0, 200));
    return r.data.listingsV2;
  };
  const all = async (st) => { const out = []; let n = 0; for (let f = 0; f < 5000; f += 100) { const p = await page(st, f, 100); n = p.count; out.push(...p.listings); if (p.listings.length < 100) break; } return { n, ls: out }; };
  const cnt = async (st) => (await page(st, 0, 1)).count;
  const act = await all('Active');
  const oos = await all('OutOfStock');
  const sku = (l) => l.coreListingFields.sku, afn = (l) => l.coreListingFields.fulfillmentChannel === 'AFN';
  const titulo = (l) => (l.listingData.title || '').replace(/^DU[EÉ]RMETE ONLINE\s*-\s*/i, '').split(',')[0].slice(0, 90);
  const listings = { activos: act.n, sellerflex: act.ls.filter(afn).length, fbm: act.ls.filter(l => !afn(l)).length,
    inactivos: null, agotados: oos.n, suprimidos: null, falta_info: null, todos: null };
  for (const [k, st] of [['inactivos', 'Inactive'], ['suprimidos', 'SearchSuppressed'], ['falta_info', 'Incomplete'], ['todos', 'All']]) {
    try { listings[k] = await cnt(st); } catch (e) { listings[k] = null; }
  }
  // --- Buy Box (oferta destacada) de los activos
  const bb = (l) => { const b = l.pricing?.competitionState?.buyBoxPrice; return b ? +b.price.amount + +(b.shipping?.amount || 0) : null; };
  const sin = act.ls.filter(l => bb(l) == null);
  const buybox = { con: act.n - sin.length, total: act.n, sin: sin.length,
    sin_top: sin.sort((a, b) => (b.listingData.last30DayUnitsSold || 0) - (a.listingData.last30DayUnitsSold || 0)).slice(0, 10)
      .map(l => ({ sku: sku(l), asin: l.coreListingFields.asin, titulo: titulo(l), uds30: l.listingData.last30DayUnitsSold || 0, precio: +(l.offers?.[0]?.price?.price?.amount || 0) })) };
  // --- SellerFlex: agotados que han vendido en 30 días y activos con poco stock
  const sf_agot = oos.ls.filter(l => afn(l) && (l.listingData.last30DayUnitsSold || 0) > 0)
    .sort((a, b) => (b.listingData.last30DayGms || 0) - (a.listingData.last30DayGms || 0))
    .map(l => ({ sku: sku(l), titulo: titulo(l), uds30: l.listingData.last30DayUnitsSold, ventas30: l.listingData.last30DayGms || 0, entrante: l.availability?.inbound || 0 }));
  const sf_bajo = act.ls.filter(l => afn(l) && (l.availability?.quantity || 0) < 50)
    .sort((a, b) => (a.availability?.quantity || 0) - (b.availability?.quantity || 0))
    .map(l => ({ sku: sku(l), titulo: titulo(l), stock: l.availability?.quantity || 0, uds30: l.listingData.last30DayUnitsSold || 0 }));
  const sellerflex = { activos: listings.sellerflex, agotados: oos.ls.filter(afn).length, agotados_con_ventas: sf_agot, stock_bajo: sf_bajo };
  // --- Estado de la cuenta (página /performance/dashboard)
  const h = await fetch('/performance/dashboard').then(r => r.text()).catch(() => '');
  const d = new DOMParser().parseFromString(h, 'text/html');
  d.querySelectorAll('script,style,noscript,template').forEach(e => e.remove());
  const lines = []; const tw = d.createTreeWalker(d.body || d, NodeFilter.SHOW_TEXT); // documento sin renderizar: un nodo de texto = una línea
  while (tw.nextNode()) { const v = tw.currentNode.nodeValue.replace(/\s+/g, ' ').trim(); if (v) lines.push(v); }
  const after = (lab, n = 1) => { const i = lines.findIndex(s => s === lab); return i >= 0 ? lines[i + n] : null; };
  const estado = { texto: null, nivel: null, cumplimiento: null, odr: null, odr_det: null, incidencias: {} };
  const iN = lines.findIndex(s => /^Nivel del estado de la cuenta$/.test(s));
  if (iN >= 0) estado.nivel = (lines.slice(iN + 1, iN + 6).find(s => /^\d{1,4}$/.test(s)) || null);
  estado.cumplimiento = after('Cumplimiento de políticas');
  const iO = lines.findIndex(s => s === 'Ratio de pedidos defectuosos');
  if (iO >= 0) { const seg = lines.slice(iO, iO + 8); const pct = seg.filter(s => /%$/.test(s) && !/Objetivo/.test(s)); estado.odr = pct[pct.length - 1] || null; estado.odr_det = seg.find(s => /pedidos$/.test(s)) || null; }
  for (const lab of ['Supuestas infracciones de la propiedad intelectual', 'Reclamaciones sobre propiedad intelectual', 'Reclamaciones por autenticidad del producto',
    'Reclamaciones por estado del producto', 'Problemas relativos a la seguridad de productos y alimentos', 'Incumplimiento de la política de publicación',
    'Infracciones de la política de productos excluidos', 'Incumplimiento de la política sobre reseñas de productos', 'Otros incumplimientos de políticas', 'Cumplimiento normativo']) {
    const v = after(lab); if (v != null && /^\d+$/.test(v)) estado.incidencias[lab] = +v;
  }
  const cab = [...document.querySelectorAll('a,div,span')].map(e => (e.innerText || '').replace(/\s+/g, ' ').trim()).find(x => /^Estado de la cuenta \S/.test(x) && x.length < 50);
  estado.texto = cab ? cab.replace(/^Estado de la cuenta /, '') : null; // distintivo de la cabecera de Seller Central
  const hora = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' }).format(new Date());
  return JSON.stringify({ cuenta, hora, estado, listings, buybox, sellerflex });
})()
