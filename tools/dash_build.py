import re, html, json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = os.path.join(ROOT, 'index.html')
src = open(os.path.join(ROOT, 'tools', 'base_1oct.html'), encoding='utf-8').read()   # plantilla base (versión del 1-oct)
H = json.load(open(os.path.join(ROOT, 'cierres.json'), encoding='utf-8'))             # histórico de cierres de mes

# ---------------- formato ----------------
def e(n, d=0):
    if n is None: return '-'
    s = f'{n:,.{d}f}'
    return s.replace(',', 'X').replace('.', ',').replace('X', '.')
def eur(n, d=0): return '-' if n is None else e(n, d) + '€'
def pct(a, b):
    if a is None or not b: return None
    return (a / b - 1) * 100
def delta(a, b, label='vs 7 días anteriores'):
    p = pct(a, b)
    if p is None: return ''
    cls = 'up' if p >= 0 else 'dn'
    return f"<span class='dl {cls}'>{'+' if p >= 0 else '−'}{e(abs(p), 1)}%</span> {label}"
MES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep']

# ---------------- componentes ----------------
def tile(label, value, sub='', cls=''):
    return f"<div class='mtr {cls}'><div class='mtr-label'>{label}</div><div class='mtr-value'>{value}</div>" + (f"<div class='mtr-sub'>{sub}</div>" if sub else '') + "</div>"
def block(title, period, tiles, note=''):
    return (f"<section class='blk'><div class='blk-head'><h2>{title}</h2><span class='blk-per'>{period}</span></div>"
            f"<div class='mtr-grid'>{''.join(tiles)}</div>" + (f"<div class='blk-note'>{note}</div>" if note else '') + "</section>")
def status(items):
    return "<div class='status'>" + ''.join(f"<div class='st'><span class='st-l'>{l}</span><span class='st-v {c}'>{v}</span></div>" for l, v, c in items) + "</div>"

def nice_max(v):
    if v <= 0: return 1
    import math
    p = 10 ** math.floor(math.log10(v));
    for m in (1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10):
        if m * p >= v: return m * p
def kfmt(v):
    if v >= 1000: return e(v / 1000, 0 if v >= 10000 else 1) + 'k'
    return e(v)

def bar_chart(vals, labels=MES, unit='€'):
    """vals: list with None = sin dato"""
    W, H, pl, pr, pt, pb = 1040, 250, 50, 12, 24, 26
    mx = nice_max(max([v for v in vals if v] or [1]))
    n = len(vals); bw = (W - pl - pr) / n
    g = []
    for k in range(5):
        y = pt + (H - pt - pb) * k / 4; val = mx * (1 - k / 4)
        g.append(f"<line x1='{pl}' x2='{W-pr}' y1='{y:.1f}' y2='{y:.1f}' class='gl'/><text x='{pl-6}' y='{y+4:.1f}' class='ax' text-anchor='end'>{kfmt(val)}</text>")
    for i, v in enumerate(vals):
        x = pl + i * bw + bw * 0.2; w = bw * 0.6; cx = x + w / 2
        g.append(f"<text x='{cx:.1f}' y='{H-8}' class='ax' text-anchor='middle'>{labels[i]}</text>")
        if v is None:
            g.append(f"<text x='{cx:.1f}' y='{H-pb-6}' class='ax' text-anchor='middle'>-</text>"); continue
        h = (H - pt - pb) * v / mx; y = H - pb - h
        g.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{max(h,0):.1f}' rx='3' class='b1'><title>{labels[i]}: {eur(v)}</title></rect>")
        g.append(f"<text x='{cx:.1f}' y='{y-5:.1f}' class='bl' text-anchor='middle'>{kfmt(v)}</text>")
    return f"<svg viewBox='0 0 {W} {H}' role='img'>{''.join(g)}</svg>"

def ads_chart(spend, sales, labels=MES):
    """barras = ventas por Ads (eje izq.), línea = inversión (eje dcho.)"""
    W, H, pl, pr, pt, pb = 1040, 260, 50, 50, 24, 26
    ms = nice_max(max([v for v in sales if v] or [1])); mi = nice_max(max([v for v in spend if v] or [1]))
    n = len(labels); bw = (W - pl - pr) / n
    g = []
    for k in range(5):
        y = pt + (H - pt - pb) * k / 4
        g.append(f"<line x1='{pl}' x2='{W-pr}' y1='{y:.1f}' y2='{y:.1f}' class='gl'/><text x='{pl-6}' y='{y+4:.1f}' class='ax' text-anchor='end'>{kfmt(ms*(1-k/4))}</text>"
                 f"<text x='{W-pr+6}' y='{y+4:.1f}' class='ax ax2'>{kfmt(mi*(1-k/4))}</text>")
    pts = []
    for i in range(n):
        x = pl + i * bw + bw * 0.22; w = bw * 0.56; cx = x + w / 2
        g.append(f"<text x='{cx:.1f}' y='{H-8}' class='ax' text-anchor='middle'>{labels[i]}</text>")
        v = sales[i]
        if v is not None:
            h = (H - pt - pb) * v / ms; y = H - pb - h
            g.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{w:.1f}' height='{max(h,0):.1f}' rx='3' class='b2'><title>{labels[i]} · ventas por Ads {eur(v)}</title></rect>")
        s = spend[i]
        if s is not None:
            y2 = H - pb - (H - pt - pb) * s / mi; pts.append((cx, y2, s, v))
        elif v is None:
            g.append(f"<text x='{cx:.1f}' y='{H-pb-6}' class='ax' text-anchor='middle'>-</text>")
    if pts:
        g.append("<polyline class='ln' points='" + ' '.join(f'{x:.1f},{y:.1f}' for x, y, _, _ in pts) + "'/>")
        for x, y, s, v in pts:
            ac = f" · ACOS {e(s / v * 100, 1)}%" if v else ''
            g.append(f"<circle cx='{x:.1f}' cy='{y:.1f}' r='4' class='dt'><title>Inversión {eur(s)}{ac}</title></circle><text x='{x:.1f}' y='{y-9:.1f}' class='bl bl2' text-anchor='middle'>{kfmt(s)}</text>")
    return f"<svg viewBox='0 0 {W} {H}' role='img'>{''.join(g)}</svg>"

def chart_card(title, svg, note='', legend=''):
    return (f"<section class='chart-card'><div class='blk-head'><h2>{title}</h2>{legend}</div><div class='chart'>{svg}</div>"
            + (f"<div class='blk-note'>{note}</div>" if note else '') + "</section>")
LEG_ADS = "<span class='leg'><i class='lg b2'></i>Ventas por Ads <i class='lg ln'></i>Inversión (eje dcho.)</span>"

def sub_sep(title):
    return f"<div class='sep-title'>{title}</div>"

MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
def ratio(a, b, lab):
    return f'{lab} {e(a / b * 100, 1)}%' if a and b else ''
