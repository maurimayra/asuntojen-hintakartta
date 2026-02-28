#!/usr/bin/env python3
"""
Asuntojen hintakartta - Interaktiivinen HTML
============================================
Luo interaktiivisen kartan postinumeroalueittain
"""

import json

# Lataa data
with open('asuntohinnat.json', 'r') as f:
    data = json.load(f)

# Ota viimeisin vuosi
latest_year = max(data['data'].keys())
prices = data['data'][latest_year]

# Ryhmittele kaupungeittain
by_city = {}
for postcode, info in prices.items():
    city = info.get('city', 'Muu')
    if city not in by_city:
        by_city[city] = []
    by_city[city].append({
        'postcode': postcode,
        'name': info['name'],
        'price': info['avg_price']
    })

# Laske kaupungittain keskiarvot

# Overall stats
all_prices = [info['avg_price'] for info in prices.values()]
overall_avg = sum(all_prices) / len(all_prices) if all_prices else 0
city_stats = {}
for city, areas in by_city.items():
    prices_list = [a['price'] for a in areas]
    city_stats[city] = {
        'count': len(areas),
        'avg_price': sum(prices_list) / len(prices_list),
        'min': min(prices_list),
        'max': max(prices_list)
    }

# Järjestä kaupungit kalliin mukaan
sorted_cities = sorted(city_stats.items(), key=lambda x: x[1]['avg_price'], reverse=True)

# Luo HTML
html = f"""<!DOCTYPE html>
<html lang="fi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Asuntojen hintakartta {latest_year}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        .stats {{ display: flex; gap: 20px; margin: 20px 0; flex-wrap: wrap; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); min-width: 200px; }}
        .stat-card h3 {{ margin: 0 0 10px 0; color: #666; font-size: 14px; }}
        .stat-card .value {{ font-size: 28px; font-weight: bold; color: #333; }}
        .city-section {{ margin: 30px 0; }}
        .city-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }}
        .city-header h2 {{ margin: 0; }}
        .city-stats {{ color: #666; }}
        table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #f8f9fa; font-weight: 600; color: #666; }}
        tr:hover {{ background: #f8f9fa; }}
        .price {{ font-weight: 600; }}
        .price-high {{ color: #e74c3c; }}
        .price-medium {{ color: #f39c12; }}
        .price-low {{ color: #27ae60; }}
        .legend {{ display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }}
        .legend-item {{ display: flex; align-items: center; gap: 5px; }}
        .legend-color {{ width: 20px; height: 20px; border-radius: 3px; }}
        .search {{ margin: 20px 0; }}
        .search input {{ padding: 10px 15px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; width: 300px; }}
        @media (max-width: 768px) {{ .search input {{ width: 100%; }} }}
    </style>
</head>
<body>
    <h1>🏠 Asuntojen keskihintakartta {latest_year}</h1>
    <p>Vanhojen osakeasuntojen neliöhinnat postinumeroalueittain (EUR/m²)</p>
    
    <div class="stats">
        <div class="stat-card">
            <h3>Postinumeroalueita</h3>
            <div class="value">{len(prices)}</div>
        </div>
        <div class="stat-card">
            <h3>Keskihinta</h3>
            <div class="value">{int(overall_avg):,} €/m²</div>
        </div>
        <div class="stat-card">
            <h3>Kallein</h3>
            <div class="value" style="color: #e74c3c;">{int(max(c['avg_price'] for c in city_stats.values())):,} €/m²</div>
        </div>
        <div class="stat-card">
            <h3>Halvin</h3>
            <div class="value" style="color: #27ae60;">{int(min(c['avg_price'] for c in city_stats.values())):,} €/m²</div>
        </div>
    </div>
    
    <div class="search">
        <input type="text" id="searchInput" placeholder="Hae postinumeroa tai aluetta..." onkeyup="filterTable()">
    </div>
    
    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background: #e74c3c;"></div> Yli 5000 €/m²</div>
        <div class="legend-item"><div class="legend-color" style="background: #f39c12;"></div> 3000-5000 €/m²</div>
        <div class="legend-item"><div class="legend-color" style="background: #f1c40f;"></div> 2000-3000 €/m²</div>
        <div class="legend-item"><div class="legend-color" style="background: #27ae60;"></div> Alle 2000 €/m²</div>
    </div>
"""

# Lisää kaupungit
for city, stats in sorted_cities[:15]:  # Top 15 kaupunkia
    city_areas = sorted(by_city[city], key=lambda x: x['price'], reverse=True)
    
    html += f"""
    <div class="city-section">
        <div class="city-header">
            <h2>🏙️ {city}</h2>
            <div class="city-stats">
                Keskihinta: <strong>{int(stats['avg_price']):,} €/m²</strong> | 
                Alueita: {stats['count']}
            </div>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Postinumero</th>
                    <th>Alue</th>
                    <th>Hinta €/m²</th>
                </tr>
            </thead>
            <tbody>
"""
    
    for area in city_areas[:20]:  # Top 20 per kaupunki
        price = area['price']
        if price > 5000:
            price_class = 'price-high'
        elif price > 3000:
            price_class = 'price-medium'
        elif price > 2000:
            price_class = ''
        else:
            price_class = 'price-low'
        
        html += f"""
                <tr>
                    <td>{area['postcode']}</td>
                    <td>{area['name']}</td>
                    <td class="price {price_class}">{int(price):,}</td>
                </tr>
"""
    
    html += """
            </tbody>
        </table>
    </div>
"""

html += """
    <script>
    function filterTable() {
        const input = document.getElementById('searchInput');
        const filter = input.value.toLowerCase();
        const tables = document.querySelectorAll('table');
        
        tables.forEach(table => {
            const rows = table.querySelectorAll('tbody tr');
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(filter) ? '' : 'none';
            });
        });
    }
    </script>
</body>
</html>
"""

# Tallenna
with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f"Interaktiivinen kartta: index.html")
print(f"Alueita: {len(prices)}")
print(f"Kaupunkeja: {len(by_city)}")
