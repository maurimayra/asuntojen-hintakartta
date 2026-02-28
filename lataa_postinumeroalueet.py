#!/usr/bin/env python3
"""
Lataa postinumeroalueet Paitulin WFS-rajapinnasta ja yhdistää asuntohintadataan.
Lähde: CSC Paituli - TK Paavo 2025
"""

import json
import requests
from typing import Dict, Any

# Paitulin WFS-rajapinnan osoite
WFS_URL = "https://paituli.csc.fi/geoserver/paituli/wfs"

def lataa_postinumeroalueet_paitulista() -> Dict[str, Any]:
    """
    Lataa postinumeroalueet Paitulin WFS-rajapinnasta.
    
    Returns:
        GeoJSON FeatureCollection postinumeroalueista
    """
    print("Haetaan postinumeroalueita Paitulin rajapinnasta...")
    
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeNames': 'paituli:tike_paavo_2025',
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326'  # WGS84 koordinaatit (lat/lon)
    }
    
    try:
        response = requests.get(WFS_URL, params=params, timeout=60)
        response.raise_for_status()
        
        geojson_data = response.json()
        print(f"✓ Haettiin {len(geojson_data['features'])} postinumeroaluetta")
        
        return geojson_data
        
    except requests.exceptions.RequestException as e:
        print(f"✗ Virhe ladattaessa dataa: {e}")
        raise


def yhdista_asuntohintadata(geojson_data: Dict[str, Any], 
                           asuntohinta_tiedosto: str = 'asuntohinnat.json') -> Dict[str, Any]:
    """
    Yhdistää asuntohintadatan GeoJSON-featureihin.
    Säilyttää vain ne postinumeroalueet, joilla on hintatietoa.
    
    Args:
        geojson_data: GeoJSON FeatureCollection
        asuntohinta_tiedosto: Polku asuntohinta JSON-tiedostoon
        
    Returns:
        Suodatettu ja rikastettu GeoJSON FeatureCollection
    """
    print(f"\nLuetaan asuntohintadata tiedostosta {asuntohinta_tiedosto}...")
    
    with open(asuntohinta_tiedosto, 'r', encoding='utf-8') as f:
        asuntohinta_data = json.load(f)
    
    # Hae viimeisin vuosi
    latest_year = max(asuntohinta_data['data'].keys())
    hinnat = asuntohinta_data['data'][latest_year]
    
    print(f"✓ Käytetään vuoden {latest_year} asuntohintoja")
    print(f"  Hintatietoa {len(hinnat)} postinumeroalueelta")
    
    # Suodata ja rikasta featuret
    filtered_features = []
    matched_count = 0
    
    for feature in geojson_data['features']:
        postinumero = feature['properties'].get('postinumer', '')
        
        # Tarkista onko tälle postinumerolle asuntohintadataa
        if postinumero in hinnat:
            # Lisää hinta propertyihin
            feature['properties']['price'] = hinnat[postinumero]['avg_price']
            feature['properties']['name'] = hinnat[postinumero]['name']
            filtered_features.append(feature)
            matched_count += 1
    
    print(f"✓ Yhdistettiin {matched_count} aluetta asuntohintadataan")
    
    # Luo uusi FeatureCollection
    result = {
        'type': 'FeatureCollection',
        'features': filtered_features
    }
    
    return result


