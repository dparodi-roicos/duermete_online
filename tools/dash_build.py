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
            ts = [tile('Ventas con IVA', eur(d['con'], 2) if d['con'] is not None else '-', d.get('det_con', ''), 'v-ok' if d['con'] else 'v-muted'),
                  tile('Ventas sin IVA', eur(d['sin'], 2) if d['sin'] is not None else '-', d.get('det_sin', ''), 'v-ok' if d['sin'] else 'v-muted'),
                  tile('Inversión en publicidad', eur(d['inv'], 2) if d['inv'] is not None else '-', d.get('det_inv', ''), 'v-warn' if d['inv'] else 'v-muted'),
                  tile('Ventas por publicidad', eur(d['vpub'], 2) if d['vpub'] is not None else '-',
                       ' · '.join(x for x in [ratio(d['inv'], d['vpub'], 'ACOS'), ratio(d['inv'], d['sin'], 'TACOS')] if x), '' if d['vpub'] else 'v-muted')]
        else:
            inv = None if d['inv_mv'] is None and d['inv_ae'] is None else (d['inv_mv'] or 0) + (d['inv_ae'] or 0)
            vp = None if d['vpub_mv'] is None and d['vpub_ae'] is None else (d['vpub_mv'] or 0) + (d['vpub_ae'] or 0)
            sub = lambda a, b, la, lb: ' · '.join(f'{l} {eur(v, 2)}' for l, v in ((la, a), (lb, b)) if v is not None)
            ts = [tile('Facturación total', eur(d['tot_con'], 2) if d['tot_con'] is not None else '-',
                       (f"Con IVA · sin IVA {eur(d['tot_sin'], 2)}" if d['tot_sin'] is not None else 'Miravia + AliExpress'), 'v-ok' if d['tot_con'] else 'v-muted'),
                  tile('Miravia', eur(d['mv_con'], 2) if d['mv_con'] is not None else '-',
                       'Con IVA' + (f" · sin IVA {eur(d['mv_sin'], 2)}" if d['mv_sin'] is not None else '') + (' · ' + d['det_mv'] if d.get('det_mv') else ''), 'v-ok' if d['mv_con'] else 'v-muted'),
                  tile('AliExpress', eur(d['ae_con'], 2) if d['ae_con'] is not None else '-',
                       ('Con IVA' + (f" · sin IVA {eur(d['ae_sin'], 2)}" if d['ae_sin'] is not None else '') + ' · ' if d['ae_con'] is not None else '') + d.get('det_ae', ''), 'v-ok' if d['ae_con'] else 'v-muted'),
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
amz_sin, LB = serie('amazon', 'sin'); amz_inv, _ = serie('amazon', 'inv'); amz_vp, _ = serie('amazon', 'vpub')
amz_top = (
    amz_status
    + "<div class='blk-row'>"
    + block('Últimos 7 días', P7, [
        tile('Ventas', eur(a7['ventas']), delta(a7['ventas'], A['p7']['ventas']) + f" · {e(a7['lineas'])} líneas · {e(a7['uds'])} uds", 'v-ok'),
        tile('Inversión Ads', eur(a7['ads_inv']), 'Sponsored Products', 'v-warn'),
        tile('Ventas por Ads', eur(a7['ads_ventas']), ' · '.join(x for x in [acos(a7['ads_inv'], a7['ads_ventas']), f"TACOS {e(a7['ads_inv'] / a7['ventas'] * 100, 1)}%" if a7['ventas'] else ''] if x))])
    + block(f'{MES_ACTUAL} hasta la fecha', PMTD, [
        tile('Ventas', eur(am['ventas']), f"{e(am['lineas'])} líneas · {e(am['uds'])} uds", 'v-ok'),
        tile('Inversión Ads', eur(am['ads_inv']), '', 'v-warn'),
        tile('Ventas por Ads', eur(am['ads_ventas']), acos(am['ads_inv'], am['ads_ventas']) + ' · aún sube: Amazon atribuye ventas hasta 14 días después del clic')])
    + "</div>"
    + "<div class='chart-row'>"
    + chart_card(titulo_evol('amazon'), bar_chart(amz_sin, LB),
                 'Sin IVA · MerchantSpring (septiembre: informe «Todos los pedidos» tras promociones) · sin ventas registradas de enero a marzo')
    + chart_card('Inversión en Ads y ventas por Ads', ads_chart(amz_inv, amz_vp, LB),
                 'API de Amazon Ads · sin datos de publicidad antes de abril', LEG_ADS)
    + "</div>" + cierre('amazon') + sub_sep('Estado de la cuenta')
)

# ---------------- MIRAKL ----------------
MK = {
 'cfe':  dict(name='Carrefour ES', div=1.21, ads='No gestionamos su publicidad', iva='Carrefour no desglosa impuestos: su panel va con IVA y aquí se muestra ÷1,21'),
 'cfr':  dict(name='Carrefour FR', div=1.20, ads='No gestionamos su publicidad', iva='Carrefour no desglosa impuestos: su panel va con IVA y aquí se muestra ÷1,20'),
 'adeo': dict(name='Leroy Merlin', div=1, ads='Lo gestiona Valiuz (externo) · sin informe de gasto'),
 'cfib': dict(name='Conforama ES', div=1, ads='El panel no tiene módulo de publicidad'),
 'conforama': dict(name='Conforama FR', div=1, ads='Sin campañas'),
 'worten': dict(name='Worten PT', div=1, ads='Mirakl Ads', lisboa=True, con_ads=True),
 'mdm':  dict(name='Maisons du Monde', div=1, ads='Sin campañas', iva='el panel no desglosa impuestos (misma cifra con y sin IVA)'),
 'brico': dict(name='Brico Dépôt', div=1, ads='El panel no tiene módulo de publicidad'),
}
for k in MK: MK[k].update(D['mirakl'][k])
def mk_top(key):
    d = MK[key]; dv = d['div']
    s7, o7 = d['d7']; sp, op = d['p7']; s30, o30 = d['d30']; sm, om = d['mtd']
    ped = lambda o: '' if o is None else f' · {e(o)} pedidos'
    ads7 = tile('Inversión Ads', '-', 'Mirakl Ads · pendiente de consultar el panel de publicidad', 'v-muted') if d.get('con_ads') else tile('Publicidad', '-', d['ads'], 'v-muted')
    tz = 'hora de Lisboa' if d.get('lisboa') else 'hora de Madrid'
    stale = f" · datos del {fd(d['fecha'])}" if d.get('fecha') and d['fecha'] != D['actualizado'] else ''
    blocks = ("<div class='blk-row'>"
        + block('Últimos 7 días', P7 + stale, [tile('Ventas', eur(s7 / dv), (delta(s7, sp) or 'sin ventas') + ped(o7), 'v-ok' if s7 else 'v-muted'), ads7])
        + block('Últimos 30 días', P30 + stale, [tile('Ventas', eur(s30 / dv), ped(o30).lstrip(' ·'), 'v-ok' if s30 else 'v-muted'),
                                         tile(f'{MES_ACTUAL} hasta la fecha', eur(sm / dv), PMTD + ped(om), '')])
        + "</div>")
    vals, lb = serie(key, 'sin', 'con')
    charts = "<div class='chart-row'>" + chart_card(titulo_evol(key), bar_chart(vals, lb),
        f"Ingresos por ventas del panel, portes incluidos, {tz} · " + (d['iva'] if 'iva' in d else 'sin impuestos') + ' · 7 días, 30 días y mes en curso: días cerrados, hoy no cuenta')
    inv, lb = serie(key, 'inv'); vp, _ = serie(key, 'vpub')
    if any(v for v in inv):
        charts += chart_card('Inversión en Ads y ventas por Ads', ads_chart(inv, vp, lb), 'Mirakl Ads · sin datos de publicidad antes de julio', LEG_ADS)
    else:
        charts += chart_card('Inversión en Ads y ventas por Ads', "<div class='empty'>Sin datos de publicidad</div>", d['ads'])
    charts += "</div>"
    return blocks + charts + cierre(key) + sub_sep('Estado de la tienda')

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
    if pid == 'somnia-mv': t7.append(tile('AliExpress Ads', '-', 'Pendiente de consultar el panel de AliExpress Ads', 'v-muted'))
    top = (banner + "<div class='blk-row'>"
        + block('Últimos 7 días', P7 + stale, t7)
        + block('Mes en curso y 30 días', f'{PMTD} · {P30}{stale}', [
            tile(f'{MES_ACTUAL} hasta la fecha · Miravia', eur(m['mtd'][0], 2), f"{PMTD} · {e(m['mtd'][1])} pedidos", ''),
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
      <div class="report-meta">Actualizado {ACT} · últimos 7 días = {P7} · mes en curso = {PMTD} · ventas sin IVA salvo Miravia (con IVA)</div>
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
out = out[:ps] + '\n' + amz_top + body + out[pe:]

# Miravia y Mirakl: bloques arriba + cuadrícula reducida como resumen de septiembre
TOPS = {'somnia-mv': som_top, 'duermete-mv': do_top}
TOPS.update({k: mk_top(k) for k in MK})
for pid, top in TOPS.items():
    s_, ps, pe = panel_span(pid)
    body = out[ps:pe]
    g = re.search(r'<div class="mtr-grid">.*?\n\s*</div>\n', body, re.S)
    body = body[:g.start()].rstrip() + '\n' + top + '\n  ' + keep_sep(g.group(0)) + '\n' + body[g.end():]
    out = out[:ps] + body + out[pe:]

# Pie
out = re.sub(r'<footer>.*?</footer>', f'<footer>Duérmete Online · actualizado {ACT} · Roicos · Amazon ES: ventas sin IVA de MerchantSpring y publicidad de la API de Amazon Ads; listings, Buy Box y estado de la cuenta a {fd(ES["fecha"])} · Mirakl: ingresos por ventas del panel (portes incluidos; sin impuestos salvo Carrefour, que va con IVA y se muestra ÷1,21 / ÷1,20; Worten en hora de Lisboa) · Miravia: canal Miravia con IVA; AliExpress solo 30 días · «-» = sin dato</footer>', out, flags=re.S)
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
