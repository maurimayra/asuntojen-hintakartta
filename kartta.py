#!/usr/bin/env python3
"""
Asuntojen hintakartta - Leaflet-interaktiivinen kartta
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

# Postinumerokoordinaatit (Helsingin keskustan alueet)
HELSINKI_POSTCODES = {
    '00100': (60.1699, 24.9384),
    '00120': (60.1675, 24.9425),
    '00130': (60.1650, 24.9500),
    '00140': (60.1600, 24.9550),
    '00150': (60.1620, 24.9350),
    '00160': (60.1680, 24.9650),
    '00170': (60.1750, 24.9520),
    '00180': (60.1580, 24.9300),
    '00190': (60.1550, 24.9450),
    '00200': (60.1500, 24.9300),
    '00210': (60.1480, 24.9400),
    '00250': (60.1450, 24.9200),
    '00260': (60.1400, 24.9100),
    '00300': (60.1350, 24.8850),
    '00310': (60.1300, 24.8800),
    '00500': (60.1550, 24.9750),
    '00510': (60.1600, 24.9800),
    '00540': (60.1620, 24.9900),
    '00580': (60.1650, 24.9850),
    '00600': (60.1850, 24.9650),
    '00610': (60.1900, 24.9600),
    '00700': (60.1950, 24.9400),
    '00710': (60.2000, 24.9350),
    '00800': (60.1750, 24.9200),
    '00810': (60.1700, 24.9150),
    '00820': (60.1650, 24.9100),
    '00900': (60.2050, 24.9700),
    '00910': (60.2100, 24.9650),
    '00920': (60.2150, 24.9600),
    '00930': (60.2200, 24.9550),
    '00940': (60.2250, 24.9500),
}

# Muut kaupungit
OTHER_CITIES = {
    'Espoo': (60.2052, 24.6566),
    'Vantaa': (60.2944, 24.9722),
    'Tampere': (61.4978, 23.7608),
    'Turku': (60.4518, 22.6306),
    'Oulu': (65.0121, 25.4651),
    'Lahti': (60.9827, 25.6650),
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
