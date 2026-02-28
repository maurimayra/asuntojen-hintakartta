#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lataa postinumeroalueet Tilastokeskuksen WFS-rajapinnasta ja yhdistää asuntohintadataan.
Lähde: Tilastokeskus geo.stat.fi - postialue:pno_tilasto
"""

import sys
import json
import requests
from typing import Dict, Any

# Aseta UTF-8 enkoodaus tulostuksille
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Tilastokeskuksen WFS-rajapinnan osoite (tarkemmat postinumeroalueet)
WFS_URL = "https://geo.stat.fi/geoserver/postialue/wfs"

def lataa_postinumeroalueet_paitulista() -> Dict[str, Any]:
    """
    Lataa postinumeroalueet Tilastokeskuksen WFS-rajapinnasta.
    
    Returns:
        GeoJSON FeatureCollection postinumeroalueista
    """
    print("Haetaan postinumeroalueita Tilastokeskuksen rajapinnasta...")
    print("  Pyydetään tarkkoja geometrioita (ei yksinkertaistusta)...")
    
    params = {
        'service': 'WFS',
        'version': '2.0.0',
        'request': 'GetFeature',
        'typeNames': 'postialue:pno_tilasto',  # Tarkat postinumeroalueet
        'outputFormat': 'application/json',
        'srsName': 'EPSG:4326',  # WGS84 koordinaatit (lat/lon)
        # GeoServer format_options: estä geometrian yksinkertaistaminen
        'format_options': 'coordinate_precision:8;decimation:NONE'
    }
    
    try:
        response = requests.get(WFS_URL, params=params, timeout=120)  # Pidempi timeout tarkoille geometrioille
        response.raise_for_status()
        
        geojson_data = response.json()
        
        # Laske geometrien keskimääräinen pisteiden määrä
        total_coords = 0
        feature_count = len(geojson_data['features'])
        
        for feature in geojson_data['features']:
            if feature['geometry']['type'] == 'Polygon':
                total_coords += sum(len(ring) for ring in feature['geometry']['coordinates'])
            elif feature['geometry']['type'] == 'MultiPolygon':
                for polygon in feature['geometry']['coordinates']:
                    total_coords += sum(len(ring) for ring in polygon)
        
        avg_coords = total_coords / feature_count if feature_count > 0 else 0
        
        print(f"✓ Haettiin {feature_count} postinumeroaluetta")
        print(f"  Keskimäärin {avg_coords:.0f} koordinaattipistettä per alue")
        
        # Normalisoi postinumerokentän nimi (eri WFS:t voivat käyttää eri nimiä)
        for feature in geojson_data['features']:
            props = feature['properties']
            # Etsi postinumero eri mahdollisista kentistä
            postcode = (props.get('postinumer') or       # Paavo (vanha)
                       props.get('postinumeroalue') or   # Tilastokeskus pno_tilasto (UUSI!)
                       props.get('posno') or             # Vaihtoehtoinen
                       props.get('posti_alue') or        # Toinen vaihtoehto
                       props.get('postcode') or          # Englanniksi
                       props.get('zipcode'))             # Vielä yksi
            
            if postcode:
                props['postinumer'] = str(postcode)  # Varmista että on string
        
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
    
    # Uusi datarakenne: data[postcode][data][year][building_type][metric]
    available_postcodes = asuntohinta_data['data']
    available_years = sorted(asuntohinta_data['metadata']['years'])
    latest_year = available_years[-1]
    
    print(f"✓ Käytetään vuoden {latest_year} asuntohintoja")
    print(f"  Hintatietoa {len(available_postcodes)} postinumeroalueelta")
    
    # Suodata ja rikasta featuret
    filtered_features = []
    matched_count = 0
    
    for feature in geojson_data['features']:
        postinumero = feature['properties'].get('postinumer', '')
        
        # Tarkista onko tälle postinumerolle asuntohintadataa
        if postinumero in available_postcodes:
            postcode_data = available_postcodes[postinumero]
            
            # Lisää nimi ja kaupunki
            feature['properties']['name'] = postcode_data.get('name', postinumero)
            feature['properties']['city'] = postcode_data.get('city', '')
            
            # Laske keskihinta kaikista talotyyppien hinnoista viimeisimmälle vuodelle
            # (voidaan käyttää myös kartalla, vaikka kartta itse lataa kaikki vuodet)
            if latest_year in postcode_data.get('data', {}):
                year_data = postcode_data['data'][latest_year]
                prices = []
                for building_type in ['1', '2', '3', '5']:  # Kaikki talotyypit
                    if building_type in year_data:
                        price = year_data[building_type].get('keskihinta_aritm_nw')
                        if price is not None:
                            prices.append(price)
                
                if prices:
                    feature['properties']['avg_price'] = sum(prices) / len(prices)
                else:
                    feature['properties']['avg_price'] = None
            else:
                feature['properties']['avg_price'] = None
            
            filtered_features.append(feature)
            matched_count += 1
    
    print(f"✓ Yhdistettiin {matched_count} aluetta asuntohintadataan")
    
    # Luo uusi FeatureCollection
    result = {
        'type': 'FeatureCollection',
        'features': filtered_features
    }
    
    return result
    
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
    print("Postinumeroalueiden lataus Tilastokeskuksesta")
    print("=" * 60)
    
    # 1. Lataa postinumeroalueet Tilastokeskuksen WFS:stä
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
    print("  - Geometria: Tilastokeskus geo.stat.fi (postialue:pno_tilasto)")
    print("  - Asuntohinnat: Tilastokeskus")
    print("=" * 60)


if __name__ == '__main__':
    main()
