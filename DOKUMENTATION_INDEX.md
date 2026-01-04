# OpenGlider - Dokumentationsübersicht

Diese Übersicht führt Sie durch die verfügbare Dokumentation des OpenGlider-Projekts.

## Verfügbare Dokumentationen

### 1. Funktionsdokumentation (`FUNKTIONS_DOKUMENTATION.md`)

**Zielgruppe:** Entwickler, die einen Überblick über die Funktionalität benötigen

**Inhalt:**
- Übersicht über alle Hauptmodule
- Beschreibung der wichtigsten Klassen und Funktionen
- Beispiele für die Verwendung
- Erklärungen zu Konzepten und Datenstrukturen

**Empfohlen für:**
- Neue Entwickler
- Entwickler, die einen Überblick benötigen
- Schnelle Referenz für häufige Aufgaben

[→ Zur Funktionsdokumentation](FUNKTIONS_DOKUMENTATION.md)

---

### 2. API-Referenz (`API_REFERENZ.md`)

**Zielgruppe:** Entwickler, die detaillierte Funktionssignaturen benötigen

**Inhalt:**
- Vollständige Funktionssignaturen
- Parameter-Dokumentation
- Rückgabewerte
- Typ-Hinweise
- Systematische Auflistung aller öffentlichen APIs

**Empfohlen für:**
- Entwickler, die spezifische Funktionen suchen
- API-Integration
- Detaillierte Implementierungsreferenz

[→ Zur API-Referenz](API_REFERENZ.md)

---

### 3. Modul-spezifische READMEs

Jedes Modul hat sein eigenes README mit spezifischen Informationen:

- `openglider/README.md` - Basis-Modul
- `openglider/glider/README.md` - Glider-Modul
- `openglider/airfoil/README.md` - Airfoil-Modul
- `openglider/lines/README.md` - Lines-Modul
- `openglider/mesh/README.md` - Mesh-Modul
- `openglider/plots/README.md` - Plots-Modul

---

## Schnellstart

### Für neue Benutzer

1. Lesen Sie zuerst die [Funktionsdokumentation](FUNKTIONS_DOKUMENTATION.md)
2. Schauen Sie sich die Beispiele an
3. Konsultieren Sie die [API-Referenz](API_REFERENZ.md) für Details

### Für Entwickler

1. Überblick: [Funktionsdokumentation](FUNKTIONS_DOKUMENTATION.md)
2. Detaillierte APIs: [API-Referenz](API_REFERENZ.md)
3. Modul-spezifische Details: READMEs in den jeweiligen Modulen

---

## Modulstruktur

```
openglider/
├── __init__.py          # Hauptmodul (load, save)
├── glider/              # Gleitschirm-Klassen
│   ├── glider.py        # Glider-Klasse
│   ├── rib/             # Rippen-Klassen
│   ├── cell/            # Zellen-Klassen
│   └── parametric/     # Parametrische Gleitschirme
├── airfoil/             # Profil-Klassen
│   └── profile_2d.py    # 2D-Profile
├── lines/               # Leinensatz-Klassen
│   └── lineset.py       # LineSet-Klasse
├── vector/              # Vektor-Operationen
│   └── functions.py     # Vektor-Funktionen
├── mesh/                # Mesh-Klassen
│   └── mesh.py          # Mesh-Klasse
├── plots/               # Plot-Funktionen
│   └── patterns.py      # Schnittmuster
└── utils/               # Hilfsfunktionen
    └── distribution.py  # Punktverteilungen
```

---

## Wichtige Konzepte

### Gleitschirm-Hierarchie

```
Glider
├── Cells (Zellen)
│   ├── Rib1, Rib2 (Rippen)
│   ├── Miniribs (Minirippen)
│   ├── Panels (Paneele)
│   ├── Diagonals (Diagonalen)
│   └── Straps (Gurte)
└── LineSet (Leinensatz)
    ├── Lines (Leinen)
    └── Nodes (Knoten)
```

### Koordinatensystem

- **x**: Vorne/Hinten (positiv = vorne)
- **y**: Spannweite (positiv = rechts)
- **z**: Oben/Unten (positiv = oben)

### Profil-Koordinaten

- **x-Werte**: -1 (Oberseite) bis 1 (Unterseite), 0 = Nase
- **y-Werte**: Dicke des Profils

---

## Beispiel-Workflow

```python
import openglider

# 1. Gleitschirm laden
glider = openglider.load("demokite.json")

# 2. Eigenschaften abfragen
print(f"Fläche: {glider.area} m²")
print(f"Spannweite: {glider.span} m")

# 3. Mesh erstellen
mesh = glider.get_mesh(midribs=2, add_lines=True)

# 4. Exportieren
mesh.export_obj("glider.obj")

# 5. Plots erstellen
from openglider.plots.patterns import PatternsNew
from openglider.glider.project import GliderProject

project = GliderProject(glider_2d, glider_3d)
patterns = PatternsNew(project)
patterns.export_dxf("patterns.dxf")
```

---

## Weitere Ressourcen

- **Haupt-README**: [README.md](README.md)
- **Installationsanleitung**: [INSTALL.md](INSTALL.md)
- **Sphinx-Dokumentation**: `docs/sphinx/` (falls vorhanden)
- **Tests**: `tests/` - Beispiele für Verwendung

---

## Beitrag zur Dokumentation

Wenn Sie Verbesserungen oder Ergänzungen zur Dokumentation haben:

1. Dokumentation aktualisieren
2. Beispiele hinzufügen
3. Fehler korrigieren
4. Pull Request erstellen

---

*Letzte Aktualisierung: 2024*
*OpenGlider Version: 0.8.1*

