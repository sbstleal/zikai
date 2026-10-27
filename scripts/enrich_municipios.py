import json
import math

def compute_centroid(coords):
    """Compute centroid of a polygon (list of [lon, lat] points)."""
    if not coords:
        return None, None
    lon_sum = sum(point[0] for point in coords)
    lat_sum = sum(point[1] for point in coords)
    n = len(coords)
    return lon_sum / n, lat_sum / n

def main():
    # Load municipality data
    with open('data/raw/pb_municipios_ibge.json', 'r', encoding='utf-8') as f:
        municipios = json.load(f)

    # Load geojson with polygons
    with open('data/raw/pb_malha_municipios_minima.geojson', 'r', encoding='utf-8') as f:
        geo = json.load(f)

    # Build map from codarea to geometry coordinates
    geom_map = {}
    for feature in geo.get('features', []):
        cod = int(feature['properties']['codarea'])
        geometry = feature['geometry']
        if geometry['type'] == 'Polygon':
            coords = geometry['coordinates'][0]
            geom_map[cod] = coords
        elif geometry['type'] == 'MultiPolygon':
            coords = geometry['coordinates'][0][0]
            geom_map[cod] = coords

    enriched = []
    for m in municipios:
        cod = m['geocode']
        lat, lon = None, None
        if cod in geom_map:
            lon, lat = compute_centroid(geom_map[cod])
        enriched.append({**m, "latitude": lat, "longitude": lon})

    with open('data/raw/pb_municipios_ibge_enriched.json', 'w', encoding='utf-8') as f:
        json.dump(enriched, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
