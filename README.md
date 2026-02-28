# Asuntojen hintakartta

Interaktiivinen kartta Suomen asuntojen keskihinnoista postinumeroalueittain.

**Datalähde:** Tilastokeskus (StatFin) - Vanhojen osakeasuntojen neliöhinnat postinumeroalueittain

**Yksikkö:** EUR/m²

## Käyttö

```bash
# 1. Päivitä data
python3 asuntohinnat.py

# 2. Luo interaktiivinen kartta
python3 hintakartta.py
```

Avaa `index.html` selaimessa.

## Tiedostot

- `asuntohinnat.py` - Data collector (Tilastokeskus API)
- `asuntohinnat.json` - Hintadata
- `hintakartta.py` - HTML-generaattori
- `index.html` - Interaktiivinen kartta