def cierre(pid):
    h = H[pid]; ms = sorted(h['meses']); last = ms[-1]
    tabs = ''.join(f"<button class='mtab{' on' if m == last else ''}' data-m='{m}' onclick=\"selMes('{pid}','{m}')\">{MESES[int(m[5:]) - 1][:3]}</button>" for m in ms)
    bodies = []
    for m in ms:
        d = h['meses'][m]
        if h['tipo'] == 'mk':
            ped = re.search(r'(\d[\d.]*) (pedidos|líneas)', d.get('det_sin') or '')   # nº de pedidos/líneas guardado en el detalle
            ts = [tile('Ventas con IVA', eur(d['con'], 2) if d['con'] is not None else '-', ' · '.join(x for x in [d.get('det_con', ''), ped.group(0) if ped else ''] if x), 'v-ok' if d['con'] else 'v-muted'),
                  tile('Inversión en publicidad', eur(d['inv'], 2) if d['inv'] is not None else '-', d.get('det_inv', ''), 'v-warn' if d['inv'] else 'v-muted'),
                  tile('Ventas por publicidad', eur(d['vpub'], 2) if d['vpub'] is not None else '-',
                       ' · '.join(x for x in [ratio(d['inv'], d['vpub'], 'ACOS'), ratio(d['inv'], d['con'], 'TACOS')] if x), '' if d['vpub'] else 'v-muted')]
        else:
            inv = None if d['inv_mv'] is None and d['inv_ae'] is None else (d['inv_mv'] or 0) + (d['inv_ae'] or 0)
            vp = None if d['vpub_mv'] is None and d['vpub_ae'] is None else (d['vpub_mv'] or 0) + (d['vpub_ae'] or 0)
            sub = lambda a, b, la, lb: ' · '.join(f'{l} {eur(v, 2)}' for l, v in ((la, a), (lb, b)) if v is not None)
            ts = [tile('Facturación total', eur(d['tot_con'], 2) if d['tot_con'] is not None else '-', 'Con IVA · Miravia + AliExpress', 'v-ok' if d['tot_con'] else 'v-muted'),
                  tile('Miravia', eur(d['mv_con'], 2) if d['mv_con'] is not None else '-',
                       'Con IVA' + (' · ' + re.sub(r'^Con IVA · ', '', d['det_mv']) if d.get('det_mv') else ''), 'v-ok' if d['mv_con'] else 'v-muted'),
                  tile('AliExpress', eur(d['ae_con'], 2) if d['ae_con'] is not None else '-',
                       ('Con IVA · ' if d['ae_con'] is not None else '') + d.get('det_ae', ''), 'v-ok' if d['ae_con'] else 'v-muted'),
                  tile('Inversión total en anuncios', eur(inv, 2) if inv is not None else '-',
                       sub(d['inv_mv'], d['inv_ae'], 'Miravia', 'AliExpress') + (' · ' + d['det_inv'] if d.get('det_inv') else ''), 'v-warn' if inv else 'v-muted'),
                  tile('Ventas por anuncios', eur(vp, 2) if vp is not None else '-',
                       sub(d['vpub_mv'], d['vpub_ae'], 'Miravia', 'AliExpress') + (f' · ROAS {e(vp / inv, 2)}' if vp and inv else ''), '' if vp else 'v-muted')]
        bodies.append(f"<div class='mc' data-m='{m}'{'' if m == last else ' hidden'}><div class='mtr-grid'>{''.join(ts)}</div></div>")
    return (f"<section class='blk cierre' id='cierre-{pid}'><div class='blk-head'><h2>Cierre de mes</h2>"
            f"<div class='mtabs' role='tablist'>{tabs}</div></div>{''.join(bodies)}</section>")

# =====================================================================
# DATOS: diario.json (bloques de arriba) + cierres.json (gráficos e histórico)
# =====================================================================
import datetime as _dt
D = json.load(open(os.path.join(ROOT, 'diario.json'), encoding='utf-8'))
_MC = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
def fd(s): d = _dt.date.fromisoformat(s); return f'{d.day} {_MC[d.month - 1]}'
def rango(k): a, b = D['periodo'][k]; return f'{fd(a)} – {fd(b)}'
P7, PMTD, P30 = rango('d7'), rango('mtd'), rango('d30')
MES_ACTUAL = MESES[_dt.date.fromisoformat(D['periodo']['mtd'][0]).month - 1]
ACT = fd(D['actualizado'])

def serie(pid, campo, alt=None):
    ms = sorted(H[pid]['meses']); vals = []
    for m in ms:
        v = H[pid]['meses'][m].get(campo)
        if v is None and alt: v = H[pid]['meses'][m].get(alt)
        vals.append(v)
    return vals, [MESES[int(m[5:]) - 1][:3] for m in ms]
def titulo_evol(pid, txt='Evolución de ventas'):
    ms = sorted(H[pid]['meses'])
    return f"{txt} · {MESES[int(ms[0][5:]) - 1].lower()} a {MESES[int(ms[-1][5:]) - 1].lower()} {ms[-1][:4]}"

# ---------------- AMAZON ----------------
A = D['amazon']; ES = A['estado']
amz_status = status([('Estado de la cuenta', f"{ES['nivel']} · {ES['texto']}", 'ok'), ('Listings activos', e(ES['listings_activos']), ''),
                     ('Buy Box', ES['buybox'], 'ok'), ('Agotados con ventas', e(ES['agotados_con_ventas']), 'crit' if ES['agotados_con_ventas'] else ''),
                     ('Inactivos otros', e(ES['inactivos_otros']), '')])
a7, am = A['d7'], A['mtd']
def acos(i, v): return f"ACOS {e(i / v * 100, 1)}%" if i and v else ''
def tacos(i, v): return f"TACOS {e(i / v * 100, 1)}%" if i and v else ''
AR = A.get('rangos') or {}   # periodos de Seller Central (incluyen hoy, como el Panel de ventas)
def arango(k, base):
    if k not in AR: return base
    a, b = AR[k]; t = f'{fd(a)} – {fd(b)}'
    return t + (f" · hoy hasta las {A['hora']}" if b == D['actualizado'] and A.get('hora') else '')
AP7, APMTD = arango('d7', P7), arango('mtd', PMTD)
ADS7, ADSMTD = (f"{fd(AR['ads_d7'][0])} – {fd(AR['ads_d7'][1])}", f"{fd(AR['ads_mtd'][0])} – {fd(AR['ads_mtd'][1])}") if 'ads_d7' in AR else (P7, PMTD)
amz_con, LB = serie('amazon', 'con'); amz_inv, _ = serie('amazon', 'inv'); amz_vp, _ = serie('amazon', 'vpub')
amz_top = (
    amz_status
    + "<div class='blk-row'>"
    + block('Últimos 7 días', AP7, [
        tile('Ventas', eur(a7['ventas'], 2), delta(a7['ventas'], A['p7']['ventas']) + f" · {e(a7['lineas'])} líneas · {e(a7['uds'])} uds", 'v-ok'),
        tile('Inversión Ads', eur(a7['ads_inv'], 2), f'Sponsored Products · {ADS7} (días cerrados)', 'v-warn'),
        tile('Ventas por Ads', eur(a7['ads_ventas'], 2), ' · '.join(x for x in [acos(a7['ads_inv'], a7['ads_ventas']), tacos(a7['ads_inv'], a7.get('ventas_cerr', a7['ventas']))] if x) + f' · {ADS7}')])
    + block(f'{MES_ACTUAL} hasta la fecha', APMTD, [
        tile('Ventas', eur(am['ventas'], 2), f"{e(am['lineas'])} líneas · {e(am['uds'])} uds", 'v-ok'),
        tile('Inversión Ads', eur(am['ads_inv'], 2), f'{ADSMTD} (días cerrados)', 'v-warn'),
        tile('Ventas por Ads', eur(am['ads_ventas'], 2), ' · '.join(x for x in [acos(am['ads_inv'], am['ads_ventas']), tacos(am['ads_inv'], am.get('ventas_cerr', am['ventas']))] if x) + ' · aún sube: Amazon atribuye ventas hasta 14 días después del clic')],
        'Ventas con IVA: «Ventas de productos pedidos» del Panel de ventas de Seller Central (mismas fechas) · publicidad de la API de Amazon Ads hasta ayer')
    + "</div>"
    + "<div class='chart-row'>"
    + chart_card(titulo_evol('amazon'), bar_chart(amz_con, LB),
                 'Con IVA · Seller Central, Panel de ventas («Ventas de productos pedidos») · sin ventas de enero a marzo')
    + chart_card('Inversión en Ads y ventas por Ads', ads_chart(amz_inv, amz_vp, LB),
                 'API de Amazon Ads · sin datos de publicidad antes de abril', LEG_ADS)
    + "</div>" + cierre('amazon') + sub_sep('Estado de la cuenta')
)

