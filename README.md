# Asuntojen hintakartta

Interaktiivinen kartta Suomen asuntojen keskihinnoista ja kauppamääristä postinumeroalueittain vuosilta 2009-2026*.

**Datalähteet:** 
- Asuntohinnat ja kauppamäärät: Tilastokeskus (StatFin) - Vanhojen osakeasuntojen neliöhinnat ja kauppojen lukumäärät postinumeroalueittain (taulukko ashi_13mu)
- Postinumeroalueiden geometria: Tilastokeskus geo.stat.fi (postialue:pno_tilasto) - Tarkat postinumeroalueet, ~240 koordinaattipistettä per alue

**Huom:** * = Vuosi 2026 on ennuste, laskettu viimeisen 5 vuoden lineaarisen trendin perusteella

## Ominaisuudet

### 📊 Datasisältö
- **18 vuotta historiallista dataa** (2009-2025) + ennuste vuodelle 2026*
- **Huoneistotyypit:**
  - Kerrostalo yksiöt
  - Kerrostalo kaksiot
  - Kerrostalo kolmiot+
  - Rivitalot yhteensä
- **Kaksi mittaria:**
  - Neliöhinnat (EUR/m²)
  - Kauppojen lukumäärä (kpl)
- **1723 postinumeroaluetta** joilla asuntohintadataa

### 🗺️ Karttaominaisuudet
- **Polygon-pohjaiset postinumeroalueet** (tarkat rajat, ei geometrian yksinkertaistusta)
- **Korkea geometriatarkkuus** - Keskimäärin 240 koordinaattipistettä per alue
- **Absoluuttiset arvot** - valitse vuosi, huoneistotyyppi ja mittari
- **Vuosimuutokset** - vertaa kahta vuotta, näe %-muutokset
- **Intuitiiviset väriskalat:**
  - Hinnoissa: vihreä = halpa, punainen = kallis
  - Kauppojen määrissä: vihreä = paljon kauppoja, punainen = vähän
  - Muutos-%:ssä: vihreä = positiivinen kasvu, punainen = negatiivinen lasku
- **Hakutoiminto** postinumeroalueille
- **Kaupunkinavigointi** (Helsinki, Espoo, Vantaa, Tampere, Turku, Oulu)
- **Dynaamiset tilastot** valituista parametreista

### 🔮 Ennusteet
- **Automaattinen trendianalyysi** viimeisen 5 vuoden datasta
- **Lineaarinen ennuste** vuodelle 2026 sekä hinnoille että kauppamäärille
- **3558 ennustetta** eri postinumeroalueille ja huoneistotyypeille
- **Visuaalinen erottelu** tähdellä (*) ennustevuodesta

## Asennus

```bash
# Asenna riippuvuudet
pip install -r requirements.txt
```

## Käyttö

### GitHub Pages (julkinen kartta)

Kartta päivittyy automaattisesti kerran kuukaudessa GitHub Actionsin kautta:
- 🌐 Käytä suoraan julkista versiota (linkki repositoryn kuvauksessa)
- ⚙️ Automaattinen päivitys joka kuukauden 1. päivä
- 🔄 Manuaalinen päivitys: Actions-välilehdellä → "Päivitä ja julkaise asuntohintakartta" → Run workflow

### Paikallinen käyttö (kehitys/testaus)

```bash
# 1. Päivitä asuntohintadata Tilastokeskuksesta (2009-2025) ja laske ennuste (2026)
python asuntohinnat.py

# 2. Lataa postinumeroalueet Tilastokeskuksen WFS-rajapinnasta
python lataa_postinumeroalueet.py

# 3. Luo interaktiivinen kartta
python kartta_polygon.py
```

Avaa `kartta.html` selaimessa.

**Huom:** Vaiheet 1 ja 2 hakevat dataa verkosta (asuntohinnat.py kestää ~1-2 min). Kartta generoidaan nopeasti vaiheessa 3.

## Tiedostot

### Dataskriptit
- `asuntohinnat.py` - Hakee asuntohintadatan Tilastokeskuksesta (2009-2025) ja laskee ennusteen (2026)
- `lataa_postinumeroalueet.py` - Hakee postinumeroalueiden tarkat geometriat Tilastokeskuksen WFS-rajapinnasta
- `kartta_polygon.py` - Luo interaktiivisen kartan

### Datatiedostot (generoituvat)
- `asuntohinnat.json` - Asuntohintadata vuosittain (2009-2026), huoneistotyypeittäin (~7.9 MB)
- `postinumerot_hinnat.geojson` - Postinumeroalueiden tarkat geometriat + hinnat (~16.6 MB)
- `postinumerokoordinaatit.json` - Alueiden keskipisteet

### Kartat (generoituvat)
- `kartta.html` - Interaktiivinen polygon-kartta (~20.1 MB)

## Tekninen toteutus

