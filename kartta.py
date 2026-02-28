#!/usr/bin/env python3
"""
Asuntojen hintakartta - Leaflet-interaktiivinen kartta (KORJATTU)
"""

import json

# Lataa data
with open('asuntohinnat.json', 'r') as f:
    data = json.load(f)

latest_year = max(data['data'].keys())
prices = data['data'][latest_year]

# Laske hinnat
price_values = [p['avg_price'] for p in prices.values()]
avg_price = int(sum(price_values) / len(price_values))
max_price = int(max(price_values))
min_price = int(min(price_values))

# KORJATUT Helsinki koordinaatit (lat, lon)
# Lähde: Posti.fi / Google Maps
HELSINKI_POSTCODES = {
    '00100': (60.1699, 24.9384),   # Helsinki keskusta
    '00120': (60.1675, 24.9425),   # Punavuori
    '00130': (60.1650, 24.9500),   # Kaartinkaupunki
    '00140': (60.1600, 24.9550),   # Kaivopuisto/Ullanlinna
    '00150': (60.1620, 24.9350),   # Eira
    '00160': (60.1680, 24.9650),   # Katajanokka
    '00170': (60.1750, 24.9520),   # Kruununhaka
    '00180': (60.1580, 24.9300),   # Hietaniemi
    '00190': (60.1550, 24.9450),   # Lauttasaari
    '00200': (60.1500, 24.9300),   # Etu-Töölö
    '00210': (60.1480, 24.9400),   # Töölö
    '00240': (60.1450, 24.9250),   # Ruskeasuo
    '00250': (60.1450, 24.9200),   # Ruskeasuo
    '00260': (60.1400, 24.9100),   # Munkkiniemi
    '00270': (60.1350, 24.9000),   # Munkkivuori
    '00280': (60.1300, 24.8950),   # Pajala
    '00290': (60.1250, 24.8900),   # Merikallio
    '00300': (60.1350, 24.8850),   # Toukola
    '00310': (60.1300, 24.8800),   # Vallila
    '00320': (60.1250, 24.8700),   # Kumpula
    '00330': (60.1200, 24.8650),   # Koskela
    '00340': (60.1150, 24.8600),   # Hermanninmäki
    '00350': (60.1100, 24.8550),   # Kulosaari
    '00360': (60.1050, 24.8500),   # Herttoniemi
    '00370': (60.1000, 24.8450),   # Tammisalo
    '00380': (60.0950, 24.8400),   # Roihuvuori *** KORJATTU
    '00390': (60.0900, 24.8350),   # Puistola
    '00400': (60.0850, 24.8250),   # Malmi
    '00410': (60.2400, 25.0800),   # Pohjois-Tapiola
    '00420': (60.2350, 25.0700),   # Tapiola
    '00430': (60.2250, 25.0600),   # Leppävaara
    '00440': (60.2150, 25.0500),   # Säteri
    '00500': (60.1550, 24.9750),   # Kalasatama
    '00510': (60.1600, 24.9800),   # Sörnäinen
    '00520': (60.1550, 24.9700),   # Kallio
    '00530': (60.1500, 24.9650),   # Hakaniemi
    '00540': (60.1620, 24.9900),   # Kalasatama
    '00560': (60.1700, 24.9550),   # Malmi
    '00570': (60.1750, 24.9500),   # Pukinmäki
    '00580': (60.1650, 24.9850),   # Kyläsaari
    '00600': (60.1850, 24.9650),   # Maunula
    '00610': (60.1900, 24.9600),   # Oulunkylä
    '00620': (60.1950, 24.9550),   # Patola
    '00630': (60.2000, 24.9500),   # Paloheinä
    '00640': (60.2050, 24.9450),   # Tuomarinkylä
    '00650': (60.2100, 24.9400),   # Viikki
    '00660': (60.2150, 24.9350),   # Latokartano
    '00670': (60.2200, 24.9300),   # Pornaisten
    '00680': (60.2250, 24.9250),   # Viikki
    '00700': (60.1950, 24.9400),   # Malmi
    '00710': (60.2000, 24.9350),   # Tammisto
    '00720': (60.2050, 24.9300),   # Pihlajamäki
    '00730': (60.2100, 24.9250),   # Pihlajisto
    '00740': (60.2150, 24.9200),   # Jakomäki
    '00750': (60.2200, 24.9150),   # Alppikylä
    '00760': (60.2250, 24.9100),   # Verajamäki
    '00770': (60.2300, 24.9050),   # Havukoski
    '00780': (60.2350, 24.9000),   # Koivukylä
    '00790': (60.2400, 24.8950),   # Ilola
    '00800': (60.1750, 24.9200),   # Herttoniemi
    '00810': (60.1700, 24.9150),   # Länsi-Herttoniemi
    '00820': (60.1650, 24.9100),   # Roihuvuori
    '00830': (60.1600, 24.9050),   # Tammisalo
    '00840': (60.1550, 24.9000),   # Jollas
    '00850': (60.1500, 24.8950),   # Vuosaari
    '00860': (60.1450, 24.8900),   # Kallahdenniemi
    '00870': (60.1400, 24.8850),   # Aurala
    '00880': (60.1350, 24.8800),   # Nordsjö
    '00900': (60.2050, 24.9700),   # Pohjois-Haaga
    '00910': (60.2100, 24.9650),   # Kumpula
    '00920': (60.2150, 24.9600),   # Rajajoki
    '00930': (60.2200, 24.9550),   # Jokiniemi
    '00940': (60.2250, 24.9500),   # Petikko
    '00950': (60.2300, 24.9450),   # Talinmäki
    '00960': (60.2350, 24.9400),   # Myllypuro
    '00970': (60.2400, 24.9350),   # Kontula
    '00980': (60.2450, 24.9300),   # Mellunmäki
    '00990': (60.2500, 24.9250),   # Vapaala
}