# ---------------- MIRAKL ----------------
MK = {
 'cfe':  dict(name='Carrefour ES', div=1, ads='No gestionamos su publicidad', iva='con IVA (Carrefour no desglosa impuestos)'),
 'cfr':  dict(name='Carrefour FR', div=1, ads='No gestionamos su publicidad', iva='con IVA (Carrefour no desglosa impuestos)'),
 'adeo': dict(name='Leroy Merlin', div=1, ads='Lo gestiona Valiuz (externo) · sin informe de gasto'),
 'cfib': dict(name='Conforama ES', div=1, ads='El panel no tiene módulo de publicidad'),
 'conforama': dict(name='Conforama FR', div=1, ads='Sin campañas'),
 'worten': dict(name='Worten PT', div=1, ads='Mirakl Ads', lisboa=True, con_ads=True),
 'mdm':  dict(name='Maisons du Monde', div=1, ads='Sin campañas', iva='con IVA (el panel no desglosa impuestos)'),
 'brico': dict(name='Brico Dépôt', div=1, ads='El panel no tiene módulo de publicidad'),
}
for k in MK: MK[k].update(D['mirakl'][k])
def mk_top(key):
    d = MK[key]; dv = d['div']
    s7, o7 = d['d7']; sp, op = d['p7']; s30, o30 = d['d30']; sm, om = d['mtd']
    ped = lambda o: '' if o is None else f' · {e(o)} pedidos'
    rg = d.get('rangos')
    hora = d.get('hora_ventas') or (d.get('estado') or {}).get('hora')   # hora a la que se leyeron las ventas
    def per(k, base):
        if not rg or k not in rg: return base
        a, b = rg[k]; txt = f'{fd(a)} – {fd(b)}'
        return txt + (f' · hoy hasta las {hora}' if b == d.get('fecha') and hora else ' · incluye hoy')
    P7, P30, PMTD = per('d7', globals()['P7']), per('d30', globals()['P30']), per('mtd', globals()['PMTD'])
    a7 = d.get('ads_d7')
    if d.get('con_ads') and a7:
        ads7 = tile('Inversión Ads', eur(a7['inv'], 2), f"Mirakl Ads · últimos 7 días · ventas {eur(a7['ventas'], 2)} · {e(a7.get('pedidos'))} pedidos · ROAS {e(a7.get('roas'), 1)} · ACoS {e(a7.get('acos'), 1)}% (datos del {fd(a7['fecha'])})", 'v-warn')
    elif d.get('con_ads'): ads7 = tile('Inversión Ads', '-', 'Mirakl Ads · pendiente de consultar el panel de publicidad', 'v-muted')
    else: ads7 = tile('Publicidad', '-', d['ads'], 'v-muted')
    tz = 'hora de Lisboa' if d.get('lisboa') else 'hora de Madrid'
    stale = f" · datos del {fd(d['fecha'])}" if d.get('fecha') and d['fecha'] != D['actualizado'] else ''
    blocks = ("<div class='blk-row'>"
        + block('Últimos 7 días', P7 + stale, [tile('Ventas', eur(s7 / dv), (delta(s7, sp) or 'sin ventas') + ped(o7), 'v-ok' if s7 else 'v-muted'), ads7])
        + block('Últimos 30 días', P30 + stale, [tile('Ventas', eur(s30 / dv), ped(o30).lstrip(' ·'), 'v-ok' if s30 else 'v-muted'),
                                         tile(f'{MES_ACTUAL} hasta la fecha', eur(sm / dv), PMTD + ped(om), '')])
        + "</div>")
    vals, lb = serie(key, 'con', 'sin')
    charts = "<div class='chart-row'>" + chart_card(titulo_evol(key), bar_chart(vals, lb),
        f"Ingresos por ventas del panel, con IVA y portes incluidos, {tz} · " + (d['iva'] if 'iva' in d else 'en el panel: «Configuración del valor bruto de mercancías» → «Con impuestos incluidos»') + ' · 7 días, 30 días y mes en curso: igual que el panel de Mirakl, incluyen el día de hoy hasta la hora de la actualización' if d.get('rangos') else ' · 7 días, 30 días y mes en curso: días cerrados, hoy no cuenta')
    inv, lb = serie(key, 'inv'); vp, _ = serie(key, 'vpub')
    if any(v for v in inv):
        charts += chart_card('Inversión en Ads y ventas por Ads', ads_chart(inv, vp, lb), 'Mirakl Ads · sin datos de publicidad antes de julio', LEG_ADS)
    else:
        charts += chart_card('Inversión en Ads y ventas por Ads', "<div class='empty'>Sin datos de publicidad</div>", d['ads'])
    charts += "</div>"
    cal = f"Control de calidad · {fd(d['fecha'])} a las {(d.get('estado') or {}).get('hora', '-')}" if d.get('calidad') else 'Auditoría de calidad · 1 oct 2026 (foto fija, no se actualiza)'
    C = d.get('calidad') or {}; al = (d.get('estado') or {}).get('alerta') or {}
    susp = ''
    if (C.get('suspendida') or C.get('estado') == 'SUSPENDED') and al.get('k') != 'SUSPENSION':   # si la alerta ya es de suspensión, el banner lo pone mk_estado
        k = KYC.get(C.get('kyc'), (C.get('kyc') or '-', ''))[0]
        susp = (f"<div class='banner b-crit'><span class='banner-icon'>🚫</span><div><span class='banner-title'>Tienda suspendida por el marketplace · KYC: {html.escape(k.lower())}</span>"
                f"<span class='banner-sub'>Portada de Mirakl ({fd(d['fecha'])} a las {(d.get('estado') or {}).get('hora', '-')}) · el panel no indica el motivo de la suspensión</span></div></div>")
    return susp + blocks + mk_estado(d) + charts + cierre(key) + sub_sep(cal)

CRIT = {'EVALUATION_GRADE': ('Clasificación', '★', True), 'INCIDENT_RATE': ('Tasa de incidencias', '%', False), 'ACCEPTATION_DELAY': ('Tiempo de aceptación', 'h', False),
        'ACCEPTATION_RATE': ('Porcentaje de aceptación', '%', True), 'REFUND_RATE': ('Tasa de reembolsos', '%', False), 'MESSAGE_RESPONSE_TIME': ('Tiempo de respuesta a mensajes', 'h', False),
        'ORDERS_SHIPPED_LATE_RATE': ('Envíos tardíos', '%', False), 'ABORTED_COUNT': ('Pedidos rechazados automáticamente', '', False), 'VALID_TRACKING_RATE': ('Seguimiento válido', '%', True)}
