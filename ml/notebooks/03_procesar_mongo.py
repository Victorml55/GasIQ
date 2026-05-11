"""
GasolinaIQ - Procesar export JSON de MongoDB (gasolinaiq.precios)
Reemplaza la asignacion sintetica de estado por una derivada de las
coordenadas reales (nearest-centroid).

Entrada:  data/raw/precios_mongo.json  (export full collection desde Compass)
Salidas:  data/processed/estaciones.csv         (REGENERADO con datos reales)
          data/processed/precios_por_estado.csv (REGENERADO)
          data/processed/kpis.csv               (REGENERADO)
          data/processed/meta.csv               (actualizado: fuente_catalogo=Mongo real)
"""
import csv, json, os, statistics, math
from collections import defaultdict
from datetime import datetime

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
RAW = os.path.join(BASE, "data", "raw", "precios_mongo.json")
OUT = os.path.join(BASE, "data", "processed")
os.makedirs(OUT, exist_ok=True)

# Centroides aproximados de cada estado (mismos del script 01)
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
    "Tlaxcala":            (19.3139,  -98.2400),
    "Veracruz":            (19.1738,  -96.1342),
    "Yucatan":             (20.7099,  -89.0943),
    "Zacatecas":           (22.7709, -102.5832),
}

def nearest_estado(lat, lon):
    """Devuelve el estado cuyo centroide esta mas cerca (Euclidiano simple)."""
    best, best_d = None, float("inf")
    for estado, (la, lo) in CENTROIDES.items():
        d = (lat - la) ** 2 + (lon - lo) ** 2
        if d < best_d:
            best_d, best = d, estado
    return best

def to_float(x):
    """Acepta numero o string. Devuelve None si no se puede."""
    if x is None: return None
    if isinstance(x, (int, float)): return float(x)
    if isinstance(x, dict):
        # Manejar formato extendido: {"$numberDouble": "22.95"} o {"$numberInt": ...}
        for k in ("$numberDouble", "$numberInt", "$numberLong", "$numberDecimal"):
            if k in x: return float(x[k])
        return None
    try: return float(x)
    except: return None

# ----------------------------- Lectura JSON -----------------------------

print(f"Leyendo {RAW} ...")
if not os.path.exists(RAW):
    raise SystemExit(f"FALTA: {RAW}. Exporta primero la coleccion desde Compass.")

# El export de Compass puede ser un JSON array O un NDJSON (uno por linea).
docs = []
with open(RAW, encoding="utf-8") as f:
    txt = f.read().strip()
if txt.startswith("["):
    docs = json.loads(txt)
else:
    for line in txt.split("\n"):
        line = line.strip()
        if line:
            docs.append(json.loads(line))

print(f"Documentos leidos: {len(docs)}")

# ----------------------------- Normalizacion -----------------------------

estaciones = []  # [(place_id, estado, lat, lon, magna, premium, diesel, nombre, cre_id)]
descartados_geo = 0

for d in docs:
    place_id = d.get("place_id")
    if place_id is None: continue
    place_id = str(place_id)
    lat = to_float(d.get("latitud"))
    lon = to_float(d.get("longitud"))
    if lat is None or lon is None:
        descartados_geo += 1; continue
    # Mexico esta aprox entre lat 14-33 y lon -118 a -86. Filtra coords absurdas.
    if not (14 <= lat <= 33 and -120 <= lon <= -86):
        descartados_geo += 1; continue
    estado = nearest_estado(lat, lon)
    magna = to_float(d.get("precio_regular"))
    prem  = to_float(d.get("precio_premium"))
    dies  = to_float(d.get("precio_diesel"))
    nombre = d.get("nombre", "") or ""
    cre = d.get("cre_id", "") or ""
    estaciones.append((place_id, estado, lat, lon, magna, prem, dies, nombre, cre))

print(f"Estaciones validas: {len(estaciones)} (descartadas por coordenadas malas: {descartados_geo})")

# ----------------------------- estaciones.csv -----------------------------

with open(os.path.join(OUT, "estaciones.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["place_id","estado","lat","lon",
                "precio_magna","precio_premium","precio_diesel",
                "nombre","cre_id"])
    for pid, est, la, lo, m, p, d, nom, cre in estaciones:
        w.writerow([pid, est, round(la,5), round(lo,5),
                    m if m is not None else "",
                    p if p is not None else "",
                    d if d is not None else "",
                    nom, cre])
