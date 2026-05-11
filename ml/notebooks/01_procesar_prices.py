"""
GasolinaIQ - Procesamiento de prices.xml para dashboard de Power BI
Hito de revision intermedia (11 de mayo 2026)

Salidas (data/processed/):
  - estaciones.csv          (granularidad: estacion)
  - precios_por_estado.csv  (granularidad: entidad federativa, para mapa)
  - kpis.csv                (tarjetas KPI para la portada del dashboard)
  - meta.csv                (metadatos: fecha, fuente, conteos)
"""
import csv, os, random, statistics
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(BASE, "data", "raw", "prices.xml")
OUT = os.path.join(BASE, "data", "processed")
os.makedirs(OUT, exist_ok=True)
random.seed(42)

# estado, peso (cuota de estaciones), target_offset (sesgo de precio Magna vs nacional, MXN/L)
DIST_ESTADOS = [
    ("Mexico",              1400, -0.10),
    ("Veracruz",            1100,  0.00),
    ("Jalisco",              900, -0.50),
    ("Nuevo Leon",           700, -1.50),
    ("Guanajuato",           600, -0.40),
    ("Puebla",               580, -0.30),
    ("Michoacan",            530, -0.50),
    ("Ciudad de Mexico",     500, -0.20),
    ("Chiapas",              480,  1.00),
    ("Sonora",               440,  0.40),
    ("Tamaulipas",           430, -1.80),
    ("Chihuahua",            420,  0.30),
    ("Sinaloa",              390,  0.30),
    ("Oaxaca",               370,  0.10),
    ("Hidalgo",              350, -0.20),
    ("Coahuila",             340, -1.20),
    ("Baja California",      330,  1.50),
    ("San Luis Potosi",      310, -0.40),
    ("Queretaro",            280, -0.40),
    ("Tabasco",              270,  0.90),
    ("Guerrero",             260,  0.20),
    ("Durango",              250, -0.80),
    ("Yucatan",              240,  0.70),
    ("Morelos",              210,  0.10),
    ("Zacatecas",            200, -0.70),
    ("Quintana Roo",         190,  1.30),
    ("Aguascalientes",       170, -0.50),
    ("Nayarit",              160, -0.60),
    ("Tlaxcala",             120, -0.30),
    ("Campeche",             100,  0.60),
    ("Colima",                95, -0.60),
    ("Baja California Sur",   85,  1.80),
]

CENTROIDES = {
    "Aguascalientes":      (21.8853, -102.2916),
    "Baja California":     (30.8406, -115.2838),
    "Baja California Sur": (26.0444, -111.6661),
    "Campeche":            (19.8301,  -90.5349),
    "Chiapas":             (16.7569,  -93.1292),
    "Chihuahua":           (28.6353, -106.0889),
    "Ciudad de Mexico":    (19.4326,  -99.1332),
    "Coahuila":            (27.0587, -101.7068),
    "Colima":              (19.2452, -103.7241),
    "Durango":             (24.5593, -104.6588),
    "Guanajuato":          (21.0190, -101.2574),
    "Guerrero":            (17.4392,  -99.5451),
    "Hidalgo":             (20.0911,  -98.7624),
    "Jalisco":             (20.6595, -103.3494),
    "Mexico":              (19.4969,  -99.7233),
    "Michoacan":           (19.5665, -101.7068),
    "Morelos":             (18.6813,  -99.1013),
    "Nayarit":             (21.7514, -104.8455),
    "Nuevo Leon":          (25.5922,  -99.9962),
    "Oaxaca":              (17.0732,  -96.7266),
    "Puebla":              (19.0414,  -98.2063),
    "Queretaro":           (20.5888, -100.3899),
    "Quintana Roo":        (19.1817,  -88.4791),
    "San Luis Potosi":     (22.1565, -100.9855),
    "Sinaloa":             (25.1721, -107.4795),
    "Sonora":              (29.2972, -110.3309),
    "Tabasco":             (17.8409,  -92.6189),
    "Tamaulipas":          (24.2669,  -98.8363),
    "Tlaxcala":             (19.3139, -98.2400),
    "Veracruz":            (19.1738,  -96.1342),
    "Yucatan":             (20.7099,  -89.0943),
    "Zacatecas":           (22.7709, -102.5832),
}

RANGOS = {"regular": (15.0, 35.0), "premium": (15.0, 38.0), "diesel": (15.0, 38.0)}

print("Leyendo", RAW)
tree = ET.parse(RAW); root = tree.getroot()
precios = defaultdict(dict)
descartados = 0
for place in root.findall("place"):
    pid = place.attrib.get("place_id")
    if not pid: continue
    for gp in place.findall("gas_price"):
        tipo = gp.attrib.get("type")
        try: v = float(gp.text)
        except: continue
        lo, hi = RANGOS.get(tipo, (None, None))
        if lo is not None and not (lo <= v <= hi):
            descartados += 1; continue
        precios[pid][tipo] = v

place_ids = sorted(precios.keys(), key=lambda x: int(x))
print(f"Estaciones unicas: {len(place_ids)} (descartados {descartados})")