PERIODO = {'LAST_SIX_MONTHS': '6 meses', 'LAST_THREE_MONTHS': '3 meses', 'LAST_MONTH': 'último mes', 'LAST_YEAR': '12 meses', 'ALL_SINCE_BEGINNING': 'desde el inicio'}
KYC = {'APPROVED': ('Aprobado', 'k-ok'), 'PENDING_SUBMISSION': ('Pendiente de enviar la documentación', 'k-crit'), 'PENDING_APPROVAL': ('En revisión', 'k-warn'), 'REFUSED': ('Rechazado', 'k-crit')}
def mk_calidad(key):
    """Control de calidad de la portada de Mirakl (shop-detail + platform-rules + quality-control/statistics)."""
    d = MK[key]; C = d['calidad']
    def kcard(t, rows): return f'<div class="kpi-card">\n    <div class="kpi-head">{t}</div>\n    <table class="kpi-table">\n      ' + '\n      '.join(rows) + '\n    </table>\n  </div>'
    def tr(a, b, c='', cls=''): return f'<tr><td>{a}</td><td class="{cls}">{b}</td><td>{c}</td></tr>'
    def val(v, u):
        if v is None: return '-'
        x = float(v); t = e(x, 2 if u == '★' else (0 if x == int(x) else 1))
        return t + ('★' if u == '★' else (' h' if u == 'h' else u))
    def regla(r, tipo):
        c, v, th, ok, per = r; lab, u, mayor = CRIT.get(c, (c, '', False))
        lim = (('Mínimo ≥ ' if mayor else 'Límite < ') + val(th, u)) if tipo == 'premium' else ('Suspende si ' + ('< ' if mayor else '≥ ') + val(th, u))
        verd = 'sin datos' if v is None else ('✓ cumple' if ok else '❌ no cumple')
        return tr(f"{lab} · {PERIODO.get(per, per)}", val(v, u), f"{lim} · {verd}", '' if v is None else ('k-ok' if ok else 'k-crit'))
    estado = 'Suspendida' if C.get('suspendida') or C.get('estado') == 'SUSPENDED' else 'Abierta'
    kyc, kcls = KYC.get(C.get('kyc'), (C.get('kyc') or '-', ''))
    rows = [tr('Estado de la tienda', estado, 'Suspensión aplicada por el marketplace' if estado == 'Suspendida' else 'Vendiendo', 'k-crit' if estado == 'Suspendida' else 'k-ok'),
            tr('Tienda premium', 'Sí' if C.get('premium') else 'No', 'Cumple todas las reglas de premium' if C.get('premium') else 'No cumple todas las reglas de premium', 'k-ok' if C.get('premium') else ''),
            tr('Valoración de la tienda', val(C.get('nota'), '★'), f"{e(C.get('valoraciones'))} valoraciones" if C.get('valoraciones') else 'Sin valoraciones', ''),
            tr('KYC', kyc, 'Verificación de la empresa', kcls)]
    if C.get('falta_2fa'): rows.append(tr('Autenticación en dos pasos (2FA)', 'Pendiente', 'El panel pide activarla (Strong Customer Authentication)', 'k-warn'))
    cards = [kcard('Resumen de la tienda', rows)]
    if C.get('premium_reglas'): cards.append(kcard('Reglas de premium', [regla(r, 'premium') for r in C['premium_reglas']]))
    if C.get('suspension_reglas'): cards.append(kcard('Reglas de suspensión', [regla(r, 'susp') for r in C['suspension_reglas']]))
    s7, s30 = C.get('s7') or {}, C.get('s30') or {}
    if s30.get('ped') or s7.get('ped'):
        def srow(lab, k, u):
            a, b = s30.get(k), s7.get(k)
            if a is None and b is None: return None
            return tr(lab, val(a, u), f"Últimos 7 días: {val(b, u)}", 'k-crit' if k == 'tard' and (a or 0) >= 10 else '')
        st = [srow('Envíos tardíos', 'tard', '%'), srow('Tasa de incidencias', 'incid', '%'), srow('Porcentaje de aceptación', 'acept', '%'), srow('Tiempo de aceptación', 't_acept', 'h'),
              srow('Tiempo de respuesta', 'resp', 'h'), srow('Plazo de envío', 'envio', 'h'), srow('Tasa de reembolsos', 'reemb', '%'), srow('Tasa de devoluciones', 'devol', '%'),
              srow('Tasa de cancelación', 'cancel', '%'), srow('Rechazos automáticos', 'rech', '%'), srow('Seguimiento', 'track', '%')]
        cards.append(kcard(f"Estadísticas · últimos 30 días ({e(s30.get('ped'))} pedidos) · 7 días ({e(s7.get('ped'))} pedidos)", [r for r in st if r]))
    acts = []
    al = (d.get('estado') or {}).get('alerta') or {}
    if estado == 'Suspendida': acts.append(('p-urg', 'Urgente', 'Tienda suspendida' + (' — ' + html.escape(' · '.join(al.get('r') or [])) if al.get('r') else '')))
    for r in C.get('suspension_reglas') or []:
        if r[1] is not None and not r[3]:
            lab, u, _ = CRIT.get(r[0], (r[0], '', False))
            acts.append(('p-urg', 'Urgente', f"Regla de suspensión incumplida: {lab} {val(r[1], u)} ({PERIODO.get(r[4], r[4])})"))
    if C.get('kyc') and C['kyc'] != 'APPROVED': acts.append(('p-hi', 'Alta', f"KYC: {kyc.lower()}"))
    if (s30.get('tard') or 0) >= 10: acts.append(('p-hi', 'Alta', f"Envíos tardíos {e(s30['tard'], 1)}% en 30 días ({val(s7.get('tard'), '%')} en 7 días)"))
    fallos = [CRIT.get(r[0], (r[0],))[0].lower() for r in C.get('premium_reglas') or [] if r[1] is not None and not r[3]]
    if fallos: acts.append(('p-med', 'Media', 'Premium: no cumple ' + ', '.join(fallos)))
    if C.get('falta_2fa'): acts.append(('p-lo', 'Baja', 'Activar la autenticación en dos pasos que pide el panel'))
    acc = ('\n  <div class="actions">\n    <div class="kpi-head" style="padding:11px 16px;border-bottom:1px solid var(--border);background:var(--surface-2);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted)">Puntos de atención</div>\n'
           + '\n'.join(f'    <div class="action"><span class="pri {c}">{p}</span><span class="action-txt">{t}</span></div>' for c, p, t in acts) + '\n  </div>') if acts else ''
    return '  ' + '\n  '.join(cards) + acc

def mk_estado(d):
    st = d.get('estado')
    if not st:
        return "<div class='blk-row'>" + block('Estado de la tienda', '-', [tile('Sin datos', '-', 'Se rellena en la próxima actualización diaria', 'v-muted')]) + "</div>"
    num = lambda v: '-' if v is None else e(v)
    warn = lambda v, crit=False: 'v-muted' if v is None else ('v-ok' if v == 0 else ('v-crit' if crit else 'v-warn'))
    al = st.get('alerta') or {}
    banner = ''
    if al.get('k') and al['k'] not in ('NONE', 'OK'):
        reglas = ' · '.join(al.get('r') or []) or al['k']
        cls, ico = ('b-crit', '⛔') if al['k'] in ('ALERT', 'SUSPENSION') else ('b-warn', '⚠️')
        if al['k'] == 'SUSPENSION': reglas = 'tienda suspendida · ' + reglas
        banner = (f"<div class='banner {cls}'><span class='banner-icon'>{ico}</span><div><span class='banner-title'>Alerta del panel: {html.escape(reglas)}</span>"
                  f"<span class='banner-sub'>Aviso de la portada de Mirakl ({fd(d['fecha'])} a las {st.get('hora', '-')})</span></div></div>")
    prox = f"Próxima facturación {fd(st['prox_fact'])}" if st.get('prox_fact') else ''
    ult = f"Pagado el {fd(st['ult_pago_f'])}" if st.get('ult_pago_f') else 'Sin pagos registrados en el panel'
    tiles = [
        tile('Pdte envío', num(st.get('envio')), 'Pedidos en preparación', warn(st.get('envio'))),
        tile('Tardíos', num(st.get('tardios')), 'Fuera de plazo de envío', warn(st.get('tardios'), True)),
        tile('Incid. en curso', num(st.get('incid')), '', warn(st.get('incid'))),
        tile('Nuevas incid.', num(st.get('incid_new')), '', warn(st.get('incid_new'), True)),
        tile('Msgs no leídos', num(st.get('msgs')), f"{num(st.get('msgs_crit'))} críticos" if st.get('msgs_crit') is not None else 'Conversaciones sin leer', warn(st.get('msgs'))),
        tile('Pdte aceptación', num(st.get('acept')), '', warn(st.get('acept'))),
        tile('Devoluciones en curso', num(st.get('devol')), '', warn(st.get('devol'))),
        tile('Ofertas activas', num(st.get('ofertas')), '', ''),
        tile('Media carrito 30d', eur(st.get('carrito') or None), 'Ingresos ÷ pedidos del panel' if st.get('carrito') else 'Sin pedidos en 30 días', ''),
        tile('Saldo pendiente', eur(st.get('pend'), 2), 'Pendiente de liberar', ''),
        tile('Saldo a pagar', eur(st.get('pagar'), 2), prox, ''),
        tile('Último pago', eur(st.get('ult_pago'), 2), ult, '')]
    return banner + "<div class='blk-row'>" + block('Estado de la tienda', f"hoy {fd(d['fecha'])} a las {st.get('hora', '-')}", tiles,
                                                   'Portada del panel de Mirakl en el momento de la actualización diaria') + "</div>"

