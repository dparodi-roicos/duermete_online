# Genera el histórico de cierres de mes (cierres.json en el repo del dashboard).
# Cada vez que cierra un mes se añade su entrada aquí (o directamente en el JSON) y se vuelve a generar el dashboard.
import json
OUT = r'C:\Users\Daniela\Downloads\duermete_online\cierres.json'
MM = [f'2026-{m:02d}' for m in range(1, 10)]
H = {}

# ---------------- Amazon ES ----------------
amz = {}
ms_con = [0, 0, 0, 27460.06, 85702.46, 213560.27, 264923.70, 260662.31]
ms_sin = [0, 0, 0, 22866.09, 71361.20, 178069.94, 222311.02, 218230.62]
uds = [0, 0, 0, 94, 275, 684, 872, 823]
inv = [None, None, None, 2021.54, 3876.70, 9521.66, 8798.57, 7385.75]
vpub = [None, None, None, 9830.20, 26862.45, 91026.60, 119832.07, 97224.34]
for i, m in enumerate(MM[:8]):
    amz[m] = dict(con=ms_con[i], sin=ms_sin[i], det_con='MerchantSpring · promociones y cupones no desglosados',
                  det_sin=(f'{uds[i]} uds' if uds[i] else 'Sin ventas registradas'), inv=inv[i], vpub=vpub[i],
                  det_inv='Epinium (API de Amazon Ads)' if inv[i] else 'Sin datos de publicidad')
amz['2026-09'] = dict(con=189015.18, sin=156211.04,
                      det_con='Tras promociones · antes de promociones 199.276,62€ · promociones y cupones −10.261,44€ · informe «Todos los pedidos»',
                      det_sin='600 pedidos · 616 uds · sin cancelados', inv=6284.15, vpub=70561.68,
                      det_inv='Epinium · 28 campañas Sponsored Products · comisión 4%: 251,37€')
H['amazon'] = dict(tipo='mk', meses=amz)

# ---------------- Mirakl ----------------
def mirakl(con, sin, ped, inv=None, vpub=None, det_con='', det_inv='', note_sin=''):
    d = {}
    for i, m in enumerate(MM):
        d[m] = dict(con=con[i] if con else None, sin=sin[i] if sin else None,
                    det_con=det_con, det_sin=(f'{ped[i]} pedidos' if ped else '') + note_sin,
                    inv=inv[i] if inv else None, vpub=vpub[i] if vpub else None, det_inv=det_inv)
    return dict(tipo='mk', meses=d)
cfe = [153959, 169919, 191077, 209592, 245220, 280532, 303385, 305414, 233724]
H['cfe'] = mirakl(cfe, [round(v / 1.21, 2) for v in cfe], [1171, 1287, 1410, 1507, 1687, 1883, 2013, 2149, 1578],
                  det_con='Panel de Carrefour (no desglosa impuestos)', det_inv='No gestionamos su publicidad', note_sin=' · ÷1,21')
cfr = [0, 0, 0, 0, 147, 0, 0, 0, 130]
H['cfr'] = mirakl(cfr, [round(v / 1.20, 2) for v in cfr], [0, 0, 0, 0, 1, 0, 0, 3, 1],
                  det_con='Panel de Carrefour (no desglosa impuestos)', det_inv='No gestionamos su publicidad', note_sin=' · ÷1,20')
H['adeo'] = mirakl([76192, 43335, 61327, 61603, 79844, 89146, 125078, 202047, 162160],
                   [62992, 35826, 50705, 50924, 66006, 73699, 103400, 166997, 134020], [353, 215, 327, 314, 425, 519, 754, 962, 737],
                   det_con='Panel de Leroy Merlin', det_inv='Lo gestiona Valiuz (externo) · sin informe de gasto')
H['cfib'] = mirakl([71946, 51988, 51926, 42507, 46999, 43175, 80963, 101544, 72030],
                   [59456, 42966, 42912, 35129, 38840, 35695, 67666, 91011, 61634], [606, 447, 392, 363, 436, 376, 703, 886, 630],
                   det_con='Panel de Conforama Iberia (ES + PT)', det_inv='El panel no tiene módulo de publicidad')
