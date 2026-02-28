#!/usr/bin/env python3
"""
Asuntojen hintakartta
=====================
Hakee postinumeroalueittain vanhojen osakeasuntojen:
- Neliöhinnat (EUR/m²)
- Kauppojen lukumäärät
- Eriteltynä talotyypin mukaan

Tilastokeskuksen StatFin-rajapinnasta (taulukko: ashi_13mu)
Vuodet: 2009-2025
"""

import requests
import json
import time
import warnings
warnings.filterwarnings('ignore')

BASE_URL = "https://statfin.stat.fi/PxWeb/api/v1/fi/StatFin"
TABLE = "ashi/statfin_ashi_pxt_13mu.px"

# Talotyypit
BUILDING_TYPES = {
    "1": "Kerrostalo yksiöt",
    "2": "Kerrostalo kaksiot", 
    "3": "Kerrostalo kolmiot+",
    "5": "Rivitalot yhteensä"
}


def get_metadata():
    """Hae taulukon metatiedot"""
    url = f"{BASE_URL}/{TABLE}"
    response = requests.get(url, timeout=30)
    return response.json()


def fetch_prices(postcodes=None, years=None):
    """Hae neliöhinnat ja kauppojen lukumäärät postinumeroittain"""
    print("Haetaan metadataa...")
    meta = get_metadata()
    
    # Jos vuosia ei määritelty, hae kaikki 2009 lähtien
    if years is None:
        all_years = meta['variables'][0]['values']  # Kaikki vuodet
        years = [y for y in all_years if int(y) >= 2009]
    
    # Kaikki postinumerot
    all_postcodes = [v for v in meta['variables'][1]['values'] if v != 'SSS']
    
    if postcodes:
        postcodes_to_fetch = [p for p in postcodes if p in all_postcodes]
    else:
        postcodes_to_fetch = all_postcodes
    
    print(f"Vuodet: {len(years)} ({min(years)}-{max(years)})")
    print(f"Postinumerot: {len(postcodes_to_fetch)}")
    
    # Hae data erissä
    results = {}
    batch_size = 300  # Pienempi erä koska haetaan enemmän dataa
    
    for i in range(0, len(postcodes_to_fetch), batch_size):
        batch = postcodes_to_fetch[i:i+batch_size]
        print(f"  Haetaan postinumerot {i+1}-{min(i+batch_size, len(postcodes_to_fetch))}...")
        
        # Hae sekä hinnat että kauppojen lukumäärät
        query = {
            "query": [
                {"code": "Vuosi", "selection": {"filter": "item", "values": years}},
                {"code": "Postinumero", "selection": {"filter": "item", "values": batch}},
                {"code": "Talotyyppi", "selection": {"filter": "item", "values": list(BUILDING_TYPES.keys())}},
                {"code": "Tiedot", "selection": {"filter": "item", "values": ["keskihinta_aritm_nw", "lkm_julk20"]}}
            ],
            "response": {"format": "json"}
        }
        
        url = f"{BASE_URL}/{TABLE}"
        response = requests.post(url, json=query, timeout=90)
        
        if response.status_code == 200:
            data = response.json()
            
            # Hae metriikkien indeksit columns-listasta
            columns = data.get('columns', [])
            metric_indices = {}
            for idx, col in enumerate(columns):
                if col['code'] in ['keskihinta_aritm_nw', 'lkm_julk20']:
                    metric_indices[col['code']] = idx - 3  # Vähennä ensimmäiset 3 key-kenttää
            
            # Parse data
            for item in data.get('data', []):
                year = item['key'][0]
                postcode = item['key'][1]
                building_type = item['key'][2]
                values_list = item['values']
                
                # Rakenne: results[postcode][year][building_type][metric]
                if postcode not in results:
                    results[postcode] = {}
                if year not in results[postcode]:
                    results[postcode][year] = {}
                if building_type not in results[postcode][year]:
                    results[postcode][year][building_type] = {}
                
                # Lisää hinnat ja lukumäärät
                for metric, idx in metric_indices.items():
                    value = values_list[idx]
                    if value not in ['.', '..', '...', '']:
                        try:
                            results[postcode][year][building_type][metric] = float(value)
                        except:
                            pass
        
        time.sleep(0.5)
    
    return results, meta, years


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
    """Analysoi tulokset - ei tarvita enää, data on jo oikeassa muodossa"""
    # Lisää postinumeroiden nimet
    output = {}
    
    for postcode, years_data in results.items():
        name, city = get_postcode_name(postcode, meta)
        
        output[postcode] = {
            'name': name,
            'city': city,
            'data': years_data  # Sisältää: {year: {building_type: {keskihinta_aritm_nw, lukumaara}}}
        }
    
    return output

