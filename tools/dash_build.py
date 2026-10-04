import re, html
import json
P = r'C:\Users\Daniela\Downloads\duermete_online\index.html'
import os; src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "base_1oct.html"), encoding="utf-8").read()   # versión del 1-oct
H = json.load(open(r'C:\Users\Daniela\Downloads\duermete_online\cierres.json', encoding='utf-8'))      # histórico de cierres de mes

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
# AMAZON
# =====================================================================
amz_sales = [0, 0, 0, 22866.09, 71361.20, 178069.94, 222311.02, 218230.62, 162360.81]
amz_spend = [None, None, None, 2021.54, 3876.70, 9521.66, 8798.57, 7385.75, 6284.15]
amz_adsal = [None, None, None, 9830.20, 26862.45, 91026.60, 119832.07, 97224.34, 70561.68]
A7, A7p, AM = 46045.02, 32943.57, 20115.64
amz_status = status([('Estado de la cuenta', '282 · En buen estado', 'ok'), ('Listings activos', '312', ''), ('Buy Box', '312 / 312', 'ok'),
                     ('Agotados con ventas sept.', '6', 'crit'), ('Inactivos otros', '2', '')])
amz_top = (
    amz_status
    + "<div class='blk-row'>"
    + block('Últimos 7 días', '27 sep – 3 oct', [
        tile('Ventas', eur(A7), delta(A7, A7p) + ' · 152 líneas · 158 uds', 'v-ok'),
        tile('Inversión Ads', eur(1366.98), 'Sponsored Products', 'v-warn'),
        tile('Ventas por Ads', eur(15197.95), 'ACOS 9,0% · TACOS 3,0%')])
    + block('Octubre hasta la fecha', '1 – 3 oct', [
        tile('Ventas', eur(AM), '57 líneas · 63 uds', 'v-ok'),
        tile('Inversión Ads', eur(534.22), '', 'v-warn'),
        tile('Ventas por Ads', eur(3949.97), 'ACOS 13,5% · aún sube: Amazon atribuye ventas hasta 14 días después del clic')])
    + "</div>"
    + "<div class='chart-row'>"
    + chart_card('Evolución de ventas · enero a septiembre 2026', bar_chart(amz_sales),
                 'Sin IVA · MerchantSpring · sin ventas registradas de enero a marzo. Septiembre: 162.361€ en MerchantSpring frente a 156.211€ del informe de pedidos tras promociones (resumen de abajo).')
    + chart_card('Inversión en Ads y ventas por Ads', ads_chart(amz_spend, amz_adsal),
                 'Epinium · sin datos de publicidad antes de abril. ACOS: abr 20,6% · may 14,4% · jun 10,5% · jul 7,3% · ago 7,6% · sep 8,9%.', LEG_ADS)
    + "</div>" + cierre('amazon') + sub_sep('Estado de la cuenta')
)

# =====================================================================
# MIRAKL
# =====================================================================
def mk_data(raw, div=1.0):
    return {k: (None if v is None else v / div) for k, v in raw.items()}