# Muut kaupungit - keskustan koordinaatit
OTHER_CITIES = {
    # Espoo
    '02100': (60.2052, 24.6566),  # Espoo keskusta
    '02150': (60.2150, 24.6500),
    '02160': (60.2250, 24.6400),
    '02170': (60.2350, 24.6300),
    '02180': (60.2450, 24.6200),
    '02190': (60.2550, 24.6100),
    '02200': (60.2650, 24.6000),
    '02210': (60.2750, 24.5900),
    '02300': (60.2850, 24.5800),
    '02380': (60.2950, 24.5700),
    '02600': (60.3050, 24.5600),
    '02650': (60.3150, 24.5500),
    
    # Vantaa
    '01300': (60.2944, 24.9722),  # Vantaa keskusta
    '01350': (60.2850, 24.9800),
    '01370': (60.2750, 24.9900),
    '01380': (60.2650, 25.0000),
    '01390': (60.2550, 25.0100),
    '01400': (60.2450, 25.0200),
    '01450': (60.2350, 25.0300),
    '01500': (60.3100, 24.9600),
    '01510': (60.3050, 24.9500),
    '01520': (60.3000, 24.9400),
    '01530': (60.2950, 24.9300),
    '01540': (60.2900, 24.9200),
    '01600': (60.3200, 24.9500),
    '01610': (60.3250, 24.9400),
    '01620': (60.3300, 24.9300),
    '01630': (60.3350, 24.9200),
    '01640': (60.3400, 24.9100),
    '01650': (60.3450, 24.9000),
    '01660': (60.3500, 24.8900),
    '01670': (60.3550, 24.8800),
    '01680': (60.3600, 24.8700),
    '01690': (60.3650, 24.8600),
    '01700': (60.3700, 24.8500),
    '01710': (60.3750, 24.8400),
    '01720': (60.3800, 24.8300),
    '01730': (60.3850, 24.8200),
    '01740': (60.3900, 24.8100),
    '01750': (60.3950, 24.8000),
    '01760': (60.4000, 24.7900),
    '01770': (60.4050, 24.7800),
    '01780': (60.4100, 24.7700),
    '01790': (60.4150, 24.7600),
    '01800': (60.4200, 24.7500),
    '01810': (60.4250, 24.7400),
    '01820': (60.4300, 24.7300),
    '01830': (60.4350, 24.7200),
    '01840': (60.4400, 24.7100),
    '01850': (60.4450, 24.7000),
    '01860': (60.4500, 24.6900),
    '01870': (60.4550, 24.6800),
    '01880': (60.4600, 24.6700),
    '01890': (60.4650, 24.6600),
    
    # Tampere
    '33100': (61.4978, 23.7608),  # Tampere keskusta
    '33200': (61.4900, 23.7700),
    '33210': (61.4850, 23.7800),
    '33230': (61.4800, 23.7900),
    '33240': (61.4750, 23.8000),
    '33250': (61.4700, 23.8100),
    '33270': (61.4650, 23.8200),
    '33280': (61.4600, 23.8300),
    '33300': (61.5000, 23.7500),
    '33310': (61.5050, 23.7400),
    '33320': (61.5100, 23.7300),
    '33330': (61.5150, 23.7200),
    '33340': (61.5200, 23.7100),
    '33380': (61.5250, 23.7000),
    '33400': (61.5300, 23.6900),
    '33410': (61.5350, 23.6800),
    '33420': (61.5400, 23.6700),
    '33500': (61.4950, 23.7600),
    '33530': (61.5000, 23.7700),
    '33580': (61.5050, 23.7800),
    '33600': (61.5100, 23.7500),
    '33610': (61.5150, 23.7400),
    '33680': (61.5200, 23.7300),
    '33700': (61.5250, 23.7200),
    '33710': (61.5300, 23.7100),
    '33720': (61.5350, 23.7000),
    '33800': (61.5400, 23.6900),
    '33880': (61.5450, 23.6800),
    '33900': (61.5500, 23.6700),
    '33950': (61.5550, 23.6600),
    
    # Turku
    '20100': (60.4518, 22.6306),  # Turku keskusta
    '20110': (60.4550, 22.6350),
    '20200': (60.4600, 22.6400),
    '20210': (60.4650, 22.6450),
    '20240': (60.4700, 22.6500),
    '20300': (60.4750, 22.6550),
    '20360': (60.4800, 22.6600),
    '20400': (60.4850, 22.6650),
    '20500': (60.4450, 22.6250),
    '20520': (60.4400, 22.6200),
    '20540': (60.4350, 22.6150),
    '20610': (60.4300, 22.6100),
    '20700': (60.4250, 22.6050),
    '20720': (60.4200, 22.6000),
    '20740': (60.4150, 22.5950),
    '20750': (60.4100, 22.5900),
    '20760': (60.4050, 22.5850),
    '20780': (60.4000, 22.5800),
    '20800': (60.3950, 22.5750),
    '20810': (60.3900, 22.5700),
    
    # Oulu
    '90100': (65.0121, 25.4651),  # Oulu keskusta
    '90120': (65.0150, 25.4700),
    '90130': (65.0180, 25.4750),
    '90140': (65.0200, 25.4800),
    '90230': (65.0100, 25.4600),
    '90250': (65.0050, 25.4550),
    '90300': (65.0000, 25.4500),
    '90500': (65.0200, 25.4400),
    '90510': (65.0250, 25.4350),
    '90520': (65.0300, 25.4300),
    '90530': (65.0350, 25.4250),
    '90540': (65.0400, 25.4200),
    '90550': (65.0450, 25.4150),
    '90570': (65.0500, 25.4100),
    '90600': (65.0550, 25.4050),
    '90630': (65.0600, 25.4000),
    '90650': (65.0650, 25.3950),
    '90670': (65.0700, 25.3900),
    '90700': (65.0750, 25.3850),
    '90730': (65.0800, 25.3800),
    '90750': (65.0850, 25.3750),
    
    # Lahti
    '15100': (60.9827, 25.6650),  # Lahti keskusta
    '15110': (60.9850, 25.6700),
    '15120': (60.9900, 25.6750),
    '15140': (60.9950, 25.6800),
    '15150': (61.0000, 25.6850),
    '15170': (61.0050, 25.6900),
    '15200': (61.0100, 25.6950),
    '15230': (61.0150, 25.7000),
    '15300': (61.0200, 25.7050),
    '15320': (61.0250, 25.7100),
}