H['conforama'] = mirakl([1787, 1380, 331, 558, 0, 0, 0, 0, 0], [1489, 1150, 276, 465, 0, 0, 0, 0, 0], [3, 3, 1, 1, 0, 1, 0, 0, 0],
                        det_con='Panel de Conforama FR', det_inv='Sin campañas')
H['worten'] = mirakl([5648, 6069, 7342, 8979, 7619, 25274, 44897, 82093, 40555],
                     [4593, 4939, 5979, 7312, 6196, 20563, 36511, 66742, 32971], [46, 28, 46, 58, 52, 190, 306, 524, 249],
                     inv=[None] * 6 + [1639.03, 2200.50, 957.47], vpub=[None] * 6 + [22783.28, 35896.27, 18822.52],
                     det_con='Panel de Worten (IVA PT 23%)', det_inv='Mirakl Ads')
for m in MM[:6]: H['worten']['meses'][m]['det_inv'] = 'Sin datos de publicidad'
H['worten']['meses']['2026-09']['det_inv'] = 'Mirakl Ads · +48,77€ de campañas opt-out aparte'
mdm = [3965, 3971, 5445, 2580, 8688, 4244, 10534, 7390, 0]
H['mdm'] = mirakl(mdm, None, [20, 16, 23, 13, 29, 27, 43, 28, 0],
                  det_con='Panel de Maisons du Monde (no desglosa impuestos)', det_inv='Sin campañas', note_sin='')
H['brico'] = mirakl(None, [5059, 1878, 0, 236, 290, 1229, 889, 0, 0], None,
                    det_con='No consultado: el panel no respondía', det_inv='El panel no tiene módulo de publicidad')

# ---------------- Miravia ----------------
def mv(meses): return dict(tipo='mv', meses=meses)
ba = [9954.07, 5989.61, 2882.49, 3130.68, 5756.12, 16769.98, 27351.52, 48371.91]
ba_ped = [95, 48, 29, 29, 52, 179, 258, 474]
som = {}
for i, m in enumerate(MM[:8]):
    som[m] = dict(mv_con=ba[i], mv_sin=None, det_mv=f'Importe pagado (Business Advisor) · {ba_ped[i]} pedidos',
                  ae_con=None, ae_sin=None, det_ae='Sin histórico mensual en el panel', tot_con=None, tot_sin=None,
                  inv_mv=None, inv_ae=None, vpub_mv=None, vpub_ae=None)
som['2026-07'].update(inv_mv=1052.66, inv_ae=1005.55, vpub_mv=9584.68, vpub_ae=8498.32)
som['2026-08'].update(inv_mv=1202.61, inv_ae=775.09, vpub_mv=15693.38, vpub_ae=12393.68)
som['2026-09'] = dict(mv_con=25066.53, mv_sin=20716.14, det_mv='250 pedidos creados del 1 al 30, sin cancelados',
                      ae_con=12938.60, ae_sin=10689.61, det_ae='111 pedidos (3 a Portugal, IVA 23%)',
                      tot_con=38005.13, tot_sin=31405.75, inv_mv=819.32, inv_ae=500.58, vpub_mv=7911.52, vpub_ae=3594.64,
                      det_inv='AliExpress Ads hasta el 29 (el 28 y el 29 sin gasto)')
H['somnia-mv'] = mv(som)
do = {m: dict(mv_con=None, mv_sin=None, det_mv='Pendiente de abrir la tienda', ae_con=None, ae_sin=None, det_ae='Pendiente',
              tot_con=None, tot_sin=None, inv_mv=None, inv_ae=None, vpub_mv=None, vpub_ae=None) for m in MM[:8]}
do['2026-09'] = dict(mv_con=7641.33, mv_sin=6315.15, det_mv='72 pedidos', ae_con=4374.17, ae_sin=3615.02, det_ae='48 pedidos',
                     tot_con=12015.50, tot_sin=9930.17, inv_mv=0, inv_ae=None, vpub_mv=0, vpub_ae=None,
                     det_inv='Sponsored Discovery sin gasto · sin módulo de AliExpress Ads')
H['duermete-mv'] = mv(do)

json.dump(H, open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('ok', {k: len(v['meses']) for k, v in H.items()})
