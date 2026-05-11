"""
GasolinaIQ - Genera tendencia temporal sintetica + GeoJSON simple
"""
import csv, json, os, random, math
from datetime import date, timedelta

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(BASE, "data", "processed")
RAW = os.path.join(BASE, "data", "raw")
random.seed(7)

# 1) Tendencia temporal: 12 semanas, basada en precios_por_estado.csv
estado_prices = {}
with open(os.path.join(OUT, "precios_por_estado.csv"), encoding="utf-8") as f:
    r = csv.DictReader(f)
    for row in r:
        try:
            magna = float(row["magna_promedio"])
            prem = float(row["premium_promedio"])
            dies = float(row["diesel_promedio"])
            estado_prices[row["estado"]] = (magna, prem, dies)
        except:
            continue

# 12 semanas hacia atras desde hoy
hoy = date(2026, 5, 11)
semanas = [hoy - timedelta(days=7*i) for i in range(11, -1, -1)]

# tendencia base: +0.012/semana (sube ~1.5% trimestre) con ruido por estado
with open(os.path.join(OUT, "tendencia_semanal.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["semana","estado","magna","premium","diesel"])
    for estado, (m, p, d) in estado_prices.items():
        # Trayectoria: cada semana sube 0.005-0.015 con ruido
        for idx, semana in enumerate(semanas):
            t = idx - 11   # -11 ... 0 (semana actual = 0)
            drift = -0.008 * t   # hace 11 semanas estaba ~9 centavos abajo
            noise_m = random.uniform(-0.08, 0.08)
            noise_p = random.uniform(-0.10, 0.10)
            noise_d = random.uniform(-0.06, 0.06)
            w.writerow([
                semana.isoformat(), estado,
                round(m + drift + noise_m, 2),
                round(p + drift*1.1 + noise_p, 2),
                round(d + drift*0.8 + noise_d, 2),
            ])
print("Escrito: tendencia_semanal.csv")

# Tendencia nacional (un solo numero por semana, util para grafica grande)
with open(os.path.join(OUT, "tendencia_nacional.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["semana","magna_nacional","premium_nacional","diesel_nacional"])
    avg_m = sum(p[0] for p in estado_prices.values()) / len(estado_prices)
    avg_p = sum(p[1] for p in estado_prices.values()) / len(estado_prices)
    avg_d = sum(p[2] for p in estado_prices.values()) / len(estado_prices)
    for idx, semana in enumerate(semanas):
        t = idx - 11
        drift = -0.008 * t
        w.writerow([
            semana.isoformat(),
            round(avg_m + drift + random.uniform(-0.03, 0.03), 2),
            round(avg_p + drift*1.1 + random.uniform(-0.04, 0.04), 2),
            round(avg_d + drift*0.8 + random.uniform(-0.03, 0.03), 2),
        ])
print("Escrito: tendencia_nacional.csv")

# 2) GeoJSON simple: poligonos con bounding box aproximada por estado
# Para mapa decente en Power BI con visual "Mapa coropletico" o "Shape Map".
# El bounding box es burdo; documentamos en README como reemplazar por el oficial.
BBOX = {
    # estado: (lat_min, lat_max, lon_min, lon_max)
    "Aguascalientes":      (21.6,  22.45, -102.86, -101.84),
    "Baja California":     (28.0,  32.71, -117.13, -112.78),
    "Baja California Sur": (22.87, 28.0,  -115.20, -109.41),
    "Campeche":            (17.8,  20.85,  -92.46,  -89.10),
    "Chiapas":             (14.53, 17.99,  -94.14,  -90.38),
    "Chihuahua":           (25.55, 31.78, -109.07, -103.30),
    "Ciudad de Mexico":    (19.05, 19.59,  -99.36,  -98.94),
    "Coahuila":            (24.55, 29.88, -103.97, -99.84),
    "Colima":              (18.66, 19.52, -104.69, -103.49),
    "Durango":             (22.34, 26.85, -107.18, -102.46),
    "Guanajuato":          (19.93, 21.85, -102.10, -99.69),
    "Guerrero":            (16.30, 18.91, -102.18,  -98.00),
    "Hidalgo":             (19.62, 21.40,  -99.88,  -97.97),
    "Jalisco":             (18.92, 22.75, -105.69, -101.51),
    "Mexico":              (18.36, 20.28, -100.59,  -98.61),
    "Michoacan":           (17.91, 20.41, -103.74, -100.07),
    "Morelos":             (18.33, 19.13,  -99.51,  -98.62),
    "Nayarit":             (20.62, 23.78, -105.78, -103.71),
    "Nuevo Leon":          (23.18, 27.81, -101.20, -98.43),
    "Oaxaca":              (15.66, 18.65,  -98.55,  -93.86),
    "Puebla":              (17.88, 20.84,  -99.07,  -96.71),
    "Queretaro":           (20.01, 21.66, -100.61,  -99.04),
    "Quintana Roo":        (17.88, 21.61,  -89.32,  -86.71),
    "San Luis Potosi":     (21.16, 24.50, -102.30, -98.33),
    "Sinaloa":             (22.46, 27.04, -109.45, -105.39),
    "Sonora":              (26.27, 32.49, -115.07, -108.41),
    "Tabasco":             (17.27, 18.66,  -94.13,  -91.02),
    "Tamaulipas":          (22.21, 27.68,  -100.13, -97.13),
    "Tlaxcala":            (19.06, 19.73,  -98.71,  -97.62),
    "Veracruz":            (17.15, 22.46,  -98.65,  -93.62),
    "Yucatan":             (19.55, 21.62,  -90.42,  -87.53),
    "Zacatecas":           (21.04, 25.13, -104.36,  -100.81),
}

features = []
for estado, (la0, la1, lo0, lo1) in BBOX.items():
    poly = [[
        [lo0, la0], [lo1, la0], [lo1, la1], [lo0, la1], [lo0, la0]
    ]]
    features.append({
        "type": "Feature",
        "properties": {"name": estado, "ESTADO": estado},
        "geometry": {"type": "Polygon", "coordinates": poly},
    })

geojson = {"type": "FeatureCollection", "features": features}
gjpath = os.path.join(RAW, "mexico_estados_simple.geojson")
with open(gjpath, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)
print("Escrito:", gjpath)
print("OK")
