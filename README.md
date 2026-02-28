# Asuntojen hintakartta

Interaktiivinen kartta Suomen asuntojen keskihinnoista postinumeroalueittain.

**Datalähde:** Tilastokeskus (StatFin) - Vanhojen osakeasuntojen neliöhinnat postinumeroalueittain

**Yksikkö:** EUR/m²

## Käyttö

```bash
# 1. Päivitä data
python3 asuntohinnat.py

# 2. Päivitä interaktiivinen kartta
python3 hintakartta.py   # Taulukko
python3 kartta.py        # Kartta (Leaflet)
```

Avaa `kartta.html` selaimessa.

## Tiedostot

- `asuntohinnat.py` - Data collector
- `asuntohinnat.json` - Hintadata
- `kartta.py` / `kartta.html` - Interaktiivinen Leaflet-kartta
- `hintakartta.py` / `index.html` - Taulukko