# ---------------- MIRAVIA ----------------
def mv_top(pid):
    m = D['miravia'][pid]; act = fd(m['fecha'])
    banner = (f"<div class='banner b-crit'><span class='banner-icon'>⛔</span><div><span class='banner-title'>{html.escape(m['aviso'])}</span>"
              f"<span class='banner-sub'>Aviso del Seller Center ({act})</span></div></div>") if m.get('aviso') else ''
    ad = m['ads_d7']
    ads_tile = (tile('Anuncios Miravia', eur(ad['inv'], 2), f"Sponsored Discovery · {ad['periodo']} · ingresos {eur(ad['ventas'], 2)}" + (f" · ROAS {e(ad['ventas'] / ad['inv'], 2)}" if ad['inv'] else ''), 'v-warn' if ad['inv'] else 'v-muted')
                if ad.get('inv') is not None else tile('Anuncios Miravia', '-', 'Pendiente', 'v-muted'))
    stale = '' if m['fecha'] == D['actualizado'] else f" · datos del {act}"
    t7 = [tile('Ventas Miravia', eur(m['d7'][0], 2), delta(m['d7'][0], m['p7'][0]) + f" · {e(m['d7'][1])} pedidos", 'v-ok'),
          tile('Ventas AliExpress', '-', 'Sin desglose de 7 días en el panel', 'v-muted'), ads_tile]
    if pid == 'somnia-mv':
        aa = m.get('ae_ads_d7')
        t7.append(tile('AliExpress Ads', eur(aa['inv'], 2), f"{aa['periodo']} · ventas {eur(aa['ventas'], 2)} · {e(aa.get('pedidos'))} pedidos" + (f" · ROAS {e(aa['roas'], 2)} (panel)" if aa.get('roas') is not None else ''), 'v-warn')
                  if aa else tile('AliExpress Ads', '-', 'Pendiente de consultar el panel de AliExpress Ads', 'v-muted'))
    top = (banner + "<div class='blk-row'>"
        + block('Últimos 7 días', P7 + stale, t7)
        + block('Últimos 30 días', f'{P30}{stale}', [
            tile('Total 30d Miravia + AliExpress', eur((m['d30'][0] or 0) + (m['ae_d30'] or 0), 2) if m['d30'][0] is not None and m['ae_d30'] is not None else '-', 'Con IVA · suma de los dos canales', 'v-ok'),
            tile('Revenue 30d Miravia', eur(m['d30'][0], 2), f"{e(m['d30'][1])} pedidos", 'v-ok'),
            tile('Revenue 30d AliExpress', eur(m['ae_d30'], 2), 'Inicio del Seller Center', 'v-ok'),
            tile('Tráfico 30d', e(m['uv_d30']), 'Visitantes únicos · canal Miravia', ''),
            tile('Pedidos pendientes', e(m['pendientes']), f'Aviso del inicio del Seller Center ({act})', 'v-warn' if m['pendientes'] else ''),
            tile('Sin stock', e(m['sin_stock']), m.get('sin_stock_nota', ''), 'v-warn' if m['sin_stock'] else '')])
        + "</div>")
    vals, lb = serie(pid, 'mv_con')
    charts = "<div class='chart-row'>" + chart_card(titulo_evol(pid, 'Evolución de ventas Miravia'), bar_chart(vals, lb),
        'Canal Miravia · con IVA (Business Advisor; septiembre: pedidos creados sin cancelados) · AliExpress: el panel solo publica los ingresos de los últimos 30 días, sin histórico mensual')
    for camp, tit, nota in (('mv', 'Anuncios Miravia · inversión y ventas', 'Sponsored Discovery · sin datos antes de julio'),
                            ('ae', 'AliExpress Ads · inversión y ventas', 'Panel de AliExpress Ads · sin datos antes de julio')):
        inv, lb = serie(pid, 'inv_' + camp); vp, _ = serie(pid, 'vpub_' + camp)
        if any(v for v in inv): charts += chart_card(tit, ads_chart(inv, vp, lb), nota, LEG_ADS)
        elif camp == 'mv': charts += chart_card(tit, "<div class='empty'>Sin gasto en anuncios</div>", 'Sponsored Discovery sin gasto')
    charts += "</div>"
    return top + charts + cierre(pid) + sub_sep('Estado de la tienda')
som_top, do_top = mv_top('somnia-mv'), mv_top('duermete-mv')

