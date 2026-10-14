"""Junta las salidas de tools/mirakl_fetch.js (una por marketplace, en tools/_mk/<clave>.json) en el parche de diario.json.
Uso: python -X utf8 tools/mirakl_parche.py <HOY>   → escribe tools/_parche_mk.json
Opcional: tools/_mk/worten_ads.json con {inv, ventas, pedidos, roas, acos} (Mirakl Ads, últimos 7 días) → mirakl.worten.ads_d7
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR = os.path.join(ROOT, 'tools', '_mk'); hoy = sys.argv[1]
HOST = {'carrefoures-prod.mirakl.net': 'cfe', 'carrefourfr.mirakl.net': 'cfr', 'adeo-marketplace.mirakl.net': 'adeo', 'conforamaiberia-prod.mirakl.net': 'cfib',
        'conforama-prod.mirakl.net': 'conforama', 'marketplace.worten.pt': 'worten', 'maisonsdumonde-prod.mirakl.net': 'mdm', 'marketplace.bricodepot.es': 'brico'}
patch, hechos = {}, []
for f in sorted(os.listdir(DIR)):
    if not f.endswith('.json') or f == 'worten_ads.json': continue
    o = json.load(open(os.path.join(DIR, f), encoding='utf-8'))
    if 'skip' in o: print('SALTADO', f, o['skip']); continue
    k = HOST.get(o.get('host'))
    if not k: print('host desconocido', f, o.get('host')); continue
    patch[k] = {x: o[x] for x in ('d7', 'p7', 'd30', 'mtd', 'rangos', 'estado', 'calidad') if x in o}
    patch[k]['fecha'] = hoy; hechos.append(k)
ads = os.path.join(DIR, 'worten_ads.json')
if os.path.exists(ads):
    a = json.load(open(ads, encoding='utf-8')); a['fecha'] = hoy
    patch.setdefault('worten', {})['ads_d7'] = a; hechos.append('worten_ads')
out = os.path.join(ROOT, 'tools', '_parche_mk.json')
json.dump({'mirakl': patch}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', out, hechos)
