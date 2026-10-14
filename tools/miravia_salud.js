// Miravia · estado de la tienda (Estado de la cuenta + penalizaciones), canal Miravia y canal AliExpress.
// Ejecutar en una pestaña de https://sellercenter.miravia.es/ con `await ` delante. Abre 4 páginas del Seller Center en marcos ocultos y lee el texto renderizado.
(async () => {
  const load = (path) => new Promise((res) => {
    const f = document.createElement('iframe');
    f.style.cssText = 'position:fixed;left:-5000px;top:0;width:1400px;height:1200px;';
    f.src = path; document.body.appendChild(f);
    let n = 0;
    const tick = () => {
      let t = ''; try { t = f.contentDocument.body.innerText || ''; } catch (e) {}
      const ok = /Ver detalles de la métrica|Penalizaciones recibidas/.test(t) && (!/mypenalty/.test(path) || f.contentDocument.querySelector('tbody tr') || /No hay datos|Sin datos/.test(t));
      if ((ok && n > 4) || n > 40) { const rows = [...(f.contentDocument?.querySelectorAll('tbody tr') || [])].map(r => r.innerText.replace(/\s+/g, ' ').trim()); f.remove(); res({ t, rows }); }
      else { n++; setTimeout(tick, 500); }
    };
    setTimeout(tick, 1500);
  });
  const L = (t) => t.split('\n').map(s => s.replace(/\t/g, '').trim()).filter(Boolean);
  const metr = (lines, labs) => {
    const o = {};
    for (const [k, lab] of labs) {
      const i = lines.findIndex(s => s === lab);
      if (i < 0) { o[k] = null; continue; }
      const seg = lines.slice(i + 1, i + 4);
      const obj = seg.find(s => /^[≥≤<>]/.test(s)) || null;
      const val = seg.find(s => /^(\d+(\.\d+)?%|--)$/.test(s)) || null;
      o[k] = { v: val === '--' ? null : val, obj };
    }
    return o;
  };
  const tienda = (document.body.innerText.match(/Mi cuenta\s*\n(?:[^\n]*\n)?([^\n]+)\nIngresos de los últimos 30 días/) || [])[1] || null;
  const [hm, ha, pm, pa] = [await load('/apps/seller/account_health?businessType=miravia'), await load('/apps/seller/account_health?businessType=ae'),
    await load('/apps/seller/mypenalty?businessType=miravia&category=ongoing_penalty'), await load('/apps/seller/mypenalty?businessType=ae&category=ongoing_penalty')];
  const lm = L(hm.t), la = L(ha.t), lpa = L(pa.t);
  const num = (lines, lab) => { const i = lines.findIndex(s => s === lab); return i >= 0 && /^\d+$/.test(lines[i + 1]) ? +lines[i + 1] : null; };
  const out = { tienda, revision: (hm.t.match(/Momento de la revisión:\s*([\d-]+ [\d:]+)/) || [])[1] || null,
    pen_mv: num(lm, 'Miravia'), pen_ae: num(lm, 'AliExpress'), impacto_gmv: (hm.t.match(/Impacto en GMV:\s*\n?\s*([\d.,]+)/) || [])[1] || null };
  out.mv = metr(lm, [['envio_plazo', 'Ratio de envíos en plazo'], ['sin_preparar', 'Ratio de paquetes sin preparar'], ['entrega_tiempo', 'Ratio de entrega a tiempo'],
    ['cancelaciones', 'Ratio de cancelaciones'], ['devoluciones', 'Ratio de devoluciones'], ['valoraciones', 'Ratio de valoraciones del vendedor'], ['chat', 'Ratio de respuesta del chat de tienda']]);
  out.ae = metr(la, [['no_verificados', 'Ratio de envíos no verificados'], ['envio_plazo', 'Ratio de envíos en plazo (2 días hábiles)'], ['escaneo72', 'Ratio de escaneo en 72 horas'],
    ['entrega_tiempo', 'Ratio de entrega a tiempo'], ['omision', 'Ratio de omisión del envío'], ['nr', 'Ratio de pedidos no recibidos (NR)']]);
  out.politicas_mv = ['Política de catálogo y contenidos', 'Política de contenido inapropiado', 'Política de productos prohibidos y controlados', 'Política de derechos de autor y propiedad intelectual', 'Política de la cuenta de vendedor']
    .map(p => { const i = lm.findIndex(s => s === p); return [p, i >= 0 ? lm[i + 1] : null]; }).filter(([, v]) => v && v !== 'Excelente');
  const pts = (lab) => { const i = lpa.findIndex(s => s === lab); return i >= 0 && /^\d+$/.test(lpa[i + 1]) ? +lpa[i + 1] : null; };
  out.puntos_ae = { transaccion: pts('Infracciones de transacción'), producto: pts('Información del producto'),
    pi: (() => { const i = lpa.findIndex(s => /^Normas de Política de propiedad intelectual/.test(s)); return i >= 0 && /^\d+$/.test(lpa[i + 1]) ? +lpa[i + 1] : null; })() };
  const fila = (r) => {
    const fecha = (r.match(/^(\d{4}-\d{2}-\d{2})/) || [])[1];
    const desde = (r.match(/Desde (\d{4}-\d{2}-\d{2})(?: hasta (\d{4}-\d{2}-\d{2}))?/) || []);
    const estado = (r.match(/(Pendiente de apelación|Apelación rechazada|Apelación aprobada|En apelación|No requiere apelación)/) || [])[1] || null;
    const tipo = (r.match(/(Retención de pagos|Desactivación de productos|Política de transacciones y otros|Política de propiedad intelectual[^0-9]*?restringidos|Política de calidad del contenido del producto|Penalizaciones de Cuenta|Restricción de ventas[^0-9]*)/) || [])[1] || null;
    const motivo = (r.match(/(Fraude de Cumplimiento[^.]*|NR\)[^.]*|Item Not Received[^.]*|mala calidad de[^.]*|congel[^.]*|bloquea[^.]*)/i) || [])[1] || null;
    return { fecha, tipo, estado, desde: desde[1] || null, hasta: desde[2] || null, motivo: motivo ? motivo.slice(0, 160) : null };
  };
  out.pen_lista_mv = pm.rows.map(fila).filter(x => x.fecha);   // sin penalizaciones la tabla trae una fila vacía
  const ae = pa.rows.map(fila).filter(x => x.fecha);
  out.pen_lista_ae = ae.filter(x => !/propiedad intelectual/i.test(x.tipo || ''));
  out.pen_ae_pi = out.pen_ae != null ? out.pen_ae - out.pen_lista_ae.length : null;
  if (out.pen_mv == null && !pm.rows.some(r => /\d{4}-\d{2}-\d{2}/.test(r))) out.pen_mv = out.pen_lista_mv.length;   // tabla de Miravia vacía = 0 penalizaciones   // la tabla está paginada: el resto son de PI / prohibidos
  out.hora = new Intl.DateTimeFormat('es-ES', { timeZone: 'Europe/Madrid', hour: '2-digit', minute: '2-digit' }).format(new Date());
  return JSON.stringify(out);
})()
