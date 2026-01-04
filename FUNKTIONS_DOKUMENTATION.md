# OpenGlider - Funktionsdokumentation

Diese Dokumentation beschreibt die Hauptfunktionen und Klassen des OpenGlider-Projekts, einer Open-Source-Software zur Paraglider-Konstruktion.

## Inhaltsverzeichnis

1. [Hauptmodul (`openglider`)](#hauptmodul-openglider)
2. [Glider-Modul](#glider-modul)
3. [Airfoil-Modul](#airfoil-modul)
4. [Lines-Modul](#lines-modul)
5. [Vector-Modul](#vector-modul)
6. [Mesh-Modul](#mesh-modul)
7. [Plots-Modul](#plots-modul)
8. [Utils-Modul](#utils-modul)

---

## Hauptmodul (`openglider`)

### Funktionen

#### `load(filename)`
Lädt ein Gleitschirm-Projekt aus einer Datei.

**Parameter:**
- `filename` (str): Pfad zur Datei (.json oder .ods)

**Rückgabe:**
- Geladenes Gleitschirm-Objekt (ParametricGlider oder Glider)

**Beispiel:**
```python
glider = openglider.load("demokite.json")
```

#### `save(data, filename, add_meta=True)`
Speichert ein Gleitschirm-Projekt in eine Datei.

**Parameter:**
- `data`: Zu speicherndes Gleitschirm-Objekt
- `filename` (str): Pfad zur Ausgabedatei
- `add_meta` (bool): Ob Metadaten hinzugefügt werden sollen

---

## Glider-Modul

### Klasse: `Glider`

Hauptklasse für 3D-Gleitschirm-Repräsentation.

#### Konstruktor
```python
Glider(cells=None, lineset: LineSet = None)
```

**Parameter:**
- `cells` (List[Cell]): Liste der Zellen des Gleitschirms
- `lineset` (LineSet): Leinensatz des Gleitschirms

#### Wichtige Eigenschaften

- `area` (float): Fläche des Gleitschirms in m²
- `span` (float): Spannweite des Gleitschirms
- `aspect_ratio` (float): Streckung (Span²/Fläche)
- `ribs` (List[Rib]): Liste aller Rippen
- `cells` (List[Cell]): Liste aller Zellen
- `lineset` (LineSet): Leinensatz
- `has_center_cell` (bool): Ob eine Mittelzelle vorhanden ist

#### Wichtige Methoden

##### `get_mesh(midribs=0, add_lines=True)`
Erstellt ein Mesh-Objekt für die Visualisierung.

**Parameter:**
- `midribs` (int): Anzahl der Midribs pro Zelle
- `add_lines` (bool): Ob Leinen hinzugefügt werden sollen

**Rückgabe:** Mesh-Objekt

##### `return_ribs(num=0, ballooning=True)`
Gibt eine Liste von Rippen-Kurven zurück.

**Parameter:**
- `num` (int): Anzahl der Midribs pro Zelle
- `ballooning` (bool): Ob Ballooning berechnet werden soll

**Rückgabe:** Liste von Rippen-Punkten

##### `get_point(y=0, x=-1)`
Gibt einen Punkt auf dem Gleitschirm zurück.

**Parameter:**
- `y` (float): Spannweiten-Argument (0 bis cell_no)
- `x` (float): Chord-Argument (-1 bis 1)

**Rückgabe:** 3D-Punkt

##### `scale(faktor)`
Skaliert den gesamten Gleitschirm.

**Parameter:**
- `faktor` (float): Skalierungsfaktor

##### `mirror(cutmidrib=True)`
Spiegelt den Gleitschirm.

**Parameter:**
- `cutmidrib` (bool): Ob die Mittelrippe entfernt werden soll

##### `copy()`
Erstellt eine tiefe Kopie des Gleitschirms.

##### `copy_complete()`
Erstellt eine gespiegelte und kombinierte Kopie für Export/Visualisierung.

##### `export_3d(path="", *args, **kwargs)`
Exportiert den Gleitschirm in ein 3D-Format.

**Parameter:**
- `path` (str): Ausgabepfad
- Dateityp wird aus der Dateierweiterung erkannt

##### `import_geometry(cls, path, filetype=None)`
Importiert Geometrie aus einer Datei.

**Parameter:**
- `path` (str): Pfad zur Datei
- `filetype` (str, optional): Dateityp (wird aus Pfad erkannt, falls nicht angegeben)

---

### Klasse: `ParametricGlider`

Parametrische (2D) Gleitschirm-Repräsentation für GUI-Eingaben.

#### Konstruktor
```python
ParametricGlider(
    shape, arc, aoa, profiles, profile_merge_curve,
    balloonings, ballooning_merge_curve, lineset,
    speed, glide, zrot, elements=None
)
```

#### Wichtige Eigenschaften

- `shape` (ParametricShape): Form des Gleitschirms
- `arc`: Bogen-Kurve
- `aoa`: Anstellwinkel-Kurve
- `profiles` (List): Liste der Profile
- `balloonings` (List): Liste der Ballooning-Kurven
- `lineset` (LineSet2D): 2D-Leinensatz

#### Methoden

##### `import_ods(path)`
Importiert einen Gleitschirm aus einer ODS-Datei.

##### `export_ods(path)`
Exportiert einen Gleitschirm in eine ODS-Datei.

---

### Klasse: `Rib`

Repräsentiert eine einzelne Rippe des Gleitschirms.

#### Konstruktor
```python
Rib(
    profile_2d=None, startpoint=None, chord=1.0,
    arcang=0, aoa_absolute=0, zrot=0, xrot=0,
    glide=1, name="unnamed rib", startpos=0.0,
    rigidfoils=None, holes=None, material_code=None
)
```

#### Wichtige Eigenschaften

- `profile_2d` (Profile2D): 2D-Profil der Rippe
- `profile_3d` (Profile3D): 3D-Profil der Rippe (berechnet)
- `pos` (np.array): Position der Rippe
- `chord` (float): Sehnenlänge
- `arcang` (float): Bogenwinkel
- `aoa_absolute` (float): Absoluter Anstellwinkel
- `glide` (float): Gleitzahl

#### Wichtige Methoden

##### `align(point, scale=True)`
Transformiert einen 2D- oder 3D-Punkt in die 3D-Position der Rippe.

**Parameter:**
- `point`: 2D oder 3D Punkt
- `scale` (bool): Ob Skalierung angewendet werden soll

**Rückgabe:** Transformierter Punkt

##### `point(x_value)`
Gibt einen Punkt auf der Rippe für einen x-Wert zurück.

**Parameter:**
- `x_value` (float): x-Wert (-1 bis 1)

**Rückgabe:** 3D-Punkt

##### `get_mesh(filled=True, glider=None)`
Erstellt ein Mesh für die Rippe.

---

### Klasse: `Cell`

Repräsentiert eine Zelle des Gleitschirms.

#### Konstruktor
```python
Cell(
    rib1, rib2, ballooning, miniribs=None,
    panels: List[Panel] = None, diagonals: list = None,
    straps: list = None, rigidfoils: list = None,
    name="unnamed", **kwargs
)
```

#### Wichtige Eigenschaften

- `rib1` (Rib): Erste Rippe der Zelle
- `rib2` (Rib): Zweite Rippe der Zelle
- `ballooning` (Ballooning): Ballooning-Kurve
- `miniribs` (List): Liste der Miniribs
- `panels` (List[Panel]): Liste der Panels
- `diagonals` (List): Liste der Diagonalen
- `straps` (List): Liste der Gurte

#### Wichtige Methoden

##### `midrib(y, ballooning=True)`
Gibt eine Midrib-Kurve zurück.

**Parameter:**
- `y` (float): Position zwischen 0 und 1
- `ballooning` (bool): Ob Ballooning angewendet werden soll

**Rückgabe:** Profile3D-Objekt

##### `get_mesh(num_midribs=0)`
Erstellt ein Mesh für die Zelle.

##### `flatten()` 
Abflacht die Zelle für Plot-Erstellung.

---

### Klasse: `GliderProject`

Kombiniert ParametricGlider und Glider3D.

#### Konstruktor
```python
GliderProject(glider_2d, glider_3d=None, name=None)
```

#### Eigenschaften

- `glider` (ParametricGlider): Parametrischer Gleitschirm
- `glider_3d` (Glider): 3D-Gleitschirm
- `name` (str): Name des Projekts

---

## Airfoil-Modul

### Klasse: `Profile2D`

2D-Standard-Profil-Repräsentation.

#### Konstruktor
```python
Profile2D(data, name=None)
```

**Parameter:**
- `data`: Liste von [x, y] Koordinaten
- `name` (str, optional): Name des Profils

#### Wichtige Eigenschaften

- `numpoints` (int): Anzahl der Punkte
- `x_values` (List[float]): x-Werte des Profils
- `thickness` (float): Maximale Dicke
- `camber` (float): Maximale Wölbung
- `noseindex` (int): Index der Nase

#### Wichtige Methoden

##### `__call__(xval)`
Gibt den Index für einen x-Wert zurück.

**Parameter:**
- `xval` (float): x-Wert (-1 bis 1, negativ = Oberseite)

**Rückgabe:** Float-Index

##### `profilepoint(xval, h=-1.0)`
Gibt einen Profilpunkt für einen x-Wert zurück.

**Parameter:**
- `xval` (float): x-Wert
- `h` (float): Höhe (-1: Unterseite, 1: Oberseite, 0: Mitte)

**Rückgabe:** [x, y] Punkt

##### `normalize()`
Normalisiert das Profil (Nase auf (0,0), Länge = 1).

##### `align(p)`
Richtet einen Punkt (x, y) auf dem Profil aus.

**Parameter:**
- `p` (tuple): (x, y) Koordinaten, x: (0,1), y: (-1,1)

**Rückgabe:** [x, y] Punkt

##### `import_from_dat(path)`
Importiert ein Profil aus einer .dat-Datei.

**Parameter:**
- `path` (str): Pfad zur .dat-Datei

**Rückgabe:** Profile2D-Objekt

##### `export_dat(pfad)`
Exportiert das Profil in .dat-Format.

**Parameter:**
- `pfad` (str): Ausgabepfad

##### `compute_naca(naca=1234, numpoints=100)`
Berechnet ein NACA-Profil.

**Parameter:**
- `naca` (int): NACA-Nummer (4-stellig)
- `numpoints` (int): Anzahl der Punkte

**Rückgabe:** Profile2D-Objekt

##### `compute_joukowsky(m=-0.1+0.1j, numpoints=100)`
Berechnet ein Joukowsky-Profil.

##### `set_flap(flap_begin, flap_amount)`
Setzt eine Klappe auf das Profil.

**Parameter:**
- `flap_begin` (float): Beginn der Klappe (0-1)
- `flap_amount` (float): Klappenausschlag

---

## Lines-Modul

### Klasse: `LineSet`

Repräsentiert einen Leinensatz.

#### Konstruktor
```python
LineSet(lines, v_inf=None)
```

**Parameter:**
- `lines` (List[Line]): Liste der Leinen
- `v_inf` (np.array, optional): Anströmgeschwindigkeit

#### Wichtige Eigenschaften

- `lines` (List[Line]): Liste aller Leinen
- `nodes` (set): Set aller Knoten
- `attachment_points` (List): Liste der Anbindungspunkte
- `lower_attachment_points` (List): Liste der unteren Anbindungspunkte

#### Wichtige Methoden

##### `recalc()`
Berechnet die Leinengeometrie neu (inkl. Durchhang).

##### `scale(factor)`
Skaliert den Leinensatz.

**Parameter:**
- `factor` (float): Skalierungsfaktor

##### `get_lines_by_floor(target_floor=0, node=None, en_style=True)`
Gibt Leinen einer bestimmten Etage zurück.

**Parameter:**
- `target_floor` (int): Ziel-Etage
- `node` (Node, optional): Startknoten
- `en_style` (bool): EN-Stil (siehe EN 926.1)

**Rückgabe:** Liste von Leinen

##### `get_floor_strength(node=None)`
Berechnet die Festigkeit pro Etage.

**Rückgabe:** Liste von Festigkeitswerten

##### `get_main_attachment_point()`
Gibt den Haupt-Anbindungspunkt zurück.

**Rückgabe:** AttachmentPoint-Objekt

---

## Vector-Modul

### Funktionen in `vector/functions.py`

#### `norm(vector)`
Berechnet die Norm eines n-dimensionalen Vektors.

**Parameter:**
- `vector` (np.array): Vektor

**Rückgabe:** Norm (float)

#### `normalize(vector)`
Normalisiert einen Vektor.

**Parameter:**
- `vector` (np.array): Vektor

**Rückgabe:** Normalisierter Vektor

#### `rotation_2d(angle)`
Erstellt eine 2D-Rotationsmatrix.

**Parameter:**
- `angle` (float): Winkel in Radiant

**Rückgabe:** 2x2 Rotationsmatrix

#### `rotation_3d(angle, axis=None)`
Erstellt eine 3D-Rotationsmatrix.

**Parameter:**
- `angle` (float): Winkel in Radiant
- `axis` (list, optional): Rotationsachse [x, y, z]

**Rückgabe:** 3x3 Rotationsmatrix

#### `cut(p1, p2, p3, p4)`
Berechnet den Schnittpunkt zweier 2D-Linien.

**Parameter:**
- `p1, p2`: Punkte der ersten Linie
- `p3, p4`: Punkte der zweiten Linie

**Rückgabe:** (Schnittpunkt, k, l) - k und l sind Parameter

#### `vector_angle(v1, v2)`
Berechnet den Winkel zwischen zwei Vektoren.

---

### Klasse: `Polygon2D`

2D-Polygon-Klasse.

#### Methoden

- `area`: Berechnet die Fläche
- `centroid`: Berechnet den Schwerpunkt
- `contains_point(point)`: Prüft, ob ein Punkt im Polygon liegt

---

### Klasse: `PolyLine2D`

2D-Polylinie-Klasse.

#### Methoden

- `length`: Berechnet die Länge
- `get_point(t)`: Gibt einen Punkt bei Parameter t zurück
- `get_tangent(t)`: Gibt den Tangentenvektor zurück

---

## Mesh-Modul

### Klasse: `Mesh`

Repräsentiert ein 3D-Mesh.

#### Konstruktor
```python
Mesh(vertices=None, polygons=None, name="")
```

#### Wichtige Eigenschaften

- `vertices` (List[Vertex]): Liste der Vertices
- `polygons` (List[Polygon]): Liste der Polygone

#### Wichtige Methoden

##### `from_indexed(vertices, polygons_dict, boundary=None)`
Erstellt ein Mesh aus indizierten Daten.

**Parameter:**
- `vertices` (np.array): Array von Vertices
- `polygons_dict` (dict): Dictionary von Polygon-Gruppen
- `boundary` (dict, optional): Boundary-Informationen

**Rückgabe:** Mesh-Objekt

##### `export_obj(path)`
Exportiert das Mesh als OBJ-Datei.

##### `export_stl(path)`
Exportiert das Mesh als STL-Datei.

##### `triangulate()`
Trianguliert das Mesh.

---

### Klasse: `Vertex`

Repräsentiert einen Vertex.

#### Konstruktor
```python
Vertex(x, y, z, attributes=None)
```

#### Methoden

- `copy()`: Erstellt eine Kopie
- `is_equal(other)`: Vergleicht zwei Vertices
- `round(places)`: Rundet Koordinaten

---

## Plots-Modul

### Klasse: `PatternsNew`

Erstellt Plots und Schnittmuster für die Produktion.

#### Konstruktor
```python
PatternsNew(project: GliderProject, config=None)
```

#### Wichtige Methoden

##### `get_all()`
Gibt alle Plots zurück.

**Rückgabe:** Liste von Layout-Objekten

##### `export_dxf(path)`
Exportiert Plots als DXF-Datei.

**Parameter:**
- `path` (str): Ausgabepfad

##### `export_svg(path)`
Exportiert Plots als SVG-Datei.

---

### Klasse: `PlotMaker`

Erstellt Plots für Zellen, Panels, etc.

#### Methoden

- `unwrap()`: Entfaltet die 3D-Geometrie
- `get_all_grouped()`: Gibt alle Plots gruppiert zurück

---

## Utils-Modul

### Klasse: `Distribution`

Verwaltet Punktverteilungen (z.B. für Profile).

#### Konstruktor
```python
Distribution.new(numpoints=20, dist_type=None, fixed_nodes=None, **kwargs)
```

**Parameter:**
- `numpoints` (int): Anzahl der Punkte
- `dist_type` (str): Verteilungstyp ("linear", "cos", "cos_2", "nose_cos")
- `fixed_nodes` (List, optional): Feste Knoten

#### Methoden

##### `from_cos_distribution(numpoints)`
Erstellt eine Cosinus-Verteilung.

##### `from_nose_cos_distribution(numpoints, nose_weight=0.3)`
Erstellt eine Cosinus-Verteilung mit Nase-Gewichtung.

##### `insert_value(value, start_ind=0, to_nose=True)`
Fügt einen Wert ein und verschiebt andere Werte.

##### `get_index(x)`
Gibt den Index für einen x-Wert zurück.

---

### Klasse: `CachedObject`

Basisklasse für Objekte mit Caching.

#### Verwendung

Klasse erbt von `CachedObject` und verwendet `@cached_property` Decorator:

```python
@cached_property("dependency1", "dependency2")
def computed_value(self):
    # Berechnung
    return result
```

---

## Weitere Module

### `jsonify`

Modul für JSON-Serialisierung/Deserialisierung von OpenGlider-Objekten.

- `load(file)`: Lädt aus JSON
- `dump(obj, file, add_meta=True)`: Speichert als JSON

### `graphics`

Modul für Visualisierung (VTK-basiert).

### `config`

Konfigurationsmodul für globale Einstellungen.

---

## Beispiel-Verwendung

```python
import openglider

# Gleitschirm laden
glider = openglider.load("demokite.json")

# Eigenschaften abfragen
print(f"Fläche: {glider.area} m²")
print(f"Spannweite: {glider.span} m")
print(f"Streckung: {glider.aspect_ratio}")

# Mesh erstellen
mesh = glider.get_mesh(midribs=2, add_lines=True)

# Exportieren
mesh.export_obj("glider.obj")

# Projekt erstellen
from openglider.glider.project import GliderProject
project = GliderProject(glider_2d, glider_3d)

# Plots erstellen
from openglider.plots.patterns import PatternsNew
patterns = PatternsNew(project)
patterns.export_dxf("patterns.dxf")
```

---

## Hinweise

- Die meisten Objekte unterstützen JSON-Serialisierung über `__json__()` und `__from_json__()`
- Viele Berechnungen sind gecacht (`@cached_property`) für bessere Performance
- Koordinatensystem: x = vorne/hinten, y = Spannweite, z = oben/unten
- Profile verwenden x-Werte von -1 (Oberseite) bis 1 (Unterseite), 0 = Nase

---

*Dokumentation erstellt am: 2024*
*OpenGlider Version: 0.8.1*

