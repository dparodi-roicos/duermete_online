"""Convierte la salida de tools/miravia_salud.js en el parche de miravia.<clave>.salud para diario.json.
Uso: python -X utf8 tools/miravia_estado.py <salida.json> <HOY>   → escribe tools/_parche_mvs.json
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
o = json.load(open(sys.argv[1], encoding='utf-8'))
clave = {'Somnia Descanso': 'somnia-mv', 'Duérmete Online': 'duermete-mv'}.get(o.get('tienda'))
if not clave: sys.exit(f"Tienda no reconocida: {o.get('tienda')}")
o['fecha'] = sys.argv[2]
out = os.path.join(ROOT, 'tools', '_parche_mvs.json')
json.dump({'miravia': {clave: {'salud': o}}}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', clave, 'penalizaciones', o.get('pen_mv'), o.get('pen_ae'), 'NR AE', (o.get('ae') or {}).get('nr'))