MK = {
 'cfe':  dict(name='Carrefour ES', div=1.21, m=[153959,169919,191077,209592,245220,280532,303385,305414,233724], d7=(53213,354), p7=(53935,354), d30=(229191,1538), mtd=(25196,165),
             ads='No gestionamos su publicidad', iva='Carrefour no desglosa impuestos: su panel va con IVA y aquí se muestra ÷1,21'),
 'cfr':  dict(name='Carrefour FR', div=1.20, m=[0,0,0,0,147,0,0,0,130], d7=(0,0), p7=(0,0), d30=(130,1), mtd=(0,0),
             ads='No gestionamos su publicidad', iva='Carrefour no desglosa impuestos: su panel va con IVA y aquí se muestra ÷1,20'),
 'adeo': dict(name='Leroy Merlin', div=1, m=[62992,35826,50705,50924,66006,73699,103400,166997,134020], d7=(35355,176), p7=(23669,138), d30=(127269,701), mtd=(10188,59),
             ads='Lo gestiona Valiuz (externo) · sin informe de gasto'),
 'cfib': dict(name='Conforama ES', div=1, m=[59456,42966,42912,35129,38840,35695,67666,91011,61634], d7=(12821,138), p7=(13134,140), d30=(57368,610), mtd=(4471,51),
             ads='El panel no tiene módulo de publicidad'),
 'conforama': dict(name='Conforama FR', div=1, m=[1489,1150,276,465,0,0,0,0,0], d7=(0,0), p7=(0,0), d30=(0,0), mtd=(0,0), ads='Sin campañas'),
 'worten': dict(name='Worten PT', div=1, m=[4593,4939,5979,7312,6196,20563,36511,66742,32971], d7=(7081,56), p7=(6516,58), d30=(32536,243), mtd=(2685,26),
             ads='Mirakl Ads', lisboa=True,
             spend=[None,None,None,None,None,None,1639.03,2200.50,957.47], adsal=[None,None,None,None,None,None,22783.28,35896.27,18822.52]),
 'mdm':  dict(name='Maisons du Monde', div=1, m=[3965,3971,5445,2580,8688,4244,10534,7390,0], d7=(0,0), p7=(0,0), d30=(0,0), mtd=(0,0), ads='Sin campañas',
             iva='el panel no desglosa impuestos (misma cifra con y sin IVA)'),
 'brico': dict(name='Brico Dépôt', div=1, m=[5059,1878,0,236,290,1229,889,0,0], d7=(0,None), p7=(0,None), d30=(0,None), mtd=(0,None), ads='El panel no tiene módulo de publicidad'),
}
def mk_top(key):
    d = MK[key]; dv = d['div']
    s7, o7 = d['d7']; sp, op = d['p7']; s30, o30 = d['d30']; sm, om = d['mtd']
    ped = lambda o: '' if o is None else f' · {e(o)} pedidos'
    has_ads = 'spend' in d
    ads7 = tile('Inversión Ads', '-', 'Mirakl Ads · pendiente de consultar el panel de publicidad', 'v-muted') if has_ads else tile('Publicidad', '-', d['ads'], 'v-muted')
    tz = 'hora de Lisboa' if d.get('lisboa') else 'hora de Madrid'
    blocks = ("<div class='blk-row'>"
        + block('Últimos 7 días', '27 sep – 3 oct', [tile('Ventas', eur(s7 / dv), (delta(s7, sp) or 'sin ventas') + ped(o7), 'v-ok' if s7 else 'v-muted'), ads7])
        + block('Últimos 30 días', '4 sep – 3 oct', [tile('Ventas', eur(s30 / dv), ped(o30).lstrip(' ·'), 'v-ok' if s30 else 'v-muted'),
                                                    tile('Octubre hasta la fecha', eur(sm / dv), '1–3 oct' + ped(om), '')])
        + "</div>")
    vals = [v / dv for v in d['m']]
    charts = "<div class='chart-row'>" + chart_card('Evolución de ventas · enero a septiembre 2026', bar_chart(vals),
        f"Ingresos por ventas del panel a 4-oct, portes incluidos, {tz} · " + (d['iva'] if 'iva' in d else 'sin impuestos') + ' · 7 días, 30 días y octubre: días cerrados, hoy no cuenta')
    if has_ads:
        charts += chart_card('Inversión en Ads y ventas por Ads', ads_chart(d['spend'], d['adsal']),
            'Mirakl Ads · julio y agosto del export de producto; septiembre del panel (1-oct) · sin datos de publicidad antes de julio', LEG_ADS)
    else:
        charts += chart_card('Inversión en Ads y ventas por Ads', "<div class='empty'>Sin datos de publicidad</div>", d['ads'])
    charts += "</div>"
    return blocks + charts + cierre(key) + sub_sep('Estado de la tienda')

