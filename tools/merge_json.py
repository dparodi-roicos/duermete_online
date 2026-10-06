"""Fusiona un parche JSON en diario.json o cierres.json (merge profundo: solo cambia las claves que trae el parche).
Uso: python tools/merge_json.py diario.json parche.json
     python tools/merge_json.py cierres.json parche_cierre.json
"""
import json, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def merge(a, b):
    for k, v in b.items():
        if isinstance(v, dict) and isinstance(a.get(k), dict): merge(a[k], v)
        else: a[k] = v
    return a

dest = os.path.join(ROOT, sys.argv[1]); patch = json.load(open(sys.argv[2], encoding='utf-8'))
data = json.load(open(dest, encoding='utf-8'))
json.dump(merge(data, patch), open(dest, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', sys.argv[1], list(patch.keys()))