- **Karttakirjasto:** Leaflet 1.9.4
- **Datalähde:** 
  - Asuntohinnat: Tilastokeskus StatFin API (ashi_13mu)
  - Geometriat: Tilastokeskus WFS API (postialue:pno_tilasto)
- **Geometriatarkkuus:**
  - 8 desimaalin koordinaattitarkkuus (WFS: `coordinate_precision:8`)
  - Ei geometrian yksinkertaistusta (WFS: `decimation:NONE`, Leaflet: `smoothFactor:0`)
  - Keskimäärin 240 koordinaattipistettä per postinumeroalue
- **Koordinaattijärjestelmä:** WGS84 (EPSG:4326) kartalla, ETRS-TM35FIN (EPSG:3067) lähteessä
- **Datan yhdistäminen:** Suodatetaan 3018 postinumeroalueesta vain ne 1723, joilla on asuntohintadataa
- **Ennustemenetelmä:** Lineaarinen trendi viimeisen 5 vuoden (2021-2025) datasta
- **Datamäärä:** 
  - 18 vuotta (17 todellista + 1 ennuste)
  - 4 huoneistotyyppiä
  - 2 mittaria (hinta, kauppamäärä)
  - 1723 postinumeroaluetta
  - ≈ 123,000 datapistettä
  - ≈ 414,000 koordinaattipistettä geometrioissa

### GitHub Actions deployment

Kartta päivittyy automaattisesti ilman manuaalista työtä:

1. **Workflow ajastus:** Joka kuukauden 1. päivä klo 03:00 UTC
2. **Datan haku:** 
   - Tilastokeskuksen StatFin API → Asuntohinnat (2009-2025)
   - Tilastokeskuksen WFS API → Tarkat postinumeroalueiden geometriat
3. **Ennusteet:** Lineaarinen trendianalyysi → 2026 ennusteet
4. **Kartan generointi:** Python-skriptit luovat kartta.html:n
5. **Julkaisu:** GitHub Pages palvelee automaattisesti päivitetyn kartan

**Edut:**
- ✅ Ei generoituja tiedostoja repositoriossa (repo pysyy kevyenä ~50 KB)
- ✅ Data aina ajantasalla ilman manuaalista päivitystä
- ✅ Täysin toistettava prosessi (lähdekoodista valmiiseen karttaan)
- ✅ Julkinen verkkopalvelu ilman palvelinkuluja

## 💡 Kehitysideat (Tulevat ominaisuudet)

### 1. Edistyneemmät ennustemallit
- **Koneoppimispohjainen ennuste** (esim. ARIMA, Prophet)
- **Luottamusvälit ennusteille** (esim. 80% ja 95% luottamusvälit)
- **Useamman vuoden ennusteet** (2026-2030)
- **Trendianalyysi** joka huomioi kausivaihtelut

### 2. Laajempi data-analyysi
- **Hintahistogrammit** alueittain
- **Korrelaatioanalyysi** (hinnat vs. sijainti, väestötiedot, palvelut)
- **Aikasarja-animaatio** joka näyttää hintojen kehityksen 2009-2026
- **Top/Bottom listat** (eniten nousseet/laskeneet alueet)
- **Keskimääräinen omistusaika** jos data saatavilla

### 3. Vertailutoiminnot
- **Aluevertailu** - valitse 2-5 aluetta ja vertaa niiden kehitystä
- **Naapurustohaku** - näytä alueen ympäristön hintatrendit
- **Samankaltaiset alueet** - etsi hinnaltaan ja kehitykseltään vastaavia alueita
- **Benchmark-indeksi** - vertaa yksittäisiä alueita koko maan keskiarvoon

### 4. Käyttöliittymäparannukset
- **Mobiilioptimeinti** - parempi kosketusnäytön tuki
- **Teema-asetukset** - tumma tila (dark mode)
- **Tulostusystävällinen näkymä** - PDF-vienti
- **Suosikkialueet** - tallenna kiinnostavat alueet selaimen local storageen
- **Jakolinkit** - luo URL joka avaa tietyn asetuksen (vuosi, alue, mittari)

### 5. Datan rikastaminen
- **Yhdistä Paavo-tiedot** - väestö, tulot, koulutustaso, työttömyys
- **Etäisyyslaskelmat** - etäisyys keskustaan, lähimpään metroon/rautatieasemalle
- **Palveludata** - koulut, päiväkodit, kaupat lähistöllä
- **Liikenneyhteydet** - julkisen liikenteen saavutettavuus
- **Uudiskohteet** - yhdistä suunnitellut asuntorakennushankkeet

**Osallistu kehitykseen!** Ehdotuksia ja pull requestejä otetaan vastaan mielellään.

## Lähdeviitteet

- Asuntohinnat: [Tilastokeskus StatFin](https://stat.fi/) - ashi_13mu
- Postinumeroalueet: [Tilastokeskus geo.stat.fi](https://geo.stat.fi/) - postialue:pno_tilasto
- Karttakirjasto: [Leaflet](https://leafletjs.com/)