# =====================================================================
# MIRAVIA
# =====================================================================
som_m = [9954.07, 5989.61, 2882.49, 3130.68, 5756.12, 16769.98, 27351.52, 48371.91, 27823.58]
som_top = (
    "<div class='blk-row'>"
    + block('Últimos 7 días', '27 sep – 3 oct', [
        tile('Ventas Miravia', eur(4129.35, 2), delta(4129.35, 4139.61) + ' · 41 pedidos', 'v-ok'),
        tile('Ventas AliExpress', '-', 'Sin desglose de 7 días en el panel', 'v-muted'),
        tile('Anuncios Miravia', eur(160.25, 2), 'Sponsored Discovery · ingresos 789,99€ · ROAS 4,93', 'v-warn'),
        tile('AliExpress Ads', '-', 'Pendiente de consultar el panel de AliExpress Ads', 'v-muted')])
    + block('Mes en curso y 30 días', '1–3 oct · 4 sep–3 oct', [
        tile('Octubre hasta la fecha · Miravia', eur(1680.61, 2), '1–3 oct · 22 pedidos', ''),
        tile('Revenue 30d Miravia', eur(25263.22, 2), '240 pedidos', 'v-ok'),
        tile('Revenue 30d AliExpress', eur(12742.78, 2), 'Inicio del Seller Center', 'v-ok'),
        tile('Tráfico 30d', e(10633), 'Visitantes únicos · canal Miravia', ''),
        tile('Pedidos pendientes', '59', 'Aviso del inicio del Seller Center (4-oct)', 'v-warn'),
        tile('SKUs sin stock', '32', 'Dato del 1-oct', 'v-warn')])
    + "</div><div class='chart-row'>"
    + chart_card('Evolución de ventas Miravia · enero a septiembre 2026', bar_chart(som_m),
                 'Canal Miravia · importe pagado con IVA (Business Advisor) · AliExpress: el panel solo publica los ingresos de los últimos 30 días, sin histórico mensual')
    + chart_card('Anuncios Miravia · inversión y ventas', ads_chart([None]*6 + [1052.66, 1202.61, 819.32], [None]*6 + [9584.68, 15693.38, 7911.52]),
                 'Sponsored Discovery · julio y agosto del informe de anuncios; septiembre del panel (1-oct) · sin datos antes de julio', LEG_ADS)
    + chart_card('AliExpress Ads · inversión y ventas', ads_chart([None]*6 + [1005.55, 775.09, 500.58], [None]*6 + [8498.32, 12393.68, 3594.64]),
                 'Panel de AliExpress Ads · septiembre hasta el 29 · sin datos antes de julio', LEG_ADS)
    + "</div>" + cierre('somnia-mv') + sub_sep('Estado de la tienda')
)
do_top = (
    "<div class='blk-row'>"
    + block('Últimos 7 días', 'pendiente', [
        tile('Ventas Miravia', '-', 'Pendiente', 'v-muted'), tile('Ventas AliExpress', '-', 'AliExpress restringe las ventas en España desde el 1-oct', 'v-muted')])
    + block('Últimos 30 días', 'a 1 oct', [
        tile('Revenue 30d Miravia', '8.753,25€', 'Con IVA', 'v-warn'),
        tile('Revenue 30d AliExpress', '4.857,67€', 'Con IVA', 'v-crit'),
        tile('Tráfico 30d', '5.103', 'Usuarios', 'v-warn'),
        tile('Pdte de envío', '2', '0 por embalar · 2 listos para enviar', 'v-ok'),
        tile('SKUs sin stock', '109', '10 productos con ventas en 7 días agotados', 'v-crit')])
    + "</div><div class='chart-row'>"
    + chart_card('Evolución de ventas · enero a septiembre 2026', "<div class='empty'>Pendiente de abrir la tienda en el Seller Center</div>",
                 'Datos de arriba a 1-oct · 7 días y evolución pendientes de actualizar')
    + "</div>" + cierre('duermete-mv') + sub_sep('Estado de la tienda')
)

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
new_hdr = f"""<div class="header">
  <div class="header-top">
    <div>
      <div class="client-eyebrow">Roicos · Duérmete Online</div>
      <h1 class="report-title">Amazon · Miravia · Mirakl</h1>
      <div class="report-meta">4 oct 2026 · últimos 7 días = 27 sep–3 oct · mes en curso = 1–3 oct · ventas sin IVA salvo Miravia (con IVA)</div>
    </div>
    <div class="summary-pills">
      <span class="pill-group-label">Amazon</span>
      <div class="pill"><span class="pill-num c-blue">{eur(A7)}</span><span class="pill-label">Ventas 7d</span></div>
      <div class="pill"><span class="pill-num c-amber">{eur(1366.98)}</span><span class="pill-label">Ads 7d</span></div>
      <div class="pill-vsep"></div>
      <span class="pill-group-label">Miravia</span>
      <div class="pill"><span class="pill-num c-blue">{eur(4129.35)}</span><span class="pill-label">Somnia 7d</span></div>
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
out = re.sub(r'<footer>.*?</footer>', '<footer>Duérmete Online · 4 oct 2026 · Roicos · Amazon ES: ventas sin IVA de MerchantSpring y publicidad de Epinium (API de Amazon Ads); resumen de septiembre del informe "Todos los pedidos"; listings, Buy Box y estado de la cuenta a 1-oct · Mirakl: ingresos por ventas del panel (portes incluidos; sin impuestos salvo Carrefour, que va con IVA y se muestra ÷1,21 / ÷1,20; Worten en hora de Lisboa) · Miravia: Somnia a 4-oct (canal Miravia con IVA; AliExpress solo 30 días), Duérmete Online a 1-oct · «-» = sin dato</footer>', out, flags=re.S)
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
