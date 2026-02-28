#!/usr/bin/env python3
"""
Asuntojen hintakartta - Polygon-versio GeoJSON:lla + vuosimuutos
"""

import json

# Lataa asuntohintadata
with open('asuntohinnat.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Lataa GeoJSON
with open('postinumerot_hinnat.geojson', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Hae kaikki vuodet
available_years = sorted(data['metadata']['years'])
latest_year = available_years[-1]
prices = data['data'][latest_year]

# Laske tilastot viimeisimmälle vuodelle
price_values = [p['avg_price'] for p in prices.values()]
avg_price = int(sum(price_values) / len(price_values))
max_price = int(max(price_values))
min_price = int(min(price_values))

# Lisää hintadata GeoJSON-featureisiin kaikille vuosille
for feature in geojson_data['features']:
    postcode = feature['properties']['postinumer']
    feature['properties']['prices'] = {}
    for year in available_years:
        if postcode in data['data'][year]:
            feature['properties']['prices'][year] = int(data['data'][year][postcode]['avg_price'])

# Luo JavaScript-muuttujat
years_json = json.dumps(available_years)

# Muunna GeoJSON JavaScript-muotoon
geojson_json = json.dumps(geojson_data)

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
        
        #controls {{
            background: #2a5298;
            padding: 15px 20px;
            color: white;
            display: flex;
            gap: 25px;
            align-items: center;
            flex-wrap: wrap;
        }}
        #controls label {{ font-size: 13px; font-weight: 500; }}
        #controls select {{
            padding: 6px 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-size: 14px;
            margin-left: 8px;
        }}
        #controls .control-group {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        #controls input[type="radio"] {{
            margin-left: 10px;
            margin-right: 4px;
        }}
        #controls input[type="radio"] {{
            margin-left: 10px;
            margin-right: 4px;
        }}
        
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
        
        #map {{ height: calc(100vh - 230px); width: 100%; }}
        
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
        <h1>🏠 Asuntojen hintakartta</h1>
        <p>Vanhojen osakeasuntojen neliöhinnat ja vuosimuutokset | Tilastokeskus</p>
    </div>
    
    <div id="controls">
        <div class="control-group">
            <input type="radio" id="mode-price" name="mode" value="price" checked onchange="updateMap()">
            <label for="mode-price">Absoluuttinen hinta</label>
            
            <input type="radio" id="mode-change" name="mode" value="change" onchange="updateMap()">
            <label for="mode-change">Vuosimuutos</label>
        </div>
        
        <div class="control-group" id="year-selector-single">
            <label for="year-select">Vuosi:</label>
            <select id="year-select" onchange="updateMap()">
                {chr(10).join(f'                <option value="{year}" {"selected" if year == latest_year else ""}>{year}</option>' for year in available_years)}
            </select>
        </div>
        
        <div class="control-group" id="year-selector-range" style="display:none;">
            <label for="year-from">Alku:</label>
            <select id="year-from" onchange="updateMap()">
                {chr(10).join(f'                <option value="{year}" {"selected" if year == available_years[0] else ""}>{year}</option>' for year in available_years)}
            </select>
            
            <label for="year-to">Loppu:</label>
            <select id="year-to" onchange="updateMap()">
                {chr(10).join(f'                <option value="{year}" {"selected" if year == latest_year else ""}>{year}</option>' for year in available_years)}
            </select>
        </div>
    </div>
    
    <div id="stats">
        <div class="stat-box">
            <div class="label">Postinumeroalueita</div>
            <div class="value">{len(geojson_data['features'])}</div>
        </div>
        <div class="stat-box">
            <div class="label" id="stat-label">Keskihinta {latest_year}</div>
            <div class="value" id="stat-value">{avg_price:,} €/m²</div>
        </div>
        <div class="stat-box">
            <div class="label" id="stat-max-label">Kallein</div>
            <div class="value" style="color: #e74c3c;" id="stat-max">{max_price:,} €/m²</div>
        </div>
        <div class="stat-box">
            <div class="label" id="stat-min-label">Halvin</div>
            <div class="value" style="color: #27ae60;" id="stat-min">{min_price:,} €/m²</div>
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
        
        // GeoJSON data upotettu suoraan
        var geojsonData = {geojson_json};
        var availableYears = {years_json};
        var geoJsonLayer;
        var currentLegend;
        
        // Väri absoluuttiselle hinnalle
        function getColorPrice(price) {{
            if (price > 8000) return '#8B0000';
            else if (price > 6000) return '#e74c3c';
            else if (price > 5000) return '#f39c12';
            else if (price > 4000) return '#f1c40f';
            else if (price > 3000) return '#9acd32';
            else if (price > 2000) return '#27ae60';
            else return '#2ecc71';
        }}
        
        // Väri muutosprosentille
        function getColorChange(change) {{
            if (change > 15) return '#8B0000';
            else if (change > 10) return '#e74c3c';
            else if (change > 5) return '#f39c12';
            else if (change > 0) return '#f1c40f';
            else if (change > -5) return '#9acd32';
            else if (change > -10) return '#27ae60';
            else return '#2ecc71';
        }}
        
        // Päivitä kartta
        function updateMap() {{
            var mode = document.querySelector('input[name="mode"]:checked').value;
            
            // Näytä/piilota vuosivalitsimet
            if (mode === 'price') {{
                document.getElementById('year-selector-single').style.display = 'flex';
                document.getElementById('year-selector-range').style.display = 'none';
            }} else {{
                document.getElementById('year-selector-single').style.display = 'none';
                document.getElementById('year-selector-range').style.display = 'flex';
            }}
            
            // Poista vanha layer
            if (geoJsonLayer) {{
                map.removeLayer(geoJsonLayer);
            }}
            if (currentLegend) {{
                map.removeControl(currentLegend);
            }}
            
            // Luo uusi layer
            if (mode === 'price') {{
                createPriceMap();
            }} else {{
                createChangeMap();
            }}
            
            updateStats();
        }}
        
        // Luo hintakartta
        function createPriceMap() {{
            var selectedYear = document.getElementById('year-select').value;
            
            geoJsonLayer = L.geoJSON(geojsonData, {{
                style: function(feature) {{
                    var price = feature.properties.prices[selectedYear];
                    return {{
                        fillColor: price ? getColorPrice(price) : '#ccc',
                        fillOpacity: 0.7,
                        color: '#fff',
                        weight: 1,
                        opacity: 1
                    }};
                }},
                onEachFeature: function(feature, layer) {{
                    var props = feature.properties;
                    var price = props.prices[selectedYear];
                    
                    if (price) {{
                        var popupContent = '<div class="popup-content">' +
                            '<h3>' + props.postinumer + '</h3>' +
                            '<div class="price">' + price.toLocaleString() + ' €/m²</div>' +
                            '<div class="details">' + props.name + '</div>' +
                            '<div class="year">' + selectedYear + '</div>' +
                            '</div>';
                        layer.bindPopup(popupContent);
                    }}
                    
                    // Hover-efektit
                    layer.on('mouseover', function(e) {{
                        this.setStyle({{
                            fillOpacity: 0.9,
                            weight: 2
                        }});
                    }});
                    
                    layer.on('mouseout', function(e) {{
                        geoJsonLayer.resetStyle(this);
                    }});
                }}
            }}).addTo(map);
            
            // Legenda hinnoille
            currentLegend = L.control({{position: 'bottomright'}});
            currentLegend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML = '<h4>Hinta €/m²</h4>';
                var grades = [0, 2000, 3000, 4000, 5000, 6000, 8000];
                var labels = ['< 2000', '2000-3000', '3000-4000', '4000-5000', '5000-6000', '6000-8000', '> 8000'];
                
                for (var i = 0; i < grades.length; i++) {{
                    div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + 
                        getColorPrice(grades[i] + 1) + '"></div>' + labels[i] + '</div>';
                }}
                return div;
            }};
            currentLegend.addTo(map);
        }}
        
        // Luo muutoskartta
        function createChangeMap() {{
            var yearFrom = document.getElementById('year-from').value;
            var yearTo = document.getElementById('year-to').value;
            
            geoJsonLayer = L.geoJSON(geojsonData, {{
                style: function(feature) {{
                    var priceFrom = feature.properties.prices[yearFrom];
                    var priceTo = feature.properties.prices[yearTo];
                    
                    if (priceFrom && priceTo) {{
                        var change = ((priceTo - priceFrom) / priceFrom) * 100;
                        return {{
                            fillColor: getColorChange(change),
                            fillOpacity: 0.7,
                            color: '#fff',
                            weight: 1,
                            opacity: 1
                        }};
                    }} else {{
                        return {{
                            fillColor: '#ccc',
                            fillOpacity: 0.3,
                            color: '#fff',
                            weight: 1,
                            opacity: 1
                        }};
                    }}
                }},
                onEachFeature: function(feature, layer) {{
                    var props = feature.properties;
                    var priceFrom = props.prices[yearFrom];
                    var priceTo = props.prices[yearTo];
                    
                    if (priceFrom && priceTo) {{
                        var change = ((priceTo - priceFrom) / priceFrom) * 100;
                        var absChange = priceTo - priceFrom;
                        var changeSign = change >= 0 ? '+' : '';
                        
                        var popupContent = '<div class="popup-content">' +
                            '<h3>' + props.postinumer + '</h3>' +
                            '<div class="price">' + changeSign + change.toFixed(1) + ' %</div>' +
                            '<div class="details">' + props.name + '</div>' +
                            '<div class="year">' + yearFrom + ': ' + priceFrom.toLocaleString() + ' €/m²<br>' +
                            yearTo + ': ' + priceTo.toLocaleString() + ' €/m²<br>' +
                            'Muutos: ' + changeSign + absChange.toLocaleString() + ' €/m²</div>' +
                            '</div>';
                        layer.bindPopup(popupContent);
                    }}
                    
                    // Hover-efektit
                    layer.on('mouseover', function(e) {{
                        this.setStyle({{
                            fillOpacity: 0.9,
                            weight: 2
                        }});
                    }});
                    
                    layer.on('mouseout', function(e) {{
                        geoJsonLayer.resetStyle(this);
                    }});
                }}
            }}).addTo(map);
            
            // Legenda muutoksille
            currentLegend = L.control({{position: 'bottomright'}});
            currentLegend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML = '<h4>Muutos %</h4>';
                var grades = [-20, -10, -5, 0, 5, 10, 15];
                var labels = ['< -10%', '-10% - -5%', '-5% - 0%', '0% - 5%', '5% - 10%', '10% - 15%', '> 15%'];
                
                for (var i = 0; i < grades.length; i++) {{
                    div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + 
                        getColorChange(grades[i] + 1) + '"></div>' + labels[i] + '</div>';
                }}
                return div;
            }};
            currentLegend.addTo(map);
        }}
        
        // Päivitä tilastot
        function updateStats() {{
            var mode = document.querySelector('input[name="mode"]:checked').value;
            
            if (mode === 'price') {{
                var selectedYear = document.getElementById('year-select').value;
                var prices = [];
                
                geojsonData.features.forEach(function(feature) {{
                    if (feature.properties.prices[selectedYear]) {{
                        prices.push(feature.properties.prices[selectedYear]);
                    }}
                }});
                
                if (prices.length > 0) {{
                    var avg = Math.round(prices.reduce((a,b) => a + b, 0) / prices.length);
                    var max = Math.max(...prices);
                    var min = Math.min(...prices);
                    
                    document.getElementById('stat-label').textContent = 'Keskihinta ' + selectedYear;
                    document.getElementById('stat-value').textContent = avg.toLocaleString() + ' €/m²';
                    document.getElementById('stat-max-label').textContent = 'Kallein';
                    document.getElementById('stat-max').textContent = max.toLocaleString() + ' €/m²';
                    document.getElementById('stat-min-label').textContent = 'Halvin';
                    document.getElementById('stat-min').textContent = min.toLocaleString() + ' €/m²';
                }}
            }} else {{
                var yearFrom = document.getElementById('year-from').value;
                var yearTo = document.getElementById('year-to').value;
                var changes = [];
                
                geojsonData.features.forEach(function(feature) {{
                    var priceFrom = feature.properties.prices[yearFrom];
                    var priceTo = feature.properties.prices[yearTo];
                    
                    if (priceFrom && priceTo) {{
                        var change = ((priceTo - priceFrom) / priceFrom) * 100;
                        changes.push(change);
                    }}
                }});
                
                if (changes.length > 0) {{
                    var avg = changes.reduce((a,b) => a + b, 0) / changes.length;
                    var max = Math.max(...changes);
                    var min = Math.min(...changes);
                    
                    document.getElementById('stat-label').textContent = 'Keskimuutos ' + yearFrom + '-' + yearTo;
                    document.getElementById('stat-value').textContent = (avg >= 0 ? '+' : '') + avg.toFixed(1) + ' %';
                    document.getElementById('stat-max-label').textContent = 'Suurin nousu';
                    document.getElementById('stat-max').textContent = '+' + max.toFixed(1) + ' %';
                    document.getElementById('stat-min-label').textContent = 'Suurin lasku';
                    document.getElementById('stat-min').textContent = min.toFixed(1) + ' %';
                }}
            }}
        }}
        
        // Hakutoiminto
        function filterMap() {{
            var query = document.getElementById('search').value.toLowerCase();
            
            geoJsonLayer.eachLayer(function(layer) {{
                var props = layer.feature.properties;
                var postcode = props.postinumer.toLowerCase();
                var name = props.name.toLowerCase();
                
                if (query === '' || postcode.includes(query) || name.includes(query)) {{
                    layer.setStyle({{opacity: 1, fillOpacity: 0.7}});
                }} else {{
                    layer.setStyle({{opacity: 0.1, fillOpacity: 0.1}});
                }}
            }});
        }}
        
        // Alusta kartta
        updateMap();
    </script>
</body>
</html>
'''

with open('kartta.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"✅ Kartta luotu: kartta.html")
print(f"   Postinumeroalueita: {len(geojson_data['features'])}")
print(f"   Saatavilla vuodet: {', '.join(available_years)}")
print(f"   Ominaisuudet:")
print(f"   - Polygon-pohjaiset alueet")
print(f"   - Absoluuttiset hinnat vuosittain")
print(f"   - Vuosimuutokset (%-muutos)")
print(f"   - Vapaasti valittava aikaväli")