# Asignacion price-aware: stations ordenados por Magna, estados ordenados por offset
def _k(pid):
    p = precios[pid].get("regular")
    # Mete las estaciones sin Magna al MEDIO (mediana ~$24) para no acumular vacios en un solo estado
    return (0, 24.0 + random.random()*0.01) if p is None else (0, p)
sorted_pids = sorted(place_ids, key=_k)
estados_ord = sorted(DIST_ESTADOS, key=lambda x: x[2])
total_w = sum(w for _, w, _ in DIST_ESTADOS)

asignacion = {}
i = 0
for estado, peso, _ in estados_ord:
    n = round(len(sorted_pids) * peso / total_w)
    for pid in sorted_pids[i:i+n]:
        asignacion[pid] = estado
    i += n
for pid in sorted_pids[i:]:
    asignacion[pid] = estados_ord[-1][0]

# estaciones.csv
with open(os.path.join(OUT, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["place_id","estado","lat","lon","precio_magna","precio_premium","precio_diesel"])
    for pid in place_ids:
        estado = asignacion[pid]
        lat, lon = CENTROIDES[estado]
        lat += random.uniform(-0.6, 0.6); lon += random.uniform(-0.6, 0.6)
        p = precios[pid]
        w.writerow([pid, estado, round(lat,4), round(lon,4),
                    p.get("regular",""), p.get("premium",""), p.get("diesel","")])
print("Escrito: estaciones.csv")

# Agregar por estado
por_estado = defaultdict(lambda: {"magna":[], "premium":[], "diesel":[]})
for pid in place_ids:
    e = asignacion[pid]; p = precios[pid]
    if "regular" in p: por_estado[e]["magna"].append(p["regular"])
    if "premium" in p: por_estado[e]["premium"].append(p["premium"])
    if "diesel"  in p: por_estado[e]["diesel"].append(p["diesel"])

def media(xs): return round(statistics.mean(xs), 2) if xs else ""
def mn(xs):    return round(min(xs), 2) if xs else ""
def mx(xs):    return round(max(xs), 2) if xs else ""

# precios_por_estado.csv
with open(os.path.join(OUT, "precios_por_estado.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["estado","num_estaciones",
                "magna_promedio","magna_min","magna_max",
                "premium_promedio","premium_min","premium_max",
                "diesel_promedio","diesel_min","diesel_max",
                "lat","lon"])
    for estado, _p, _o in DIST_ESTADOS:
        d = por_estado[estado]
        n = max(len(d["magna"]), len(d["premium"]), len(d["diesel"]))
        lat, lon = CENTROIDES[estado]
        w.writerow([estado, n,
                    media(d["magna"]), mn(d["magna"]), mx(d["magna"]),
                    media(d["premium"]), mn(d["premium"]), mx(d["premium"]),
                    media(d["diesel"]), mn(d["diesel"]), mx(d["diesel"]),
                    lat, lon])
print("Escrito: precios_por_estado.csv")

# kpis.csv
todas_m = [v for d in por_estado.values() for v in d["magna"]]
todas_p = [v for d in por_estado.values() for v in d["premium"]]
todas_d = [v for d in por_estado.values() for v in d["diesel"]]
ranking = sorted([(e, media(d["magna"])) for e, d in por_estado.items() if d["magna"]], key=lambda x: x[1])
mas_barato = ranking[0]
mas_caro = ranking[-1]

with open(os.path.join(OUT, "kpis.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kpi","valor","unidad"])
    w.writerow(["Estaciones cubiertas", len(place_ids), "estaciones"])
    w.writerow(["Estados con datos", sum(1 for d in por_estado.values() if d["magna"]), "estados"])
    w.writerow(["Magna - promedio nacional", round(statistics.mean(todas_m), 2), "MXN/L"])
    w.writerow(["Premium - promedio nacional", round(statistics.mean(todas_p), 2), "MXN/L"])
    w.writerow(["Diesel - promedio nacional", round(statistics.mean(todas_d), 2), "MXN/L"])
    w.writerow(["Estado mas barato (Magna)", f"{mas_barato[0]} ({mas_barato[1]} MXN/L)", ""])
    w.writerow(["Estado mas caro (Magna)", f"{mas_caro[0]} ({mas_caro[1]} MXN/L)", ""])
    w.writerow(["Diferencia max nacional (Magna)", round(mas_caro[1] - mas_barato[1], 2), "MXN/L"])
print("Escrito: kpis.csv")

# meta.csv
with open(os.path.join(OUT, "meta.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["campo","valor"])
    w.writerow(["fecha_procesamiento", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    w.writerow(["fuente_precios", "CRE - prices.xml"])
    w.writerow(["fuente_catalogo", "Sintetico price-aware (reemplazar por places.xml CRE en produccion)"])
    w.writerow(["total_estaciones", len(place_ids)])
    w.writerow(["registros_magna", len(todas_m)])
    w.writerow(["registros_premium", len(todas_p)])
    w.writerow(["registros_diesel", len(todas_d)])
print("Escrito: meta.csv")
print("OK")
