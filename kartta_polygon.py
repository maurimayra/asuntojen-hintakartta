#!/usr/bin/env python3
"""
Asuntojen hintakartta - Polygon-versio
- Vuodet 2009-2025
- Talotyypit (kerrostalot, rivi/ketjutalot, pientalot, kaikki)
- Mittarit (hinnat, kauppojen lukum.)
- Vuosimuutokset
"""

import json

print("Ladataan dataa...")

# Lataa asuntohintadata
with open('asuntohinnat.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Lataa GeoJSON
with open('postinumerot_hinnat.geojson', 'r', encoding='utf-8') as f:
    geojson_data = json.load(f)

# Hae metatiedot
available_years = sorted(data['metadata']['years'])
building_types = data['metadata']['building_types']
latest_year = available_years[-1]

print(f"  Vuodet: {len(available_years)} ({min(available_years)}-{max(available_years)})")
print(f"  Talotyypit: {len(building_types)}")
print(f"  Postinumeroalueita: {len(geojson_data['features'])}")

# Lisää hintadata GeoJSON-featureisiin
print("Yhdistetään dataa...")
for feature in geojson_data['features']:
    postcode = feature['properties']['postinumer']
    feature['properties']['data'] = {}
    
    # Lisää data jos postinumero löytyy
    if postcode in data['data']:
        feature['properties']['data'] = data['data'][postcode]['data']
        # data-rakenne: {year: {building_type: {keskihinta_aritm_nw, lkm_julk20}}}

# Luo JavaScript-muuttujat
years_json = json.dumps(available_years)
building_types_json = json.dumps(building_types)
geojson_json = json.dumps(geojson_data)

# Laske oletustilastot (viimeisin vuosi, kerrostalo yksiöt, hinnat)
default_prices = []
for feature in geojson_data['features']:
    if latest_year in feature['properties'].get('data', {}):
        if '1' in feature['properties']['data'][latest_year]:
            if 'keskihinta_aritm_nw' in feature['properties']['data'][latest_year]['1']:
                default_prices.append(feature['properties']['data'][latest_year]['1']['keskihinta_aritm_nw'])

avg_price = int(sum(default_prices) / len(default_prices)) if default_prices else 0
max_price = int(max(default_prices)) if default_prices else 0
min_price = int(min(default_prices)) if default_prices else 0

html = f'''<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asuntojen hintakartta 2009-{latest_year}</title>
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
        #header .forecast-note {{ opacity: 0.7; font-size: 12px; font-style: italic; margin-top: 5px; }}
        
        #controls {{
            background: #2a5298;
            padding: 15px 20px;
            color: white;
            display: flex;
            gap: 20px;
            align-items: center;
            flex-wrap: wrap;
        }}
        #controls label {{ font-size: 13px; font-weight: 500; margin-right: 5px; }}
        #controls select {{
            padding: 6px 10px;
            border-radius: 4px;
            border: 1px solid #ddd;
            font-size: 14px;
        }}
        #controls .control-group {{
            display: flex;
            align-items: center;
            gap: 10px;
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
        
        #map {{ height: calc(100vh - 270px); width: 100%; }}
        
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
        <p>Osakeasunnot 2009-{latest_year} | Tilastokeskus</p>
        <p class="forecast-note">* Ennuste, laskettu viimeisen 5 vuoden trendin perusteella</p>
    </div>
    
    <div id="controls">
        <div class="control-group">
            <label for="building-type-select">Huoneistotyyppi:</label>
            <select id="building-type-select" onchange="updateMap()">
                <option value="1">Kerrostalo yksiöt</option>
                <option value="2">Kerrostalo kaksiot</option>
                <option value="3">Kerrostalo kolmiot+</option>
                <option value="5" selected>Rivitalot yhteensä</option>
            </select>
        </div>
        
        <div class="control-group">
            <label for="metric-select">Mittari:</label>
            <select id="metric-select" onchange="updateMap()">
                <option value="keskihinta_aritm_nw" selected>Neliöhinta (€/m²)</option>
                <option value="lkm_julk20">Kauppojen lukumäärä</option>
            </select>
        </div>
        
        <div class="control-group">
            <input type="radio" id="mode-absolute" name="mode" value="absolute" checked onchange="updateMap()">
            <label for="mode-absolute">Absoluuttinen</label>
            
            <input type="radio" id="mode-change" name="mode" value="change" onchange="updateMap()">
            <label for="mode-change">Muutos-%</label>
        </div>
        
        <div class="control-group" id="year-selector-single">
            <label for="year-select">Vuosi:</label>
            <select id="year-select" onchange="updateMap()">
                {chr(10).join(f'                <option value="{year}" {"selected" if year == latest_year else ""}>{year}{"*" if year == "2026" else ""}</option>' for year in available_years)}
            </select>
        </div>
        
        <div class="control-group" id="year-selector-range" style="display:none;">
            <label for="year-from">Alku:</label>
            <select id="year-from" onchange="updateMap()">
                {chr(10).join(f'                <option value="{year}">{year}{"*" if year == "2026" else ""}</option>' for year in available_years)}
            </select>
            
            <label for="year-to">Loppu:</label>
            <select id="year-to" onchange="updateMap()">
                {chr(10).join(f'                <option value="{year}" {"selected" if year == latest_year else ""}>{year}{"*" if year == "2026" else ""}</option>' for year in available_years)}
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
    </div>
    
    <div id="search-box">
        <input type="text" id="search" placeholder="Hae postinumeroa..." onkeyup="filterMap()">
    </div>
    
    <div id="map"></div>
    
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <script>
        var map = L.map('map').setView([60.1699, 24.9384], 8);
        
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            attribution: '© OpenStreetMap contributors'
        }}).addTo(map);
        
        // GeoJSON data
        var geojsonData = {geojson_json};
        var availableYears = {years_json};
        var buildingTypes = {building_types_json};
        var geoJsonLayer;
        var currentLegend;
        
        // Värit hinnoille  
        function getColorPrice(price) {{
            if (price > 8000) return '#8B0000';
            else if (price > 6000) return '#e74c3c';
            else if (price > 5000) return '#f39c12';
            else if (price > 4000) return '#f1c40f';
            else if (price > 3000) return '#9acd32';
            else if (price > 2000) return '#27ae60';
            else return '#2ecc71';
        }}
        
        // Värit kauppojen lukumäärille
        function getColorTransactions(count) {{
            if (count > 100) return '#2ecc71';
            else if (count > 50) return '#27ae60';
            else if (count > 30) return '#9acd32';
            else if (count > 20) return '#f1c40f';
            else if (count > 10) return '#f39c12';
            else if (count > 5) return '#e74c3c';
            else return '#8B0000';
        }}
        
        // Värit muutosprosentille
        function getColorChange(change) {{
            if (change > 15) return '#2ecc71';
            else if (change > 10) return '#27ae60';
            else if (change > 5) return '#9acd32';
            else if (change > 0) return '#f1c40f';
            else if (change > -5) return '#f39c12';
            else if (change > -10) return '#e74c3c';
            else return '#8B0000';
        }}
        
        // Hae arvo datasta
        function getValue(feature, year, buildingType, metric) {{
            var data = feature.properties.data;
            if (!data || !data[year] || !data[year][buildingType]) return null;
            return data[year][buildingType][metric] || null;
        }}
        
        // Päivitä kartta
        function updateMap() {{
            var mode = document.querySelector('input[name="mode"]:checked').value;
            var buildingType = document.getElementById('building-type-select').value;
            var metric = document.getElementById('metric-select').value;
            
            // Näytä/piilota vuosivalitsimet
            if (mode === 'absolute') {{
                document.getElementById('year-selector-single').style.display = 'flex';
                document.getElementById('year-selector-range').style.display = 'none';
            }} else {{
                document.getElementById('year-selector-single').style.display = 'none';
                document.getElementById('year-selector-range').style.display = 'flex';
            }}
            
            // Poista vanha layer
            if (geoJsonLayer) map.removeLayer(geoJsonLayer);
            if (currentLegend) map.removeControl(currentLegend);
            
            // Luo uusi layer
            if (mode === 'absolute') {{
                createAbsoluteMap(buildingType, metric);
            }} else {{
                createChangeMap(buildingType, metric);
            }}
            
            updateStats();
        }}
        
        // Luo absoluuttinen kartta
        function createAbsoluteMap(buildingType, metric) {{
            var selectedYear = document.getElementById('year-select').value;
            var isPrice = (metric === 'keskihinta_aritm_nw');
            
            geoJsonLayer = L.geoJSON(geojsonData, {{
                smoothFactor: 0,  // Ei geometrian yksinkertaistusta, tarkemmat rajat
                style: function(feature) {{
                    var value = getValue(feature, selectedYear, buildingType, metric);
                    var color = value ? (isPrice ? getColorPrice(value) : getColorTransactions(value)) : '#ccc';
                    return {{
                        fillColor: color,
                        fillOpacity: 0.7,
                        color: '#fff',
                        weight: 1,
                        opacity: 1
                    }};
                }},
                onEachFeature: function(feature, layer) {{
                    var props = feature.properties;
                    var value = getValue(feature, selectedYear, buildingType, metric);
                    
                    if (value) {{
                        var metricLabel = isPrice ? 'EUR/m²' : 'kpl';
                        var popupContent = '<div class="popup-content">' +
                            '<h3>' + props.postinumer + '</h3>' +
                            '<div class="price">' + value.toLocaleString() + ' ' + metricLabel + '</div>' +
                            '<div class="details">' + props.name + '</div>' +
                            '<div class="details">' + selectedYear + ' | ' + buildingTypes[buildingType] + '</div>' +
                            '</div>';
                        layer.bindPopup(popupContent);
                    }}
                    
                    layer.on('mouseover', function(e) {{
                        this.setStyle({{ fillOpacity: 0.9, weight: 2 }});
                    }});
                    layer.on('mouseout', function(e) {{
                        geoJsonLayer.resetStyle(this);
                    }});
                }}
            }}).addTo(map);
            
            // Legenda
            createLegend(metric);
        }}
        
        // Luo muutoskartta
        function createChangeMap(buildingType, metric) {{
            var yearFrom = document.getElementById('year-from').value;
            var yearTo = document.getElementById('year-to').value;
            
            geoJsonLayer = L.geoJSON(geojsonData, {{
                smoothFactor: 0,  // Ei geometrian yksinkertaistusta, tarkemmat rajat
                style: function(feature) {{
                    var valueFrom = getValue(feature, yearFrom, buildingType, metric);
                    var valueTo = getValue(feature, yearTo, buildingType, metric);
                    
                    if (valueFrom && valueTo && valueFrom > 0) {{
                        var change = ((valueTo - valueFrom) / valueFrom) * 100;
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
                    var valueFrom = getValue(feature, yearFrom, buildingType, metric);
                    var valueTo = getValue(feature, yearTo, buildingType, metric);
                    
                    if (valueFrom && valueTo && valueFrom > 0) {{
                        var change = ((valueTo - valueFrom) / valueFrom) * 100;
                        var absChange = valueTo - valueFrom;
                        var changeSign = change >= 0 ? '+' : '';
                        var isPrice = (metric === 'keskihinta_aritm_nw');
                        var metricLabel = isPrice ? 'EUR/m²' : 'kpl';
                        
                        var popupContent = '<div class="popup-content">' +
                            '<h3>' + props.postinumer + '</h3>' +
                            '<div class="price">' + changeSign + change.toFixed(1) + ' %</div>' +
                            '<div class="details">' + props.name + '</div>' +
                            '<div class="details">' + yearFrom + ': ' + valueFrom.toLocaleString() + ' ' + metricLabel + '<br>' +
                            yearTo + ': ' + valueTo.toLocaleString() + ' ' + metricLabel + '<br>' +
                            'Muutos: ' + changeSign + absChange.toLocaleString() + ' ' + metricLabel + '</div>' +
                            '<div class="details">' + buildingTypes[buildingType] + '</div>' +
                            '</div>';
                        layer.bindPopup(popupContent);
                    }}
                    
                    layer.on('mouseover', function(e) {{
                        this.setStyle({{ fillOpacity: 0.9, weight: 2 }});
                    }});
                    layer.on('mouseout', function(e) {{
                        geoJsonLayer.resetStyle(this);
                    }});
                }}
            }}).addTo(map);
            
            // Legenda muutoksille
            createChangeLegend();
        }}
        
        // Luo legenda
        function createLegend(metric) {{
            currentLegend = L.control({{position: 'bottomright'}});
            currentLegend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'legend');
                
                if (metric === 'keskihinta_aritm_nw') {{
                    div.innerHTML = '<h4>Hinta €/m²</h4>';
                    var grades = [0, 2000, 3000, 4000, 5000, 6000, 8000];
                    var labels = ['< 2000', '2000-3000', '3000-4000', '4000-5000', '5000-6000', '6000-8000', '> 8000'];
                    for (var i = 0; i < grades.length; i++) {{
                        div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + 
                            getColorPrice(grades[i] + 1) + '"></div>' + labels[i] + '</div>';
                    }}
                }} else {{
                    div.innerHTML = '<h4>Kauppoja (kpl)</h4>';
                    var grades = [0, 5, 10, 20, 30, 50, 100];
                    var labels = ['< 5', '5-10', '10-20', '20-30', '30-50', '50-100', '> 100'];
                    for (var i = grades.length - 1; i >= 0; i--) {{
                        div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + 
                            getColorTransactions(grades[i] + 1) + '"></div>' + labels[i] + '</div>';
                    }}
                }}
                return div;
            }};
            currentLegend.addTo(map);
        }}
        
        // Luo legenda muutoksille
        function createChangeLegend() {{
            currentLegend = L.control({{position: 'bottomright'}});
            currentLegend.onAdd = function(map) {{
                var div = L.DomUtil.create('div', 'legend');
                div.innerHTML = '<h4>Muutos-%</h4>';
                var grades = [15, 10, 5, 0, -5, -10];
                var labels = ['> 15%', '10% - 15%', '5% - 10%', '0% - 5%', '-5% - 0%', '-10% - -5%', '< -10%'];
                for (var i = 0; i < grades.length; i++) {{
                    div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + 
                        getColorChange(grades[i] + 1) + '"></div>' + labels[i] + '</div>';
                }}
                div.innerHTML += '<div class="legend-item"><div class="legend-color" style="background:' + 
                    getColorChange(-15) + '"></div>' + labels[6] + '</div>';
                return div;
            }};
            currentLegend.addTo(map);
        }}
        
        // Päivitä tilastot
        function updateStats() {{
            var mode = document.querySelector('input[name="mode"]:checked').value;
            var buildingType = document.getElementById('building-type-select').value;
            var metric = document.getElementById('metric-select').value;
            var isPrice = (metric === 'keskihinta_aritm_nw');
            var metricLabel = isPrice ? 'EUR/m²' : 'kpl';
            
            if (mode === 'absolute') {{
                var selectedYear = document.getElementById('year-select').value;
                var values = [];
                
                geojsonData.features.forEach(function(feature) {{
                    var value = getValue(feature, selectedYear, buildingType, metric);
                    if (value) values.push(value);
                }});
                
                if (values.length > 0) {{
                    var avg = Math.round(values.reduce((a,b) => a + b, 0) / values.length);
                    var max = Math.max(...values);
                    var min = Math.min(...values);
                    
                    document.getElementById('stat-label').textContent = (isPrice ? 'Keskihinta ' : 'Keskiarvo ') + selectedYear;
                    document.getElementById('stat-value').textContent = avg.toLocaleString() + ' ' + metricLabel;
                    document.getElementById('stat-max-label').textContent = isPrice ? 'Kallein' : 'Suurin';
                    document.getElementById('stat-max').textContent = max.toLocaleString() + ' ' + metricLabel;
                    document.getElementById('stat-min-label').textContent = isPrice ? 'Halvin' : 'Pienin';
                    document.getElementById('stat-min').textContent = min.toLocaleString() + ' ' + metricLabel;
                }}
            }} else {{
                var yearFrom = document.getElementById('year-from').value;
                var yearTo = document.getElementById('year-to').value;
                var changes = [];
                
                geojsonData.features.forEach(function(feature) {{
                    var valueFrom = getValue(feature, yearFrom, buildingType, metric);
                    var valueTo = getValue(feature, yearTo, buildingType, metric);
                    if (valueFrom && valueTo && valueFrom > 0) {{
                        var change = ((valueTo - valueFrom) / valueFrom) * 100;
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

# Tallenna HTML
with open('kartta.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"\n✅ Kartta luotu: kartta.html")
print(f"   Postinumeroalueita: {len(geojson_data['features'])}")
print(f"   Saatavilla vuodet: {', '.join(available_years)}")
print(f"   Ominaisuudet:")
print(f"   - Polygon-pohjaiset alueet")
print(f"   - Talotyypit: {', '.join(building_types.values())}")
print(f"   - Mittarit: Neliöhinnat ja kauppojen lukumäärät")
print(f"   - Absoluuttiset arvot ja vuosimuutokset")