def mv_salud(pid):
    """Estado de la tienda de Miravia (canal Miravia + AliExpress) a partir de miravia.<pid>.salud."""
    S = D['miravia'][pid]['salud']; F = fd(S['fecha']) + (f" · {S['hora']}" if S.get('hora') else '')
    def pv(x): return float(x.rstrip('%')) if x else None
    def okm(v, obj):   # cumple el objetivo
        if v is None or not obj: return None
        o = float(re.sub(r'[^\d.]', '', obj)); return v >= o if obj[0] in '≥>' else v <= o if obj[0] == '≤' else v < o
    def mrow(lab, m, extra=''):
        if not m: return ''
        v = pv(m['v']); ok = okm(v, m['obj'])
        cls = '' if ok is None else 'k-ok' if ok else 'k-crit'
        return f"<tr><td>{lab}</td><td class=\"{cls}\">{m['v'] or '-'}</td><td>Objetivo {html.escape(m['obj'] or '-')} · {'✓ OK' if ok else '❌ KO' if ok is False else 'sin datos'}{extra}</td></tr>"
    def kcard(t, rows): return f"<div class=\"kpi-card\">\n    <div class=\"kpi-head\">{t}</div>\n    <table class=\"kpi-table\">\n      " + '\n      '.join(r for r in rows if r) + "\n    </table>\n  </div>"
    TRAD = {'Item Not Received (NR) of your store’s overseas fulfillment orders has exceeded the platform’s assessment standard':
            'pedidos no recibidos (NR) de envíos internacionales por encima del estándar: AliExpress restringe las líneas 3PL a países de alto riesgo'}
    def fpen(p):
        p = dict(p, motivo=TRAD.get(p.get('motivo'), p.get('motivo')))
        per = (f"del {fd(p['desde'])} al {fd(p['hasta'])}" if p.get('hasta') else f"desde {fd(p['desde'])}") if p.get('desde') else ''
        return ' · '.join(x for x in [per, html.escape(p.get('motivo') or ''), html.escape(p.get('estado') or '')] if x)
    hoy = D['actualizado']
    activa = lambda p: p.get('hasta') and p['hasta'] >= hoy
    pen = [f"<tr><td>Miravia · {html.escape(p['tipo'] or '-')} ({fd(p['fecha'])})</td><td class=\"{'k-crit' if activa(p) else 'k-warn'}\">{'En curso' if activa(p) else 'Histórica'}</td><td>{fpen(p)}</td></tr>" for p in S['pen_lista_mv']]
    pen += [f"<tr><td>AliExpress · {html.escape(p['tipo'] or '-')} ({fd(p['fecha'])})</td><td class=\"{'k-crit' if activa(p) else 'k-warn'}\">{'En curso' if activa(p) else 'Histórica'}</td><td>{fpen(p)}</td></tr>" for p in S['pen_lista_ae']]
    if S.get('pen_ae_pi'): pen.append(f"<tr><td>AliExpress · propiedad intelectual / prohibidos</td><td class=\"k-warn\">{e(S['pen_ae_pi'])}</td><td>0 puntos · bloqueos de producto (las revisadas, en Alemania por RAP/EPR)</td></tr>")
    P = S.get('puntos_ae') or {}
    pen.append(f"<tr><td>Puntos AE · infracciones de transacción</td><td class=\"{'k-crit' if (P.get('transaccion') or 0) >= 12 else 'k-ok'}\">{e(P.get('transaccion'))} puntos</td><td>Con 12 puntos la cuenta se congela 7 días · información de producto {e(P.get('producto'))} · PI {e(P.get('pi'))}</td></tr>")
    mv, ae = S['mv'], S['ae']
    cards = [kcard(f"Penalizaciones · {e(S.get('pen_mv'))} Miravia · {e(S.get('pen_ae'))} AliExpress · {F}", pen),
             kcard(f"Calidad de servicio — Canal Miravia · revisión del panel {S.get('revision') or '-'}", [
                 mrow('Envíos en plazo', mv.get('envio_plazo')), mrow('Paquetes sin preparar', mv.get('sin_preparar')), mrow('Entrega a tiempo', mv.get('entrega_tiempo')),
                 mrow('Cancelaciones', mv.get('cancelaciones')), mrow('Devoluciones', mv.get('devoluciones')), mrow('Valoraciones del vendedor', mv.get('valoraciones')),
                 mrow('Respuesta del chat de tienda', mv.get('chat'))]
                 + [f"<tr><td>{html.escape(p)}</td><td class=\"k-warn\">{html.escape(v)}</td><td>Catálogo y conducta</td></tr>" for p, v in S.get('politicas_mv', [])]),
             kcard('Calidad de servicio — Canal AliExpress', [
                 mrow('Envíos no verificados', ae.get('no_verificados')), mrow('Envíos en plazo (2 días hábiles)', ae.get('envio_plazo')), mrow('Escaneo en 72 horas', ae.get('escaneo72')),
                 mrow('Entrega a tiempo', ae.get('entrega_tiempo')), mrow('Omisión del envío', ae.get('omision')),
                 mrow('Pedidos no recibidos (NR)', ae.get('nr'), ' · a partir del 10% AliExpress resta 12 puntos y congela la cuenta 7 días' if (pv((ae.get('nr') or {}).get('v')) or 0) >= 10 else '')])]
    acts = []
    for p in S['pen_lista_mv'] + S['pen_lista_ae']:
        if activa(p): acts.append(('p-urg', 'Urgente', f"{html.escape(p['tipo'])} en curso desde el {fd(p['desde'])} hasta el {fd(p['hasta'])} ({html.escape(p.get('estado') or '-')})" + (f" — {html.escape(TRAD.get(p['motivo'], p['motivo']))}" if p.get('motivo') else '')))
    nr = pv((ae.get('nr') or {}).get('v'))
    if nr is not None and nr >= 10: acts.append(('p-urg', 'Urgente', f"Pedidos no recibidos en AliExpress {ae['nr']['v']}: por encima del 10% (en enero de 2026 supuso 12 puntos y 7 días de congelación)"))
    for lab, m in (('Envíos no verificados AE', ae.get('no_verificados')), ('Entrega a tiempo Miravia', mv.get('entrega_tiempo')), ('Entrega a tiempo AE', ae.get('entrega_tiempo')),
                   ('Valoraciones del vendedor', mv.get('valoraciones')), ('Chat de tienda', mv.get('chat'))):
        if m and okm(pv(m['v']), m['obj']) is False: acts.append(('p-hi', 'Alta', f"{lab} {m['v']} (objetivo {html.escape(m['obj'])})"))
    acc = ('\n  <div class="actions">\n    <div class="kpi-head" style="padding:11px 16px;border-bottom:1px solid var(--border);background:var(--surface-2);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted)">Puntos de atención</div>\n'
           + '\n'.join(f'    <div class="action"><span class="pri {c}">{p}</span><span class="action-txt">{t}</span></div>' for c, p, t in acts) + '\n  </div>') if acts else ''
    return '  ' + '\n  '.join(cards) + acc

# =====================================================================
# MONTAJE
# =====================================================================
out = src
# CSS
css = """
.status { display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }
.st { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:7px 12px; display:flex; gap:8px; align-items:baseline; }
.st-l { font-size:11px; color:var(--text-muted); text-transform:uppercase; letter-spacing:.06em; }
.st-v { font-family:'IBM Plex Mono',monospace; font-weight:700; font-size:14px; }
.st-v.ok { color:var(--success); } .st-v.crit { color:var(--critical); }
.blk-row { display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:16px; margin-bottom:16px; }
.blk, .chart-card { background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:14px 16px; min-width:0; }
.blk .mtr-grid { margin-bottom:0; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); }
.blk .mtr { background:var(--surface-2); border-color:transparent; }
.blk-head { display:flex; justify-content:space-between; align-items:baseline; gap:10px; flex-wrap:wrap; margin-bottom:10px; }
.blk-head h2 { font-size:14px; font-weight:700; margin:0; }
.blk-per { font-size:11px; color:var(--text-muted); font-family:'IBM Plex Mono',monospace; }
.blk-note { font-size:11px; color:var(--text-muted); margin-top:8px; line-height:1.45; }
.dl { font-weight:700; } .dl.up { color:var(--success); } .dl.dn { color:var(--critical); }
.chart-row { display:grid; grid-template-columns:1fr; gap:16px; margin-bottom:16px; }

.cierre { margin-bottom:16px; }
.mtabs { display:flex; flex-wrap:wrap; gap:4px; }
.mtab { font:inherit; font-size:12px; font-weight:600; padding:5px 11px; border-radius:6px; border:1px solid var(--border); background:var(--surface-2); color:var(--text-muted); cursor:pointer; }
.mtab:hover { color:var(--text-primary); }
.mtab.on { background:var(--accent); border-color:var(--accent); color:#fff; }
.mtab:focus-visible { outline:2px solid var(--accent); outline-offset:2px; }
.cierre .mtr-grid { grid-template-columns:repeat(auto-fill,minmax(190px,1fr)); }
.chart svg { width:100%; height:auto; display:block; }
.chart .gl { stroke:var(--border); stroke-width:1; }
.chart .ax { fill:var(--text-muted); font-size:11px; font-family:'IBM Plex Mono',monospace; }
.chart .ax2 { fill:var(--warning); }
.chart .bl { fill:var(--text-primary); font-size:11px; font-weight:600; font-family:'IBM Plex Mono',monospace; }
.chart .bl2 { fill:var(--warning); }
.chart .b1 { fill:var(--accent); } .chart .b2 { fill:#60A5FA; }
.chart .ln { fill:none; stroke:var(--warning); stroke-width:2.5; } .chart .dt { fill:var(--warning); }
.leg { font-size:11px; color:var(--text-muted); display:flex; align-items:center; gap:6px; }
.lg { display:inline-block; width:12px; height:10px; border-radius:2px; } .lg.b2 { background:#60A5FA; } .lg.ln { height:3px; background:var(--warning); margin-left:8px; }
.empty { padding:40px 10px; text-align:center; color:var(--text-muted); font-size:13px; background:var(--surface-2); border-radius:8px; }
.sep-title { font-size:11px; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:var(--text-muted); margin:28px 0 12px; padding-top:16px; border-top:1px solid var(--border); }
"""
out = out.replace('</style>', css + '</style>', 1)