def laske_keskipisteet(geojson_data: Dict[str, Any]) -> Dict[str, Dict[str, float]]:
    """
    Laskee karkeasti keskipisteet postinumeroalueille bbox:n perusteella.
    
    Args:
        geojson_data: GeoJSON FeatureCollection
        
    Returns:
        Dictionary: {postinumero: {lat: x, lon: y}}
    """
    print("\nLasketaan keskipisteitä postinumeroalueille...")
    
    koordinaatit = {}
    
    for feature in geojson_data['features']:
        postinumero = feature['properties'].get('postinumer', '')
        
        if not postinumero:
            continue
            
        # Hae Paavo-datan EUREF-FIN koordinaatit (jos saatavilla)
        if 'euref_x' in feature['properties'] and 'euref_y' in feature['properties']:
            # Nämä ovat ETRS-TM35FIN (EPSG:3067) koordinaatteja
            # Käytetään suoraan, koska kartta käyttää samaa projektioita
            # HUOM: Leaflet tarvitsee WGS84, mutta koska käytämme geometrioita, 
            # nämä keskipisteet ovat vain viitteellisiä
            koordinaatit[postinumero] = {
                'x': feature['properties']['euref_x'],
                'y': feature['properties']['euref_y']
            }
        else:
            # Vaihtoehtoinen tapa: laske geometrian keskipiste
            # (yksinkertainen bbox-keskipiste)
            geom = feature.get('geometry')
            if geom and geom['type'] in ['Polygon', 'MultiPolygon']:
                # Tämä on yksinkertaistettu - oikeasti pitäisi laskea todellinen centroid
                # Nyt käytetään vain ensimmäisen koordinaatin likimääräistä keskikohtaa
                coords = geom['coordinates']
                if geom['type'] == 'Polygon':
                    all_coords = coords[0]
                else:  # MultiPolygon
                    all_coords = coords[0][0]
                
                # Laske bbox
                lons = [c[0] for c in all_coords]
                lats = [c[1] for c in all_coords]
                
                koordinaatit[postinumero] = {
                    'lon': sum(lons) / len(lons),
                    'lat': sum(lats) / len(lats)
                }
    
    print(f"✓ Laskettiin keskipisteet {len(koordinaatit)} alueelle")
    return koordinaatit


def main():
    """Pääohjelma"""
    print("=" * 60)
    print("Postinumeroalueiden lataus Paitulista")
    print("=" * 60)
    
    # 1. Lataa postinumeroalueet Paitulista
    geojson_data = lataa_postinumeroalueet_paitulista()
    
    # 2. Yhdistä asuntohintadata
    enriched_geojson = yhdista_asuntohintadata(geojson_data)
    
    # 3. Tallenna GeoJSON
    output_file = 'postinumerot_hinnat.geojson'
    print(f"\nTallennetaan tiedostoon {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(enriched_geojson, f, ensure_ascii=False)
    
    file_size_mb = len(json.dumps(enriched_geojson)) / (1024 * 1024)
    print(f"✓ GeoJSON tallennettu ({file_size_mb:.1f} MB)")
    
    # 4. Laske ja tallenna keskipisteet
    koordinaatit = laske_keskipisteet(enriched_geojson)
    
    # Muunna EUREF-FIN koordinaatit WGS84:ksi keskipisteille
    # (Yksinkertaistettu - oikeasti tarvittaisiin projektion muunnos)
    wgs84_coords = {}
    for pnro, coords in koordinaatit.items():
        if 'x' in coords and 'y' in coords:
            # Karkea muunnos ETRS-TM35FIN -> WGS84
            # Oikea muunnos vaatisi pyproj-kirjaston
            # Nyt käytetään suoraan geometrian koordinaatteja
            for feature in enriched_geojson['features']:
                if feature['properties']['postinumer'] == pnro:
                    geom = feature['geometry']
                    if geom['type'] == 'Polygon':
                        coords_list = geom['coordinates'][0]
                    else:  # MultiPolygon
                        coords_list = geom['coordinates'][0][0]
                    
                    lons = [c[0] for c in coords_list]
                    lats = [c[1] for c in coords_list]
                    
                    wgs84_coords[pnro] = {
                        'lat': sum(lats) / len(lats),
                        'lon': sum(lons) / len(lons)
                    }
                    break
        else:
            wgs84_coords[pnro] = coords
    
    coord_file = 'postinumerokoordinaatit.json'
    print(f"Tallennetaan koordinaatit tiedostoon {coord_file}...")
    
    with open(coord_file, 'w', encoding='utf-8') as f:
        json.dump(wgs84_coords, f, ensure_ascii=False, indent=2)
    
    print(f"✓ Koordinaatit tallennettu")
    
    # Yhteenveto
    print("\n" + "=" * 60)
    print("VALMIS!")
    print("=" * 60)
    print(f"Postinumeroalueita yhteensä: {len(enriched_geojson['features'])}")
    print(f"GeoJSON-tiedosto: {output_file}")
    print(f"Koordinaattitiedosto: {coord_file}")
    print("\nDatalähteet:")
    print("  - Geometria: Paituli / TK Paavo 2025")
    print("  - Asuntohinnat: Tilastokeskus")
    print("=" * 60)


if __name__ == '__main__':
    main()