def calculate_forecast(data, available_years, forecast_year='2026'):
    """
    Laske ennuste seuraavalle vuodelle lineaarisella trendillä
    Käyttää viimeisen 5 vuoden dataa
    """
    print(f"\nLasketaan ennuste vuodelle {forecast_year}...")
    
    # Käytä viimeisiä 5 vuotta ennusteeseen
    recent_years = sorted([y for y in available_years if int(y) >= 2021])[-5:]
    forecast_count = 0
    
    for postcode, info in data.items():
        years_data = info.get('data', {})
        
        # Käy läpi kaikki talotyypit
        for building_type in ['1', '2', '3', '5']:
            # Kerää historiallinen data
            historical_prices = []
            historical_transactions = []
            
            for year in recent_years:
                if year in years_data and building_type in years_data[year]:
                    year_data = years_data[year][building_type]
                    if 'keskihinta_aritm_nw' in year_data and year_data['keskihinta_aritm_nw'] is not None:
                        historical_prices.append((int(year), year_data['keskihinta_aritm_nw']))
                    if 'lkm_julk20' in year_data and year_data['lkm_julk20'] is not None:
                        historical_transactions.append((int(year), year_data['lkm_julk20']))
            
            # Laske ennuste jos tarpeeksi dataa (vähintään 3 vuotta)
            forecast_data = {}
            
            # Ennuste hinnoille
            if len(historical_prices) >= 3:
                # Yksinkertainen lineaarinen trendi
                years = [y[0] for y in historical_prices]
                prices = [y[1] for y in historical_prices]
                
                # Laske keskimääräinen vuosimuutos
                avg_change = sum(prices[i] - prices[i-1] for i in range(1, len(prices))) / (len(prices) - 1)
                forecast_price = prices[-1] + avg_change
                forecast_data['keskihinta_aritm_nw'] = max(0, forecast_price)  # Ei negatiivisia
            
            # Ennuste kaupoille
            if len(historical_transactions) >= 3:
                years = [y[0] for y in historical_transactions]
                trans = [y[1] for y in historical_transactions]
                
                # Laske keskimääräinen vuosimuutos
                avg_change = sum(trans[i] - trans[i-1] for i in range(1, len(trans))) / (len(trans) - 1)
                forecast_trans = trans[-1] + avg_change
                forecast_data['lkm_julk20'] = max(0, round(forecast_trans))  # Ei negatiivisia, pyöristä
            
            # Lisää ennuste dataan
            if forecast_data:
                if forecast_year not in info['data']:
                    info['data'][forecast_year] = {}
                info['data'][forecast_year][building_type] = forecast_data
                forecast_count += 1
    
    print(f"   Luotu {forecast_count} ennustetta")
    return data