# Header
hdr = re.search(r'<div class="header">.*?\n</div>\n', out, re.S)
mk7 = sum(MK[k]['d7'][0] / MK[k]['div'] for k in MK)
som7 = D['miravia']['somnia-mv']['d7'][0]
new_hdr = f"""<div class="header">
  <div class="header-top">
    <div>
      <div class="client-eyebrow">Roicos · Duérmete Online</div>
      <h1 class="report-title">Amazon · Miravia · Mirakl</h1>
      <div class="report-meta">Actualizado {ACT} · todas las ventas con IVA, tal cual los paneles · cada bloque indica sus fechas (Amazon y Mirakl incluyen hoy hasta la hora de la actualización)</div>
    </div>
    <div class="summary-pills">
      <span class="pill-group-label">Amazon</span>
      <div class="pill"><span class="pill-num c-blue">{eur(a7['ventas'])}</span><span class="pill-label">Ventas 7d</span></div>
      <div class="pill"><span class="pill-num c-amber">{eur(a7['ads_inv'])}</span><span class="pill-label">Ads 7d</span></div>
      <div class="pill-vsep"></div>
      <span class="pill-group-label">Miravia</span>
      <div class="pill"><span class="pill-num c-blue">{eur(som7)}</span><span class="pill-label">Somnia 7d</span></div>
      <div class="pill-vsep"></div>
      <span class="pill-group-label">Mirakl</span>
      <div class="pill"><span class="pill-num c-blue">{eur(mk7)}</span><span class="pill-label">Ventas 7d</span></div>
    </div>
  </div>
</div>
"""
out = out[:hdr.start()] + new_hdr + out[hdr.end():]

# Tabs
tabs = re.search(r'<div class="tabs-bar">.*?</div>\n</div>\n', out, re.S)
dots = {}
for k in ['cfe', 'cfr', 'adeo', 'cfib', 'conforama', 'worten', 'mdm', 'brico', 'amazon', 'duermete-mv', 'somnia-mv']:
    m = re.search(rf'id="tab-{k}"><span class="dot ([^"]+)"', out); dots[k] = m.group(1) if m else 'dot-g'
def tb(k, label, active=False):
    return f'    <button class="tab{" active" if active else ""}" onclick="switchTab(\'{k}\')" id="tab-{k}"><span class="dot {dots[k]}"></span>{label}</button>\n'
new_tabs = ('<div class="tabs-bar">\n  <div class="tabs">\n    <span class="tab-section-label">Amazon</span>\n' + tb('amazon', 'Amazon ES', True)
    + '    <span class="tab-sep"></span>\n    <span class="tab-section-label">Miravia</span>\n' + tb('duermete-mv', 'Duérmete Online') + tb('somnia-mv', 'Somnia Descanso')
    + '    <span class="tab-sep"></span>\n    <span class="tab-section-label">Mirakl</span>\n'
    + ''.join(tb(k, MK[k]['name']) for k in ['cfe', 'cfr', 'adeo', 'cfib', 'conforama', 'worten', 'mdm', 'brico'])
    + '  </div>\n</div>\n')
out = out[:tabs.start()] + new_tabs + out[tabs.end():]

# Paneles eliminados (resúmenes)
out = re.sub(r'<!-- MIRAVIA RESUMEN -->.*?(?=<!-- DUERMETE ONLINE \(MIRAVIA\) -->)', '', out, flags=re.S)
out = re.sub(r'<!-- OVERVIEW MIRAKL -->.*?(?=<!-- WORTEN PT -->)', '', out, flags=re.S)

def panel_span(pid):
    m = re.search(rf'<div class="panel[^"]*" id="panel-{pid}">', out)
    rest = out[m.end():]
    nxt = re.search(r'\n<!-- [A-Z]', rest)
    end = m.end() + (nxt.start() if nxt else rest.index('\n</div>\n\n<footer'))
    return m.start(), m.end(), end

DROP = ('Ventas 7 días', 'Facturación sept.', 'Publicidad sept.', 'Anuncios sept.', 'Revenue 30d', 'Revenue Miravia', 'Revenue AliExpress', 'Tráfico 30d', 'Pdte de envío', 'SKUs sin stock')
def keep_sep(grid):
    # en la cuadrícula original: quita lo que ya está arriba, deja facturación/publicidad sept. (resumen del mes anterior) y el resto
    items = re.findall(r'<div class="mtr[^"]*">.*?</div></div>', grid, re.S)
    keep = []
    for it in items:
        lab = re.search(r'mtr-label">([^<]*)', it).group(1)
        if lab in ('Facturación sept.', 'Publicidad sept.', 'Anuncios sept.', 'Ventas 7 días', 'Revenue 30d', 'Revenue 30d total', 'Revenue Miravia', 'Revenue AliExpress', 'Tráfico 30d', 'Pdte de envío', 'SKUs sin stock'): continue
        if lab in ('Media carrito', 'Saldo pendiente', 'Saldo a pagar', 'Saldo pagado', 'Incidencias en curso', 'Pedidos totales'): continue  # Mirakl: ya van en vivo en «Estado de la tienda»
        keep.append(it)
    return '<div class="mtr-grid">\n    ' + '\n    '.join(keep) + '\n  </div>'

# Amazon: reconstruir parte alta
s, ps, pe = panel_span('amazon')
body = out[ps:pe]
body = re.sub(r'\s*<div class="note"><strong>Amazon ES · 1 oct 2026</strong>.*?</div>\n', '\n', body, count=1, flags=re.S)
body = re.sub(r'\s*<div class="mtr-grid">.*?\n  </div>\n', '\n', body, count=1, flags=re.S)          # fichas duplicadas
body = re.sub(r'\s*<div class="counters">.*?\n  </div>\n', '\n', body, count=1, flags=re.S)        # contadores duplicados
body = re.sub(r'\s*<tr><td>Activos sin stock</td>.*?</tr>', '', body)
body = re.sub(r'\s*<tr><td>Agotados \(inactivos\)</td>.*?</tr>', '', body)
body = re.sub(r'\s*<tr><td>Incompletos</td>.*?</tr>', '', body)
body = re.sub(r'\s*<div class="kpi-card">\s*<div class="kpi-head">Ventas e inversión en publicidad · septiembre 2026</div>.*?</table>\s*</div>', '', body, count=1, flags=re.S)
body = re.sub(r'\s*<div class="action"><span class="pri p-med">Media</span><span class="action-txt">120 listings incompletos.*?</div>', '', body)
body = body.replace('<div class="kpi-head">Listings y Buy Box · 1 oct 2026</div>', '<div class="kpi-head">Listings y Buy Box · 1 oct 2026</div>', 1)
body = re.sub(r'(<div class="kpi-head">Listings y Buy Box · 1 oct 2026</div>\s*<table class="kpi-table">\s*<tr><td>Activos</td>.*?</tr>)',
              r'\1\n      <tr><td>Agotados que vendieron en septiembre</td><td class="k-crit">6</td><td>SellerFlex · detalle en la tabla de abajo</td></tr>', body, count=1, flags=re.S)