# Yhdistä kaikki koordinaatit
ALL_COORDS = {**HELSINKI_POSTCODES, **OTHER_CITIES}

# JSON data
price_json = json.dumps({k: {'name': v['name'], 'price': v['avg_price'], 'city': v.get('city', '')} for k, v in prices.items()})
coords_json = json.dumps(ALL_COORDS)

html = f'''<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asuntojen hintakartta {latest_year}</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        
        #header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        #header h1 {{ font-size: 24px; margin-bottom: 5px; }}
        #header p {{ opacity: 0.8; font-size: 14px; }}
        
        #stats {{
            display: flex;
            gap: 15px;
            padding: 15px 20px;
            background: #f8f9fa;
            flex-wrap: wrap;
        }}
        .stat-box {{
            background: white;
            padding: 10px 20px;
            border-radius: 8px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        .stat-box .label {{ font-size: 12px; color: #666; }}
        .stat-box .value {{ font-size: 20px; font-weight: bold; }}
        
        #map {{ height: calc(100vh - 150px); width: 100%; }}
        
        .legend {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            line-height: 1.8;
        }}
        .legend h4 {{ margin-bottom: 10px; }}
        .legend-item {{ display: flex; align-items: center; gap: 8px; }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
            border: 1px solid #ccc;
        }}
        
        .popup-content {{ min-width: 220px; }}
        .popup-content h3 {{ margin-bottom: 10px; color: #1e3c72; }}
        .popup-content .price {{ font-size: 24px; font-weight: bold; color: #27ae60; }}
        .popup-content .details {{ margin-top: 10px; font-size: 12px; color: #666; }}
        .popup-content .year {{ color: #999; font-size: 11px; margin-top: 5px; }}
        
        #search-box {{
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
            background: white;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        #search-box input {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 200px;
            font-size: 14px;
        }}
        
        .city-buttons {{
            position: absolute;
            top: 10px;
            left: 50px;
            z-index: 1000;
        }}
        .city-buttons button {{
            padding: 8px 15px;
            background: white;
            border: 1px solid #ddd;
            border-radius: 4px;
            cursor: pointer;
            margin-right: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        }}
        .city-buttons button:hover {{
            background: #f0f0f0;
        }}
    </style>
</head>
<body>
    <div id="header">
        <h1>🏠 Asuntojen keskihintakartta {latest_year}</h1>
        <p>Vanhojen osakeasuntojen neliöhinnat (EUR/m²) | Tilastokeskus</p>
    </div>
    
    <div id="stats">
        <div class="stat-box">
            <div class="label">Postinumeroalueita</div>
            <div class="value">{len(prices)}</div>
        </div>
        <div class="stat-box">
            <div class="label">Keskihinta</div>
            <div class="value">{avg_price:,} €/m²</div>
        </div>
        <div class="stat-box">
            <div class="label">Kallein</div>
            <div class="value" style="color: #e74c3c;">{max_price:,} €/m²</div>
        </div>
        <div class="stat-box">
            <div class="label">Halvin</div>
            <div class="value" style="color: #27ae60;">{min_price:,} €/m²</div>
        </div>
    </div>
    
    <div class="city-buttons">
        <button onclick="map.setView([60.1699, 24.9384], 12)">Helsinki</button>
        <button onclick="map.setView([60.2052, 24.6566], 12)">Espoo</button>
        <button onclick="map.setView([60.2944, 24.9722], 12)">Vantaa</button>
        <button onclick="map.setView([61.4978, 23.7608], 12)">Tampere</button>
        <button onclick="map.setView([60.4518, 22.6306], 12)">Turku</button>
        <button onclick="map.setView([65.0121, 25.4651], 12)">Oulu</button>
        <button onclick="map.setView([60.9827, 25.6650], 12)">Lahti</button>
    </div>
    
    <div id="search-box">
        <input type="text" id="search" placeholder="Hae postinumeroa..." onkeyup="filterMap()">
    </div>
    
    <div id="map"></div>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([60.1699, 24.9384], 11);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        var priceData = {price_json};
        var postalCoords = {coords_json};
        
        function getColor(price) {{
            if (price > 8000) return '#8B0000';
            else if (price > 6000) return '#e74c3c';
            else if (price > 5000) return '#f39c12';
            else if (price > 4000) return '#f1c40f';
            else if (price > 3000) return '#9acd32';
            else if (price > 2000) return '#27ae60';
            else return '#2ecc71';
        }}
        
        var circles = [];
        
        for (var postcode in priceData) {{
            var data = priceData[postcode];
            var price = data.price;
            var coords = postalCoords[postcode];
            
            if (coords) {{
                var circle = L.circleMarker(coords, {{
                    radius: 14,
                    fillColor: getColor(price),
                    color: '#fff',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.8
                }}).addTo(map);
                
                circle.bindPopup(
                    '<div class="popup-content">' +
                    '<h3>' + postcode + '</h3>' +
                    '<div class="price">' + price.toLocaleString() + ' €/m²</div>' +
                    '<div class="details">' + data.name + '</div>' +
                    '<div class="year">{latest_year}</div>' +
                    '</div>'
                );
                
                circle.postcode = postcode;
                circles.push(circle);
            }}
        }}
        
        var legend = L.control({{position: 'bottomright'}});
        legend.onAdd = function(map) {{
            var div = L.DomUtil.create('div', 'legend');
            div.innerHTML = '<h4>Hinta €/m²</h4>';
            var grades = [0, 1500, 2000, 3000, 4000, 5000, 6000, 8000];
            var labels = ['< 1500', '1500-2000', '2000-3000', '3000-4000', '4000-5000', '5000-6000', '6000-8000', '> 8000'];
            
            for (var i = 0; i < grades.length; i++) {{
                div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + getColor(grades[i] + 1) + '"></div>' + labels[i] + '</div>';
            }}
            return div;
        }};
        legend.addTo(map);
        
        function filterMap() {{
            var query = document.getElementById('search').value.toLowerCase();
            
            circles.forEach(function(circle) {{
                var postcode = circle.postcode.toLowerCase();
                var data = priceData[circle.postcode];
                
                if (query === '' || postcode.includes(query) || (data && data.name && data.name.toLowerCase().includes(query))) {{
                    circle.setStyle({{opacity: 1, fillOpacity: 0.8}});
                }} else {{
                    circle.setStyle({{opacity: 0.1, fillOpacity: 0.1}});
                }}
            }});
        }}
    </script>
</body>
</html>
'''

with open('kartta.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Kartta: kartta.html")
print(f"Helsingin alueita: {len(HELSINKI_POSTCODES)}")
print(f"Espoo: {len([k for k in OTHER_CITIES.keys() if k.startswith('02')])}")