def export_to_json(data, available_years, filename="asuntohinnat.json"):
    """Vie JSON:iin"""
    from datetime import datetime
    
    output = {
        "metadata": {
            "source": "Tilastokeskus (StatFin) - Vanhojen osakeasuntojen hinnat ja kaupat postinumeroalueittain",
            "table": "ashi_13mu",
            "years": sorted(available_years),
            "building_types": BUILDING_TYPES,
            "metrics": {
                "keskihinta_aritm_nw": "Neliöhinta (EUR/m²)",
                "lkm_julk20": "Kauppojen lukumäärä (kpl)"
            },
            "forecast_info": "Vuosi 2026* on ennuste, joka on laskettu viimeisen 5 vuoden lineaarisen trendin perusteella",
            "last_updated": datetime.now().isoformat()
        },
        "data": data
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Data viety: {filename}")
    file_size_mb = len(json.dumps(output)) / (1024 * 1024)
    print(f"   Koko: {file_size_mb:.1f} MB")
    return output


def print_summary(data, available_years):
    """Tulosta yhteenveto"""
    print("\n" + "="*60)
    print("Y H T E E N V E T O")
    print("="*60)
    
    # Laske tilastot viimeisimmälle vuodelle (kaikki rakennustyypit)
    latest_year = max(available_years)
    prices = []
    transactions = []
    
    for postcode, info in data.items():
        if latest_year in info['data']:
            year_data = info['data'][latest_year]
            if '1' in year_data:  # Kerrostalo yksiöt
                if 'keskihinta_aritm_nw' in year_data['1']:
                    prices.append(year_data['1']['keskihinta_aritm_nw'])
                if 'lkm_julk20' in year_data['1']:
                    transactions.append(year_data['1']['lkm_julk20'])
    
    forecast_note = "* (ennuste)" if latest_year == "2026" else ""
    print(f"\nVuosi {latest_year}{forecast_note} (kerrostalo yksiöt):")
    print(f"  Postinumeroalueita hintatiedolla: {len(prices)}")
    if prices:
        print(f"  Keskihinta: {sum(prices)/len(prices):.0f} EUR/m²")
        print(f"  Min: {min(prices):.0f} EUR/m²")
        print(f"  Max: {max(prices):.0f} EUR/m²")
    if transactions:
        print(f"  Kauppoja yhteensä: {sum(transactions):.0f} kpl")
        print(f"  Keskimäärin per alue: {sum(transactions)/len(transactions):.0f} kpl")
    
    # Top 5 kalleimmat
    if prices:
        top5_data = []
        for postcode, info in data.items():
            if latest_year in info['data'] and '1' in info['data'][latest_year]:
                if 'keskihinta_aritm_nw' in info['data'][latest_year]['1']:
                    top5_data.append((
                        postcode,
                        info['name'],
                        info['data'][latest_year]['1']['keskihinta_aritm_nw']
                    ))
        
        top5 = sorted(top5_data, key=lambda x: x[2], reverse=True)[:5]
        print(f"\n  Kalleimmat alueet:")
        for postcode, name, price in top5:
            print(f"    {postcode}: {name} - {price:.0f} EUR/m²")
    
    print(f"\nSaatavilla vuodet: {min(available_years)}-{max(available_years)} ({len(available_years)} vuotta)")
    print(f"Talotyypit: {len(BUILDING_TYPES)} ({', '.join(BUILDING_TYPES.values())})")
    print("="*60)


def main():
    print("="*60)
    print("ASUNTOJEN HINNAT JA KAUPAT POSTINUMEROITTAIN")
    print("Tilastokeskus (2009-2025)")
    print("="*60)
    
    # Hae data (kaikki vuodet 2009 lähtien)
    results, meta, available_years = fetch_prices()
    
    # Analysoi
    data = analyze_results(results, meta)
    
    # Laske ennuste vuodelle 2026
    data = calculate_forecast(data, available_years, forecast_year='2026')
    
    # Lisää ennustevuosi saatavillaoleviin vuosiin
    forecast_years = available_years + ['2026']
    
    # Vie
    output = export_to_json(data, forecast_years, "asuntohinnat.json")
    print_summary(data, forecast_years)
    
    return data, meta


if __name__ == "__main__":
    main()
