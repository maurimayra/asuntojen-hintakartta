# Asuntojen hintakartta

Interaktiivinen kartta Suomen asuntojen keskihinnoista postinumeroalueittain.

**Datalähteet:** 
- Asuntohinnat: Tilastokeskus (StatFin) - Vanhojen osakeasuntojen neliöhinnat postinumeroalueittain
- Postinumeroalueiden geometria: Paituli / TK Paavo 2025

**Yksikkö:** EUR/m²

## Asennus

```bash
# Asenna riippuvuudet
pip install -r requirements.txt
```

## Käyttö

### Täysin toistettava prosessi (suositeltu)

```bash
# 1. Päivitä asuntohintadata Tilastokeskuksesta
python asuntohinnat.py

# 2. Lataa postinumeroalueet Paitulin WFS-rajapinnasta
python lataa_postinumeroalueet.py

# 3. Luo interaktiivinen kartta
python kartta_polygon.py
```

Avaa `kartta.html` selaimessa.

**Huom:** Vaiheet 1 ja 2 hakevat dataa verkosta ja voivat kestää hetken. Kartta generoidaan nopeasti vaiheessa 3.

### Ominaisuudet

Kartta näyttää:
- **Polygon-pohjaiset postinumeroalueet** (ei ympyröitä)
- **Absoluuttiset hinnat** vuosittain (2023, 2024, 2025)
- **Vuosimuutokset** (%-muutos valitulta aikaväliltä)
- **Kaksi näkymää:**
  - Hintanäkymä: Valitse vuosi, näe hinnat postinumeroalueittain
  - Muutosnäkymä: Valitse aikaväli, näe hintojen %-muutokset
- **Hakutoiminto** postinumeroalueille
- **Kaupunkinavigointi** (Helsinki, Espoo, Tampere, jne.)
- **Tilastot** näkyvistä alueista

## Tiedostot

### Dataskriptit
- `asuntohinnat.py` - Hakee asuntohintadatan Tilastokeskuksesta
- `lataa_postinumeroalueet.py` - Hakee postinumeroalueiden geometriat Paitulista
- `kartta_polygon.py` - Luo interaktiivisen kartan (nykyinen versio)

### Datatiedostot (generoituvat)
- `asuntohinnat.json` - Asuntohintadata vuosittain
- `postinumerot_hinnat.geojson` - Postinumeroalueiden geometriat + hinnat
- `postinumerokoordinaatit.json` - Alueiden keskipisteet

### Kartat (generoituvat)
- `kartta.html` - Interaktiivinen polygon-kartta (suositeltu)

### Vanhemmat skriptit (legacy)
- `kartta.py` - Vanha versio (ympyrämerkit)
- `hintakartta.py` / `index.html` - Taulukkonäkymä

## Tekninen toteutus

- **Karttakirjasto:** Leaflet 1.9.4
- **Datalähde:** Paituli WFS API (paituli:tike_paavo_2025)
- **Koordinaattijärjestelmä:** WGS84 (EPSG:4326) kartalla, ETRS-TM35FIN (EPSG:3067) lähteessä
- **Datan yhdistäminen:** Suodatetaan 3026 postinumeroalueesta vain ne 770, joilla on asuntohintadataa
- **Koko:** ~4.4 MB GeoJSON (sisältää polygon-geometriat)

## Lähdeviitteet

- Asuntohinnat: [Tilastokeskus StatFin](https://stat.fi/) - ashi_13mu
- Postinumeroalueet: [Paituli / CSC](https://paituli.csc.fi/) - TK Paavo 2025
- Karttakirjasto: [Leaflet](https://leafletjs.com/)
