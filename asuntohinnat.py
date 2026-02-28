#!/usr/bin/env python3
"""
Asuntojen hintakartta
=====================
Hakee postinumeroalueittain vanhojen osakeasuntojen neliöhinnat
Tilastokeskuksen StatFin-rajapinnasta (taulukko: ashi_13mu)

Yksikkö: EUR/m²
"""

import requests
import json
import time
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://statfin.stat.fi/PxWeb/api/v1/fi/StatFin"
TABLE = "ashi/statfin_ashi_pxt_13mu.px"


def get_metadata():
    """Hae taulukon metatiedot"""
    url = f"{BASE_URL}/{TABLE}"
    response = requests.get(url, timeout=30)
    return response.json()


def fetch_prices(postcodes=None, years=['2023', '2024', '2025']):
    """Hae neliöhinnat postinumeroittain"""
    print("Haetaan metadataa...")
    meta = get_metadata()
    
    # Kaikki postinumerot
    all_postcodes = [v for v in meta['variables'][1]['values'] if v != 'SSS']
    
    if postcodes:
        postcodes_to_fetch = [p for p in postcodes if p in all_postcodes]
    else:
        postcodes_to_fetch = all_postcodes
    
    print(f"Postinumerot: {len(postcodes_to_fetch)}")
    
    # Hae data erissä (max ~500 postnumeroa per query)
    results = {}
    batch_size = 400
    
    for i in range(0, len(postcodes_to_fetch), batch_size):
        batch = postcodes_to_fetch[i:i+batch_size]
        print(f"  Haetaan {i+1}-{min(i+batch_size, len(postcodes_to_fetch))}...")
        
        query = {
            "query": [
                {"code": "Vuosi", "selection": {"filter": "item", "values": years}},
                {"code": "Postinumero", "selection": {"filter": "item", "values": batch}},
                {"code": "Talotyyppi", "selection": {"filter": "item", "values": ["1", "2", "3", "5"]}},
                {"code": "Tiedot", "selection": {"filter": "item", "values": ["keskihinta_aritm_nw"]}}
            ],
            "response": {"format": "json"}
        }
        
        url = f"{BASE_URL}/{TABLE}"
        response = requests.post(url, json=query, timeout=60)
        
        if response.status_code == 200:
            data = response.json()
            # Parse data
            for item in data.get('data', []):
                postcode = item['key'][1]
                year = item['key'][0]
                building_type = item['key'][2]
                price = item['values'][0]
                
                if price not in ['.', '..', '']:
                    try:
                        price = float(price)
                        key = f"{postcode}_{year}"
                        if key not in results:
                            results[key] = {}
                        results[key][building_type] = price
                    except:
                        pass
        
        time.sleep(0.5)
    
    return results, meta


def get_postcode_name(postcode, meta):
    """Hae postinumeron nimi"""
    for v in meta['variables']:
        if v['code'] == 'Postinumero':
            for val, text in zip(v['values'], v.get('valueTexts', [])):
                if val == postcode:
                    # Extract city name
                    if '(' in text:
                        city = text.split('(')[-1].replace(')', '').strip()
                    else:
                        city = ''
                    return text, city
    return postcode, ''


def analyze_results(results, meta):
    """Analysoi tulokset"""
    # Ryhmittele vuoden ja postinumeron mukaan
    by_year_postcode = {}
    
    for key, prices in results.items():
        postcode, year = key.rsplit('_', 1)
        
        # Laske keskihinta (kaikki talotyypit)
        valid_prices = [p for p in prices.values() if p and p > 0]
        if valid_prices:
            avg_price = sum(valid_prices) / len(valid_prices)
            
            if year not in by_year_postcode:
                by_year_postcode[year] = {}
            
            name, city = get_postcode_name(postcode, meta)
            by_year_postcode[year][postcode] = {
                'name': name,
                'city': city,
                'avg_price': avg_price,
                'prices': prices
            }
    
    return by_year_postcode


def export_to_json(by_year_postcode, filename="asuntohinnat.json"):
    """Vie JSON:iin"""
    from datetime import datetime
    
    output = {
        "metadata": {
            "source": "Tilastokeskus (StatFin) - Vanhojen osakeasuntojen neliöhinnat postinumeroalueittain",
            "unit": "EUR/m²",
            "table": "ashi_13mu",
            "years": list(by_year_postcode.keys()),
            "last_updated": datetime.now().isoformat()
        },
        "data": by_year_postcode
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"Data viety: {filename}")
    return output


def print_summary(by_year_postcode):
    """Tulosta yhteenveto"""
    print("\n" + "="*60)
    print("Y H T E E N V E T O")
    print("="*60)
    
    for year in sorted(by_year_postcode.keys(), reverse=True):
        data = by_year_postcode[year]
        prices = [v['avg_price'] for v in data.values()]
        
        print(f"\n{year}:")
        print(f"  Postinumeroalueita: {len(data)}")
        print(f"  Keskihinta: {sum(prices)/len(prices):.0f} EUR/m²")
        print(f"  Min: {min(prices):.0f} EUR/m²")
        print(f"  Max: {max(prices):.0f} EUR/m²")
        
        # Top 5 kalleimmat
        top5 = sorted(data.items(), key=lambda x: x[1]['avg_price'], reverse=True)[:5]
        print(f"  Kalleimmat:")
        for postcode, info in top5:
            print(f"    {postcode}: {info['name']} - {info['avg_price']:.0f} EUR/m²")


def main():
    print("="*60)
    print("ASUNTOJEN NELIÖHINNAT POSTINUMEROITTAIN")
    print("Tilastokeskus")
    print("="*60)
    
    # Hae data
    results, meta = fetch_prices(years=['2023', '2024', '2025'])
    
    # Analysoi
    by_year_postcode = analyze_results(results, meta)
    
    # Vie
    output = export_to_json(by_year_postcode, "asuntohinnat.json")
    print_summary(by_year_postcode)
    
    return by_year_postcode, meta


if __name__ == "__main__":
    main()
