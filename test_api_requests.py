import requests
import json

BASE = "http://127.0.0.1:8000"

def get(path):
    r = requests.get(BASE + path)
    try:
        j = r.json()
    except Exception:
        j = r.text
    print(path, r.status_code, j)

# health
get("/")
# municipios
get("/api/municipios")
# series (example geocode)
get("/api/series/2507507")
# previsoes
get("/api/previsoes/2507507")
# alertas
get("/api/alertas")
# mapa geojson
r = requests.get(BASE + "/api/mapa/geojson")
print("/api/mapa/geojson", r.status_code)
if r.status_code == 200:
    try:
        data = r.json()
        print("geojson type", type(data), "keys", list(data.keys())[:5])
    except Exception as e:
        print("error parsing geojson", e)
