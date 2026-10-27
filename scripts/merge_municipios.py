"""Script para mesclar dados dos municípios da Paraíba.

Carrega:
1. pb_municipios_ibge.json (dados base: geocode, nome, microrregiao, mesorregiao)
2. pb_malha_municipios_minima.geojson (para calcular centróides de latitude e longitude)
3. API SIDRA do IBGE (ou fallback) para obter a população estimada oficial de todos os 223 municípios.

Gera:
data/raw/pb_municipios_ibge_merged.json
"""

import json
import gzip
import urllib.request
from pathlib import Path


def compute_centroid(coords):
    """Calcula centróide de um polígono de coordenadas [lon, lat]."""
    if not coords:
        return None, None
    lon_sum = sum(point[0] for point in coords)
    lat_sum = sum(point[1] for point in coords)
    n = len(coords)
    return lon_sum / n, lat_sum / n


def fetch_populacao_ibge():
    """Busca população de todos os 223 municípios da Paraíba no SIDRA IBGE."""
    url = "https://servicodados.ibge.gov.br/api/v3/agregados/6579/periodos/2021/variaveis/9324?localidades=N6[N3[25]]"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            content = gzip.decompress(raw) if raw[:2] == b"\x1f\x8b" else raw
            data = json.loads(content)
            series = data[0]["resultados"][0]["series"]
            pop_map = {}
            for item in series:
                cod = int(item["localidade"]["id"])
                val = item["serie"].get("2021")
                if val is not None and val != "-":
                    pop_map[cod] = int(val)
            print(f"Obtidas {len(pop_map)} populações da API IBGE SIDRA.")
            return pop_map
    except Exception as e:
        print(f"Aviso ao consultar IBGE SIDRA: {e}")
        return {}


def main():
    root = Path(__file__).resolve().parents[1]
    raw_dir = root / "data" / "raw"

    raw_json_path = raw_dir / "pb_municipios_ibge.json"
    geo_path = raw_dir / "pb_malha_municipios_minima.geojson"
    enriched_path = raw_dir / "pb_municipios_ibge_enriched.json"
    out_path = raw_dir / "pb_municipios_ibge_merged.json"

    with open(raw_json_path, "r", encoding="utf-8") as f:
        municipios = json.load(f)

    # 1. Coordenadas
    coord_map = {}
    if geo_path.exists():
        with open(geo_path, "r", encoding="utf-8") as f:
            geo = json.load(f)
        for feature in geo.get("features", []):
            cod = int(feature["properties"]["codarea"])
            geometry = feature["geometry"]
            if geometry["type"] == "Polygon":
                coords = geometry["coordinates"][0]
            elif geometry["type"] == "MultiPolygon":
                coords = geometry["coordinates"][0][0]
            else:
                coords = None
            if coords:
                lon, lat = compute_centroid(coords)
                coord_map[cod] = (lat, lon)
    elif enriched_path.exists():
        with open(enriched_path, "r", encoding="utf-8") as f:
            enriched = json.load(f)
        for m in enriched:
            coord_map[m["geocode"]] = (m.get("latitude"), m.get("longitude"))

    # 2. População
    pop_map = fetch_populacao_ibge()

    # 3. Mesclar dados
    merged = []
    for m in municipios:
        geocode = int(m["geocode"])
        lat, lon = coord_map.get(geocode, (None, None))
        populacao = pop_map.get(geocode) or m.get("populacao")

        merged.append({
            "geocode": geocode,
            "nome": m.get("nome"),
            "microrregiao": m.get("microrregiao"),
            "mesorregiao": m.get("mesorregiao"),
            "populacao": populacao,
            "latitude": lat,
            "longitude": lon,
        })

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    print(f"Arquivo gerado com sucesso em: {out_path}")
    print(f"Total de registros mesclados: {len(merged)}")
    print(f"Exemplo do primeiro registro: {merged[0]}")


if __name__ == "__main__":
    main()