print("Escrito: estaciones.csv (datos REALES de Mongo)")

# ----------------------------- precios_por_estado.csv -----------------------------

por_estado = defaultdict(lambda: {"magna":[], "premium":[], "diesel":[]})
conteo_estado = defaultdict(int)
for pid, est, la, lo, m, p, d, nom, cre in estaciones:
    conteo_estado[est] += 1
    if m is not None and 15 <= m <= 35:    por_estado[est]["magna"].append(m)
    if p is not None and 15 <= p <= 38:    por_estado[est]["premium"].append(p)
    if d is not None and 15 <= d <= 38:    por_estado[est]["diesel"].append(d)

def media(xs): return round(statistics.mean(xs), 2) if xs else ""
def mn(xs):    return round(min(xs), 2) if xs else ""
def mx(xs):    return round(max(xs), 2) if xs else ""

with open(os.path.join(OUT, "precios_por_estado.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["estado","num_estaciones",
                "magna_promedio","magna_min","magna_max",
                "premium_promedio","premium_min","premium_max",
                "diesel_promedio","diesel_min","diesel_max",
                "lat","lon"])
    # Orden estable por nombre
    for estado in sorted(CENTROIDES.keys()):
        d = por_estado[estado]
        lat, lon = CENTROIDES[estado]
        w.writerow([estado, conteo_estado[estado],
                    media(d["magna"]), mn(d["magna"]), mx(d["magna"]),
                    media(d["premium"]), mn(d["premium"]), mx(d["premium"]),
                    media(d["diesel"]), mn(d["diesel"]), mx(d["diesel"]),
                    lat, lon])
print("Escrito: precios_por_estado.csv")

# ----------------------------- kpis.csv -----------------------------

todas_m = [v for d in por_estado.values() for v in d["magna"]]
todas_p = [v for d in por_estado.values() for v in d["premium"]]
todas_d = [v for d in por_estado.values() for v in d["diesel"]]
ranking = sorted([(e, media(d["magna"])) for e, d in por_estado.items() if d["magna"]], key=lambda x: x[1])
mas_barato = ranking[0] if ranking else ("N/A", 0)
mas_caro = ranking[-1] if ranking else ("N/A", 0)

with open(os.path.join(OUT, "kpis.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["kpi","valor","unidad"])
    w.writerow(["Estaciones cubiertas", len(estaciones), "estaciones"])
    w.writerow(["Estados con datos", sum(1 for d in por_estado.values() if d["magna"]), "estados"])
    w.writerow(["Magna - promedio nacional", round(statistics.mean(todas_m), 2) if todas_m else "", "MXN/L"])
    w.writerow(["Premium - promedio nacional", round(statistics.mean(todas_p), 2) if todas_p else "", "MXN/L"])
    w.writerow(["Diesel - promedio nacional", round(statistics.mean(todas_d), 2) if todas_d else "", "MXN/L"])
    w.writerow(["Estado mas barato (Magna)", f"{mas_barato[0]} ({mas_barato[1]} MXN/L)", ""])
    w.writerow(["Estado mas caro (Magna)", f"{mas_caro[0]} ({mas_caro[1]} MXN/L)", ""])
    w.writerow(["Diferencia max nacional (Magna)", round(mas_caro[1] - mas_barato[1], 2) if ranking else "", "MXN/L"])
print("Escrito: kpis.csv")

# ----------------------------- meta.csv -----------------------------

with open(os.path.join(OUT, "meta.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["campo","valor"])
    w.writerow(["fecha_procesamiento", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    w.writerow(["fuente_precios", "MongoDB Atlas - gasolinaiq.precios"])
    w.writerow(["fuente_catalogo", "REAL - lat/lon de Mongo + nearest-centroid"])
    w.writerow(["total_documentos_leidos", len(docs)])
    w.writerow(["estaciones_validas", len(estaciones)])
    w.writerow(["descartadas_por_coordenadas", descartados_geo])
    w.writerow(["registros_magna", len(todas_m)])
    w.writerow(["registros_premium", len(todas_p)])
    w.writerow(["registros_diesel", len(todas_d)])
print("Escrito: meta.csv")
print("OK - todos los CSV regenerados con datos REALES de tu cluster.")