if ES.get('listings'):   # estado en vivo de Seller Central (tools/amazon_fetch.js): sustituye la foto fija del 1-oct
    LI, BB, SF, EC = ES['listings'], ES['bb'], ES['sellerflex'], ES.get('cuenta') or {}
    F = f"{fd(ES['fecha'])}" + (f" · {ES['hora']}" if ES.get('hora') else '')
    def tr(a, b, c='', cls=''): return f"<tr><td>{a}</td><td class=\"{cls}\">{b}</td><td>{c}</td></tr>"
    def kcard(t, rows): return f"<div class=\"kpi-card\">\n    <div class=\"kpi-head\">{t}</div>\n    <table class=\"kpi-table\">\n      " + '\n      '.join(rows) + "\n    </table>\n  </div>"
    inc = EC.get('incidencias') or {}
    rows = [tr('Estado de la cuenta', html.escape(EC.get('texto') or '-'), f"Nivel del estado de la cuenta {EC.get('nivel') or '-'} · cumplimiento de políticas: {(EC.get('cumplimiento') or '-').lower()}",
               'k-ok' if (EC.get('texto') or '').startswith('En buen') else 'k-warn'),
            tr('Ratio de pedidos defectuosos', EC.get('odr') or '-', f"Gestionado por Amazon · {EC.get('odr_det') or '-'} (60 días) · objetivo &lt; 1%", 'k-ok')]
    rows += [tr(html.escape(k), e(v), 'Ver detalle en Estado de la cuenta de Seller Central', 'k-crit' if k == 'Cumplimiento normativo' else 'k-warn') for k, v in inc.items() if v]
    if not any(inc.values()): rows.append(tr('Incidencias de políticas', '0', 'Sin incidencias abiertas', 'k-ok'))
    inact_otros = (LI['inactivos'] or 0) - (LI['agotados'] or 0)
    rows2 = [tr('Activos', e(LI['activos']), f"{e(LI['sellerflex'])} SellerFlex (gestionado por Amazon) + {e(LI['fbm'])} FBM", 'k-ok'),
             tr('Buy Box (oferta destacada)', f"{e(BB['con'])} de {e(BB['total'])}", 'Activos con oferta destacada ahora mismo' + (f" · {e(BB['sin'])} sin oferta destacada (detalle abajo)" if BB['sin'] else ''), 'k-ok' if not BB['sin'] else 'k-warn'),
             tr('Agotados', e(LI['agotados']), f"{e(SF['agotados'])} SellerFlex · {e(len(SF['agotados_con_ventas']))} SellerFlex con ventas en 30 días", 'k-crit' if SF['agotados_con_ventas'] else ''),
             tr('Inactivos por otros motivos', e(inact_otros), f"Suprimidos de la búsqueda: {e(LI['suprimidos'])}"),
             tr('Falta información', e(LI['falta_info']), 'Listings incompletos (borradores)')]
    cards = [kcard(f'Estado de la cuenta · {F}', rows), kcard(f'Listings y Buy Box · {F}', rows2)]
    if BB['sin_top']:
        cards.append(kcard(f"Activos sin oferta destacada (Buy Box) · los que más venden · {F}",
            [f"<tr><td class=\"sku\">{html.escape(x['sku'])}</td><td>{e(x['uds30'])} uds 30d</td><td>{html.escape(x['titulo'])} · {eur(x['precio'], 2)}</td></tr>" for x in BB['sin_top']]))
    ag = SF['agotados_con_ventas']
    cards.append(kcard(f"SellerFlex agotados que han vendido en 30 días · {F}",
        [f"<tr><td class=\"sku\">{html.escape(x['sku'])}</td><td>{e(x['uds30'])} {'ud' if x['uds30'] == 1 else 'uds'}</td><td>{eur(x['ventas30'], 2) + ' con IVA · ' if x['ventas30'] else ''}{html.escape(x['titulo'])}" + (f" · {e(x['entrante'])} entrantes" if x['entrante'] else '') + "</td></tr>" for x in ag]
        or [tr('Sin agotados con ventas', '0', 'Todos los SellerFlex que han vendido en 30 días tienen stock', 'k-ok')]))
    if SF.get('stock_bajo'):
        cards.append(kcard(f"SellerFlex activos con menos de 50 uds · {F}",
            [f"<tr><td class=\"sku\">{html.escape(x['sku'])}</td><td>{e(x['stock'])} uds</td><td>{e(x['uds30'])} vendidas en 30 días · {html.escape(x['titulo'])}</td></tr>" for x in SF['stock_bajo'][:20]]))
    acts = []
    if ag: acts.append(('p-hi', 'Alta', f"Reponer en SellerFlex los {len(ag)} SKU agotados que han vendido en los últimos 30 días ({e(sum(x['uds30'] for x in ag))} uds)"))
    if BB['sin']: acts.append(('p-hi', 'Alta', f"{e(BB['sin'])} activos sin oferta destacada (Buy Box) — el que más vende: {html.escape(BB['sin_top'][0]['titulo'])} ({e(BB['sin_top'][0]['uds30'])} uds en 30 días)"))
    if inc.get('Cumplimiento normativo'): acts.append(('p-med', 'Media', f"Cumplimiento normativo: {e(inc['Cumplimiento normativo'])} incidencias abiertas en Estado de la cuenta"))
    acc = ('\n  <div class="actions">\n    <div class="kpi-head" style="padding:11px 16px;border-bottom:1px solid var(--border);background:var(--surface-2);font-size:11px;font-weight:600;text-transform:uppercase;letter-spacing:0.08em;color:var(--text-muted)">Puntos de atención</div>\n'
           + '\n'.join(f'    <div class="action"><span class="pri {c}">{p}</span><span class="action-txt">{t}</span></div>' for c, p, t in acts) + '\n  </div>') if acts else ''
    i0 = body.find('<div class="kpi-card">\n    <div class="kpi-head">Estado de la cuenta · 1 oct 2026')
    i1 = body.rfind('</div>')   # cierre del panel
    if i0 >= 0: body = body[:i0] + '\n  '.join(cards) + acc + '\n' + body[i1:]
out = out[:ps] + '\n' + amz_top + body + out[pe:]

# Miravia y Mirakl: bloques arriba + cuadrícula reducida como resumen de septiembre
TOPS = {'somnia-mv': som_top, 'duermete-mv': do_top}
TOPS.update({k: mk_top(k) for k in MK})
for pid, top in TOPS.items():
    s_, ps, pe = panel_span(pid)
    body = out[ps:pe]
    if pid in MK and MK[pid].get('calidad'):   # banner fijo del 1-oct: lo sustituye el de mk_top / mk_estado en vivo
        body = re.sub(r'\s*<div class="banner b-susp">.*?\n  </div>\n', '\n', body, count=1, flags=re.S)
    g = re.search(r'<div class="mtr-grid">.*?\n\s*</div>\n', body, re.S)
    rest = body[g.end():]
    if pid in MK:  # contadores fijos del 1-oct: sustituidos por «Estado de la tienda» en vivo
        rest = re.sub(r'\s*<div class="counters">.*?\n  </div>\n', '\n', rest, count=1, flags=re.S)
    if pid in MK and MK[pid].get('calidad'):   # control de calidad en vivo (tools/mirakl_fetch.js)
        rest = mk_calidad(pid) + '\n' + rest[rest.rfind('</div>'):]
    if pid in D.get('miravia', {}) and D['miravia'][pid].get('salud'):   # estado de la tienda en vivo (tools/miravia_salud.js)
        rest = mv_salud(pid) + '\n' + rest[rest.rfind('</div>'):]
    grid = '' if (pid in MK and MK[pid].get('calidad')) else keep_sep(g.group(0))   # con datos en vivo, fuera las fichas fijas del 1-oct
    body = body[:g.start()].rstrip() + '\n' + top + '\n  ' + grid + '\n' + rest
    out = out[:ps] + body + out[pe:]

# Pie
out = re.sub(r'<footer>.*?</footer>', f'<footer>Duérmete Online · actualizado {ACT} · Roicos · Ventas con IVA, tal cual los paneles · Amazon ES: «Ventas de productos pedidos» del Panel de ventas de Seller Central y publicidad de la API de Amazon Ads; listings, Buy Box y estado de la cuenta a {fd(ES["fecha"])} · Mirakl: ingresos por ventas del panel con impuestos y portes incluidos (Carrefour, Maisons du Monde y Brico no desglosan impuestos; Worten en hora de Lisboa) · Miravia: importe pagado del canal Miravia con IVA; AliExpress solo 30 días · «-» = sin dato</footer>', out, flags=re.S)
out = out.replace('</script>', '''
function selMes(pid, m) {
  var c = document.getElementById('cierre-' + pid);
  c.querySelectorAll('.mc').forEach(function (x) { x.hidden = x.getAttribute('data-m') !== m; });
  c.querySelectorAll('.mtab').forEach(function (b) { b.classList.toggle('on', b.getAttribute('data-m') === m); });
}
</script>''', 1)
import shutil
assert 'panel-overview' not in out and 'panel-miravia"' not in out
open(P, 'w', encoding='utf-8').write(out)
print('ok', len(out))
