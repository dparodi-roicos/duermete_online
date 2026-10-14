"""Convierte la salida de tools/amazon_fetch.js en el parche de amazon.estado para diario.json.
Uso: python -X utf8 tools/amazon_estado.py <salida_amazon.json> <fecha YYYY-MM-DD>   → escribe tools/_parche_amz.json
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
o = json.load(open(sys.argv[1], encoding='utf-8')); fecha = sys.argv[2]
if 'skip' in o: sys.exit(f"Cuenta equivocada en Seller Central: {o['skip']}")
L, B, S, E = o['listings'], o['buybox'], o['sellerflex'], o['estado']
estado = {
    'fecha': fecha, 'hora': o.get('hora'),
    # campos de la barra de estado de arriba
    'nivel': E.get('nivel') or '-', 'texto': E.get('texto') or '-', 'listings_activos': L['activos'],
    'buybox': f"{B['con']} / {B['total']}", 'agotados_con_ventas': len(S['agotados_con_ventas']),
    'inactivos_otros': (L['inactivos'] or 0) - (L['agotados'] or 0) + (L['suprimidos'] or 0),
    # detalle (tarjetas de Estado de la cuenta, Listings y Buy Box, SellerFlex)
    'cuenta': E, 'listings': L, 'bb': B, 'sellerflex': S,
}
out = os.path.join(ROOT, 'tools', '_parche_amz.json')
json.dump({'amazon': {'estado': estado}}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', out, estado['nivel'], estado['texto'], estado['buybox'], 'agotados SF con ventas:', estado['agotados_con_ventas'])
