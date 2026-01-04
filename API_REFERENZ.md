# OpenGlider - API Referenz

Detaillierte API-Referenz aller öffentlichen Funktionen und Klassen.

## Inhaltsverzeichnis

1. [Hauptmodul](#hauptmodul)
2. [Glider-Klassen](#glider-klassen)
3. [Airfoil-Klassen](#airfoil-klassen)
4. [Lines-Klassen](#lines-klassen)
5. [Vector-Funktionen](#vector-funktionen)
6. [Mesh-Klassen](#mesh-klassen)
7. [Utils-Klassen](#utils-klassen)

---

## Hauptmodul

### `openglider.load(filename)`

Lädt ein Gleitschirm-Projekt.

**Signatur:**
```python
def load(filename) -> Glider | ParametricGlider
```

**Parameter:**
- `filename` (str): Dateipfad (.json oder .ods)

**Rückgabe:** Geladenes Gleitschirm-Objekt

---

### `openglider.save(data, filename, add_meta=True)`

Speichert ein Gleitschirm-Projekt.

**Signatur:**
```python
def save(data, filename: str, add_meta: bool = True) -> None
```

**Parameter:**
- `data`: Zu speicherndes Objekt
- `filename` (str): Ausgabepfad
- `add_meta` (bool): Metadaten hinzufügen

---

## Glider-Klassen

### Klasse: `Glider`

#### Konstruktor

```python
def __init__(self, cells=None, lineset: LineSet = None)
```

#### Methoden

##### Geometrie

```python
def get_mesh(self, midribs: int = 0, add_lines: bool = True) -> Mesh
```
Erstellt ein Mesh für Visualisierung.

```python
def get_mesh_panels(self, num_midribs: int = 0) -> Mesh
```
Erstellt Mesh für Panels.

```python
def get_mesh_hull(self, num_midribs: int = 0, ballooning: bool = True) -> Mesh
```
Erstellt Mesh für Hülle.

```python
def return_ribs(self, num: int = 0, ballooning: bool = True) -> List[List[float]]
```
Gibt Liste von Rippen-Kurven zurück.

```python
def return_ribs_ij(self, num: int = 0) -> List[List[float]]
```
Gibt Liste von 2D-Koordinaten ij zurück.

```python
def get_midrib(self, y: float = 0) -> Profile3D
```
Gibt Midrib bei Position y zurück.

```python
def get_point(self, y: float = 0, x: float = -1) -> np.array
```
Gibt Punkt auf Gleitschirm zurück.

```python
def get_spanwise(self, x: float = None) -> List[np.array]
```
Gibt Liste von Punkten für x-Wert zurück.

##### Transformationen

```python
def scale(self, faktor: float) -> None
```
Skaliert den Gleitschirm.

```python
def mirror(self, cutmidrib: bool = True) -> None
```
Spiegelt den Gleitschirm.

```python
def copy(self) -> Glider
```
Erstellt Kopie.

```python
def copy_complete(self) -> Glider
```
Erstellt gespiegelte und kombinierte Kopie.

##### Import/Export

```python
@classmethod
def import_geometry(cls, path: str, filetype: str = None) -> Glider
```
Importiert Geometrie.

```python
def export_3d(self, path: str = "", *args, **kwargs) -> None
```
Exportiert in 3D-Format.

##### Manipulation

```python
def replace_ribs(self, new_ribs: List[Rib]) -> None
```
Ersetzt Rippen.

```python
def rename_parts(self) -> None
```
Benennt Teile um.

```python
def apply_mean_ribs(self, num_mean: int = 8) -> None
```
Berechnet Mittelrippen.

```python
def close_rib(self, rib: int = -1) -> None
```
Schließt Rippe (setzt auf 0).

##### Anbindungspunkte

```python
def get_rib_attachment_points(self, rib: Rib, brake: bool = True, include_mirrored: bool = True) -> List
```
Gibt Anbindungspunkte einer Rippe zurück.

```python
def get_cell_attachment_points(self, cell: Cell) -> List
```
Gibt Anbindungspunkte einer Zelle zurück.

```python
def get_main_attachment_point(self) -> AttachmentPoint
```
Gibt Haupt-Anbindungspunkt zurück.

#### Eigenschaften

```python
@property
def area(self) -> float
@area.setter
def area(self, area: float) -> None
```
Fläche in m².

```python
@property
def span(self) -> float
@span.setter
def span(self, span: float) -> None
```
Spannweite.

```python
@property
def aspect_ratio(self) -> float
@aspect_ratio.setter
def aspect_ratio(self, aspect_ratio: float) -> None
```
Streckung (Span²/Fläche).

```python
@property
def ribs(self) -> List[Rib]
```
Liste aller Rippen.

```python
@property
def attachment_points(self) -> List[AttachmentPoint]
```
Liste aller Anbindungspunkte.

```python
@property
def has_center_cell(self) -> bool
```
Ob Mittelzelle vorhanden.

```python
@property
def centroid(self) -> float
```
Schwerpunkt (x-Koordinate).

```python
@property
def trailing_edge_length(self) -> float
```
Länge der Hinterkante.

```python
@property
def projected_area(self) -> float
```
Projizierte Fläche.

```python
@property
def glide(self) -> float
@glide.setter
def glide(self, glide: float) -> None
```
Gleitzahl.

---

### Klasse: `Rib`

#### Konstruktor

```python
def __init__(
    self,
    profile_2d: Profile2D = None,
    startpoint: np.array = None,
    chord: float = 1.0,
    arcang: float = 0,
    aoa_absolute: float = 0,
    zrot: float = 0,
    xrot: float = 0,
    glide: float = 1,
    name: str = "unnamed rib",
    startpos: float = 0.0,
    rigidfoils: List = None,
    holes: List = None,
    material_code: str = None
)
```

#### Methoden

##### Transformationen

```python
def align(self, point: np.array, scale: bool = True) -> np.array
```
Transformiert Punkt in 3D-Position der Rippe.

```python
def align_all(self, data: np.array) -> np.array
```
Transformiert Daten-Array.

```python
def align_x(self, x_value: float) -> np.array
```
Gibt Punkt für x-Wert zurück.

```python
def point(self, x_value: float) -> np.array
```
Gibt Punkt auf Rippe zurück.

##### Kopieren/Spiegeln

```python
def copy(self) -> Rib
```
Erstellt Kopie.

```python
def mirror(self) -> None
```
Spiegelt Rippe.

##### Mesh

```python
def get_mesh(self, hole_num: int = 10, glider: Glider = None, filled: bool = False, max_area: float = None) -> Mesh
```
Erstellt Mesh für Rippe.

##### Anbindungspunkte

```python
def get_attachment_points(self, glider: Glider, brake: bool = True) -> List
```
Gibt Anbindungspunkte zurück.

```python
def get_lines(self, glider: Glider, brake: bool = False) -> List[Line]
```
Gibt verbundene Leinen zurück.

#### Eigenschaften

```python
@property
def profile_3d(self) -> Profile3D
```
3D-Profil (berechnet).

```python
@property
def rotation_matrix(self) -> np.array
```
Rotationsmatrix.

```python
@property
def transformation(self) -> Transformation
```
Transformationsmatrix.

```python
@property
def aoa_relative(self) -> float
@aoa_relative.setter
def aoa_relative(self, aoa: float) -> None
```
Relativer Anstellwinkel.

```python
@property
def normalized_normale(self) -> np.array
```
Normalisierte Normale.

```python
@property
def in_plane_normale(self) -> np.array
```
In-Ebene-Normale.

---

### Klasse: `Cell`

#### Konstruktor

```python
def __init__(
    self,
    rib1: Rib,
    rib2: Rib,
    ballooning: Ballooning,
    miniribs: List = None,
    panels: List[Panel] = None,
    diagonals: List = None,
    straps: List = None,
    rigidfoils: List = None,
    name: str = "unnamed",
    **kwargs
)
```

#### Methoden

##### Geometrie

```python
def midrib(self, y: float, ballooning: bool = True) -> Profile3D
```
Gibt Midrib bei Position y zurück.

```python
def get_normvector(self) -> np.array
```
Gibt Normalenvektor zurück.

```python
def get_mesh(self, num_midribs: int = 0) -> Mesh
```
Erstellt Mesh für Zelle.

##### Manipulation

```python
def rename_parts(self, seperate_upper_lower: bool = False) -> None
```
Benennt Teile um.

```python
def rename_panels(self, seperate_upper_lower: bool = False) -> None
```
Benennt Panels um.

#### Eigenschaften

```python
@property
def basic_cell(self) -> BasicCell
```
Basis-Zelle (berechnet).

```python
@property
def rib_profiles_3d(self) -> List[Profile3D]
```
Liste aller 3D-Rippen-Profile.

```python
@property
def span(self) -> float
```
Spannweite der Zelle.

```python
@property
def area(self) -> float
```
Fläche der Zelle.

```python
@property
def projected_area(self) -> float
```
Projizierte Fläche.

```python
@property
def centroid(self) -> np.array
```
Schwerpunkt.

---

### Klasse: `ParametricGlider`

#### Konstruktor

```python
def __init__(
    self,
    shape: ParametricShape,
    arc,
    aoa,
    profiles: List,
    profile_merge_curve,
    balloonings: List,
    ballooning_merge_curve,
    lineset: LineSet2D,
    speed: float,
    glide: float,
    zrot,
    elements: dict = None
)
```

#### Methoden

```python
@classmethod
def import_ods(cls, path: str) -> ParametricGlider
```
Importiert aus ODS-Datei.

```python
def export_ods(self, path: str) -> None
```
Exportiert in ODS-Datei.

```python
def copy(self) -> ParametricGlider
```
Erstellt Kopie.

```python
def get_geomentry_table(self) -> Table
```
Gibt Geometrie-Tabelle zurück.

---

## Airfoil-Klassen

### Klasse: `Profile2D`

#### Konstruktor

```python
def __init__(self, data: List[List[float]], name: str = None)
```

#### Methoden

##### Punktzugriff

```python
def __call__(self, xval: float) -> float
```
Gibt Index für x-Wert zurück.

```python
def profilepoint(self, xval: float, h: float = -1.0) -> np.array
```
Gibt Profilpunkt zurück.

```python
def align(self, p: tuple) -> np.array
```
Richtet Punkt auf Profil aus.

##### Import/Export

```python
@classmethod
def import_from_dat(cls, path: str) -> Profile2D
```
Importiert aus .dat-Datei.

```python
def export_dat(self, pfad: str) -> str
```
Exportiert in .dat-Format.

```python
@classmethod
def from_url(cls, name: str = "atr72sm", url: str = "http://m-selig.ae.illinois.edu/ads/coord/") -> Profile2D
```
Lädt Profil von URL.

##### Berechnung

```python
@classmethod
def compute_naca(cls, naca: int = 1234, numpoints: int = 100) -> Profile2D
```
Berechnet NACA-Profil.

```python
@classmethod
def compute_joukowsky(cls, m: complex = -0.1 + 0.1j, numpoints: int = 100) -> Profile2D
```
Berechnet Joukowsky-Profil.

```python
@classmethod
def compute_vandevooren(cls, tau: float = 0.05, epsilon: float = 0.05, numpoints: int = 100) -> Profile2D
```
Berechnet Van de Vooren-Profil.

```python
@classmethod
def compute_trefftz(cls, m: complex = -0.1 + 0.1j, tau: float = 0.05, numpoints: int = 100) -> Profile2D
```
Berechnet Trefftz-Kutta-Profil.

##### Manipulation

```python
def normalize(self) -> Profile2D
```
Normalisiert Profil.

```python
def set_flap(self, flap_begin: float, flap_amount: float) -> None
```
Setzt Klappe.

```python
def insert_point(self, pos: float, tolerance: float = 1e-5) -> None
```
Fügt Punkt ein.

```python
def remove_points(self, start: float, end: float, tolerance: float = None) -> None
```
Entfernt Punkte.

```python
def move_nearest_point(self, pos: float) -> None
```
Verschiebt nächsten Punkt.

```python
def apply_function(self, foo: Callable) -> None
```
Wendet Funktion auf alle Punkte an.

##### Berechnungen

```python
def calc_drag(self, re: float = 2e6, cl: float = 0.7) -> float
```
Berechnet Widerstand (benötigt XFoil).

#### Eigenschaften

```python
@property
def x_values(self) -> List[float]
@x_values.setter
def x_values(self, xval: List[float]) -> None
```
x-Werte des Profils.

```python
@property
def numpoints(self) -> int
@numpoints.setter
def numpoints(self, numpoints: int) -> None
```
Anzahl der Punkte.

```python
@property
def thickness(self) -> float
@thickness.setter
def thickness(self, newthick: float) -> None
```
Maximale Dicke.

```python
@property
def camber(self) -> float
@camber.setter
def camber(self, newcamber: float) -> None
```
Maximale Wölbung.

```python
@property
def camber_line(self) -> np.array
```
Wölbungslinie.

```python
@property
def has_zero_thickness(self) -> bool
```
Ob Profil keine Dicke hat.

```python
@property
def upper_indices(self) -> range
```
Indizes der Oberseite.

```python
@property
def lower_indices(self) -> range
```
Indizes der Unterseite.

---

## Lines-Klassen

### Klasse: `LineSet`

#### Konstruktor

```python
def __init__(self, lines: List[Line] = None, v_inf: np.array = None)
```

#### Methoden

##### Berechnung

```python
def recalc(self) -> None
```
Berechnet Leinengeometrie neu.

```python
def iterate_target_length(self) -> None
```
Iteriert Ziel-Längen.

##### Transformationen

```python
def scale(self, factor: float) -> LineSet
```
Skaliert Leinensatz.

##### Abfragen

```python
def get_lines_by_floor(self, target_floor: int = 0, node: Node = None, en_style: bool = True) -> List[Line]
```
Gibt Leinen einer Etage zurück.

```python
def get_floor_strength(self, node: Node = None) -> List[float]
```
Berechnet Festigkeit pro Etage.

```python
def get_main_attachment_point(self) -> AttachmentPoint
```
Gibt Haupt-Anbindungspunkt zurück.

```python
def get_upper_connected_lines(self, node: Node) -> List[Line]
```
Gibt nach oben verbundene Leinen zurück.

```python
def get_lower_connected_lines(self, node: Node) -> List[Line]
```
Gibt nach unten verbundene Leinen zurück.

#### Eigenschaften

```python
@property
def lowest_lines(self) -> List[Line]
```
Unterste Leinen.

```python
@property
def uppermost_lines(self) -> List[Line]
```
Oberste Leinen.

```python
@property
def nodes(self) -> set
```
Alle Knoten.

```python
@property
def attachment_points(self) -> List[AttachmentPoint]
```
Anbindungspunkte.

```python
@property
def lower_attachment_points(self) -> List[AttachmentPoint]
```
Untere Anbindungspunkte.

```python
@property
def floors(self) -> dict
```
Anzahl der Etagen pro Knoten.

```python
@property
def total_length(self) -> float
```
Gesamtlänge aller Leinen.

---

## Vector-Funktionen

### `norm(vector)`

**Signatur:**
```python
def norm(vector: np.array) -> float
```

Berechnet Norm eines Vektors.

---

### `normalize(vector)`

**Signatur:**
```python
def normalize(vector: np.array) -> np.array
```

Normalisiert einen Vektor.

---

### `rotation_2d(angle)`

**Signatur:**
```python
def rotation_2d(angle: float) -> np.array
```

Erstellt 2D-Rotationsmatrix.

---

### `rotation_3d(angle, axis=None)`

**Signatur:**
```python
def rotation_3d(angle: float, axis: List[float] = None) -> np.array
```

Erstellt 3D-Rotationsmatrix.

---

### `cut(p1, p2, p3, p4)`

**Signatur:**
```python
def cut(p1: np.array, p2: np.array, p3: np.array, p4: np.array) -> tuple
```

Berechnet Schnittpunkt zweier 2D-Linien.

**Rückgabe:** (Schnittpunkt, k, l)

---

### `vector_angle(v1, v2)`

**Signatur:**
```python
def vector_angle(v1: np.array, v2: np.array) -> float
```

Berechnet Winkel zwischen Vektoren.

---

## Mesh-Klassen

### Klasse: `Mesh`

#### Konstruktor

```python
def __init__(self, vertices: List[Vertex] = None, polygons: List[Polygon] = None, name: str = "")
```

#### Methoden

##### Erstellung

```python
@classmethod
def from_indexed(cls, vertices: np.array, polygons_dict: dict, boundary: dict = None) -> Mesh
```
Erstellt Mesh aus indizierten Daten.

##### Export

```python
def export_obj(self, path: str) -> None
```
Exportiert als OBJ-Datei.

```python
def export_stl(self, path: str) -> None
```
Exportiert als STL-Datei.

```python
def export_dxf(self, path: str) -> None
```
Exportiert als DXF-Datei.

##### Operationen

```python
def triangulate(self) -> None
```
Trianguliert Mesh.

```python
def __add__(self, other: Mesh) -> Mesh
```
Vereinigt zwei Meshes.

---

### Klasse: `Vertex`

#### Konstruktor

```python
def __init__(self, x: float, y: float, z: float, attributes: dict = None)
```

#### Methoden

```python
def copy(self) -> Vertex
```
Erstellt Kopie.

```python
def is_equal(self, other: Vertex) -> bool
```
Vergleicht Vertices.

```python
def round(self, places: int) -> None
```
Rundet Koordinaten.

```python
def is_in_range(self, minimum: np.array, maximum: np.array) -> bool
```
Prüft, ob Vertex im Bereich liegt.

---

## Utils-Klassen

### Klasse: `Distribution`

#### Konstruktor

```python
@classmethod
def new(cls, numpoints: int = 20, dist_type: str = None, fixed_nodes: List[float] = None, **kwargs) -> Distribution
```

**Verteilungstypen:**
- `"linear"`: Lineare Verteilung
- `"cos"`: Cosinus-Verteilung
- `"cos_2"`: Cosinus-Verteilung Variante 2
- `"nose_cos"`: Cosinus-Verteilung mit Nase-Gewichtung

#### Methoden

```python
def get_index(self, x: float) -> float
```
Gibt Index für x-Wert zurück.

```python
def insert_value(self, value: float, start_ind: int = 0, to_nose: bool = True) -> int
```
Fügt Wert ein.

```python
def insert_values(self, values: List[float]) -> None
```
Fügt mehrere Werte ein.

```python
@classmethod
def from_cos_distribution(cls, numpoints: int) -> Distribution
```
Erstellt Cosinus-Verteilung.

```python
@classmethod
def from_nose_cos_distribution(cls, numpoints: int, nose_weight: float = 0.3) -> Distribution
```
Erstellt Cosinus-Verteilung mit Nase-Gewichtung.

```python
@classmethod
def from_linear(cls, numpoints: int) -> Distribution
```
Erstellt lineare Verteilung.

---

### Klasse: `CachedObject`

Basisklasse für Objekte mit Caching.

**Verwendung:**
```python
from openglider.utils.cache import CachedObject, cached_property

class MyClass(CachedObject):
    @cached_property("dependency1", "dependency2")
    def computed_value(self):
        # Berechnung
        return result
```

---

## Typen und Konstanten

### Koordinatensystem

- **x**: Vorne/Hinten (positiv = vorne)
- **y**: Spannweite (positiv = rechts)
- **z**: Oben/Unten (positiv = oben)

### Profil-Koordinaten

- **x-Werte**: -1 (Oberseite) bis 1 (Unterseite), 0 = Nase
- **y-Werte**: Dicke des Profils

### Einheiten

- Längen: Meter (m)
- Flächen: Quadratmeter (m²)
- Winkel: Radiant (rad) oder Grad (°)

---

*API-Referenz erstellt am: 2024*
*OpenGlider Version: 0.8.1*

