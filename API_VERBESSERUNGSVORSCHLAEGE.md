# API-Verbesserungsvorschläge für OpenGlider

Diese Liste enthält konkrete Verbesserungsvorschläge für die OpenGlider-API, um sie konsistenter, benutzerfreundlicher und wartbarer zu machen.

## Inhaltsverzeichnis

1. [Konsistenz & Namenskonventionen](#konsistenz--namenskonventionen)
2. [Fehlerbehandlung & Validierung](#fehlerbehandlung--validierung)
3. [Typ-Hinweise & Dokumentation](#typ-hinweise--dokumentation)
4. [Rückgabewerte & Methoden-Signaturen](#rückgabewerte--methoden-signaturen)
5. [API-Design-Patterns](#api-design-patterns)
6. [Import/Export-Konsistenz](#importexport-konsistenz)
7. [Getter/Setter-Patterns](#gettersetter-patterns)
8. [Konstruktoren & Factory-Methoden](#konstruktoren--factory-methoden)

---

## 1. Konsistenz & Namenskonventionen

### 1.1 Inkonsistente Methodennamen

**Problem:**
- `return_ribs()` vs `get_midrib()` - "return" vs "get"
- `get_mesh()` vs `get_mesh_panels()` vs `get_mesh_hull()` - unterschiedliche Präfixe
- `export_3d()` vs `export_dat()` vs `export_obj()` - inkonsistente Export-Namen

**Vorschlag:**
```python
# Einheitlich "get_" für alle Getter verwenden
def get_ribs(self, ...)  # statt return_ribs()
def get_ribs_ij(self, ...)  # statt return_ribs_ij()

# Einheitliche Export-Methoden
def export(self, path: str, format: str = None)  # format aus Dateierweiterung
# oder
def export_to_obj(self, path: str)
def export_to_dxf(self, path: str)
def export_to_json(self, path: str)
```

**Priorität:** Hoch

---

### 1.2 Inkonsistente Parameter-Namen

**Problem:**
- `midribs` vs `num_midribs` vs `num_midrib` - unterschiedliche Namen für dasselbe Konzept
- `faktor` vs `factor` - deutsche vs englische Namen
- `pfad` vs `path` - deutsche vs englische Namen

**Vorschlag:**
```python
# Einheitlich englische Namen verwenden
def get_mesh(self, num_midribs: int = 0, add_lines: bool = True)
def scale(self, factor: float)  # statt faktor
def export_dat(self, path: str)  # statt pfad
```

**Priorität:** Hoch

---

### 1.3 Inkonsistente Rückgabewerte

**Problem:**
- Einige Methoden geben `None` zurück, andere das Objekt selbst
- Inkonsistente Rückgabe bei Transformationen (`mirror()` gibt `None`, `copy()` gibt Objekt)

**Vorschlag:**
```python
# Fluent Interface für Transformationen
def scale(self, factor: float) -> 'Glider':
    # ... implementation
    return self

def mirror(self, cutmidrib: bool = True) -> 'Glider':
    # ... implementation
    return self
```

**Priorität:** Mittel

---

## 2. Fehlerbehandlung & Validierung

### 2.1 Fehlende Validierung in Konstruktoren

**Problem:**
- Keine Validierung von Eingabeparametern
- `Rib.__init__()` akzeptiert `None` für `profile_2d`, führt später zu Fehlern

**Vorschlag:**
```python
def __init__(self, profile_2d: Profile2D, startpoint: np.array, ...):
    if profile_2d is None:
        raise ValueError("profile_2d cannot be None")
    if startpoint is None:
        raise ValueError("startpoint cannot be None")
    if len(startpoint) != 3:
        raise ValueError("startpoint must be 3D coordinate")
    # ...
```

**Priorität:** Hoch

---

### 2.2 Fehlende Fehlerbehandlung bei Dateioperationen

**Problem:**
- `load()` und `save()` haben keine explizite Fehlerbehandlung
- Keine Validierung, ob Datei existiert oder schreibbar ist

**Vorschlag:**
```python
def load(filename: str) -> Glider | ParametricGlider:
    """Load glider from file.
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
        JSONDecodeError: If JSON file is invalid
    """
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    try:
        if filename.endswith(".ods"):
            return openglider.glider.ParametricGlider.import_ods(filename)
        else:
            with open(filename) as infile:
                res = openglider.jsonify.load(infile)
            # ...
    except Exception as e:
        raise ValueError(f"Failed to load {filename}: {e}") from e
```

**Priorität:** Hoch

---

### 2.3 Fehlende Validierung bei Geometrie-Operationen

**Problem:**
- `scale(factor)` akzeptiert negative oder Null-Werte
- `get_point(y, x)` hat keine Bereichsvalidierung

**Vorschlag:**
```python
def scale(self, factor: float) -> 'Glider':
    if factor <= 0:
        raise ValueError(f"Scale factor must be positive, got {factor}")
    # ...

def get_point(self, y: float = 0, x: float = -1) -> np.array:
    if not 0 <= y <= len(self.cells):
        raise ValueError(f"y must be between 0 and {len(self.cells)}, got {y}")
    if not -1 <= x <= 1:
        raise ValueError(f"x must be between -1 and 1, got {x}")
    # ...
```

**Priorität:** Mittel

---

## 3. Typ-Hinweise & Dokumentation

### 3.1 Fehlende Type Hints

**Problem:**
- Viele Methoden haben keine Type Hints
- Rückgabetypen sind unklar (`List` statt `List[Rib]`)

**Vorschlag:**
```python
from typing import List, Optional, Union, Tuple

def get_rib_attachment_points(
    self, 
    rib: Rib, 
    brake: bool = True, 
    include_mirrored: bool = True
) -> List[AttachmentPoint]:  # statt List
    # ...

def get_point(self, y: float = 0, x: float = -1) -> np.ndarray:  # statt np.array
    # ...
```

**Priorität:** Mittel

---

### 3.2 Fehlende Docstrings

**Problem:**
- Viele Methoden haben keine oder unvollständige Docstrings
- `load()` hat nur `""" """`

**Vorschlag:**
```python
def load(filename: str) -> Union[Glider, ParametricGlider]:
    """Load a glider project from file.
    
    Args:
        filename: Path to file (.json or .ods format)
        
    Returns:
        Loaded glider object (Glider or ParametricGlider depending on format)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is not supported
        
    Example:
        >>> glider = openglider.load("demokite.json")
        >>> print(glider.area)
    """
    # ...
```

**Priorität:** Mittel

---

### 3.3 Unklare Parameter-Beschreibungen

**Problem:**
- Parameter wie `ballooning=True` sind nicht selbsterklärend
- Keine Beschreibung, was `num_midribs` genau bedeutet

**Vorschlag:**
```python
def return_ribs(
    self, 
    num: int = 0, 
    ballooning: bool = True
) -> List[List[float]]:
    """Get list of rib curves.
    
    Args:
        num: Number of midribs per cell (0 = only main ribs)
        ballooning: If True, apply ballooning deformation to cells
        
    Returns:
        Nested list of rib points: [[[x,y,z], ...], ...]
    """
    # ...
```

**Priorität:** Niedrig

---

## 4. Rückgabewerte & Methoden-Signaturen

### 4.1 Inkonsistente Rückgabetypen

**Problem:**
- `get_rib_attachment_points()` gibt `List` zurück (ohne Typ)
- `get_cell_attachment_points()` gibt `List` zurück
- Sollten beide `List[AttachmentPoint]` sein

**Vorschlag:**
```python
def get_rib_attachment_points(
    self, 
    rib: Rib, 
    brake: bool = True, 
    include_mirrored: bool = True
) -> List[AttachmentPoint]:
    """Get attachment points for a rib."""
    # ...

def get_cell_attachment_points(self, cell: Cell) -> List[AttachmentPoint]:
    """Get attachment points for a cell."""
    # ...
```

**Priorität:** Mittel

---

### 4.2 Magic Numbers und Default-Werte

**Problem:**
- Default-Werte wie `x=-1` sind nicht selbsterklärend
- Magic Numbers in Methoden

**Vorschlag:**
```python
# Konstanten definieren
class Glider:
    TRAILING_EDGE_X = -1.0
    LEADING_EDGE_X = 1.0
    NOSE_X = 0.0
    
    def get_point(self, y: float = 0, x: float = TRAILING_EDGE_X) -> np.ndarray:
        """Get point on glider.
        
        Args:
            y: Span-wise position (0 to number of cells)
            x: Chord-wise position (TRAILING_EDGE_X=-1 to LEADING_EDGE_X=1)
        """
        # ...
```

**Priorität:** Niedrig

---

### 4.3 Fehlende Optionale Parameter

**Problem:**
- `export_3d()` verwendet `*args, **kwargs` - unklar, welche Parameter erlaubt sind
- Kommentar `# todo: fix` deutet auf unvollständige Implementierung hin

**Vorschlag:**
```python
def export_3d(
    self, 
    path: str, 
    format: Optional[str] = None,
    midribs: int = 0,
    numpoints: Optional[int] = None,
    **kwargs
) -> None:
    """Export glider to 3D format.
    
    Args:
        path: Output file path
        format: File format ('obj', 'dxf', 'json', etc.). 
                If None, inferred from file extension
        midribs: Number of midribs per cell
        numpoints: Number of points per rib (if None, uses current)
        **kwargs: Format-specific options
    """
    if format is None:
        format = path.split(".")[-1].lower()
    
    if format not in EXPORT_3D:
        raise ValueError(f"Unsupported format: {format}")
    
    EXPORT_3D[format](self, path, midribs=midribs, numpoints=numpoints, **kwargs)
```

**Priorität:** Hoch

---

## 5. API-Design-Patterns

### 5.1 Context Manager für Dateioperationen

**Problem:**
- Keine Möglichkeit, Ressourcen sicher zu verwalten

**Vorschlag:**
```python
class GliderProject:
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        pass

# Usage:
with GliderProject(glider_2d, glider_3d) as project:
    patterns = PatternsNew(project)
    patterns.export_dxf("patterns.dxf")
```

**Priorität:** Niedrig

---

### 5.2 Builder-Pattern für komplexe Objekte

**Problem:**
- `Glider.__init__()` erfordert viele Parameter
- Schwer, einen Gleitschirm schrittweise aufzubauen

**Vorschlag:**
```python
class GliderBuilder:
    def __init__(self):
        self.cells = []
        self.lineset = None
    
    def add_cell(self, cell: Cell) -> 'GliderBuilder':
        self.cells.append(cell)
        return self
    
    def set_lineset(self, lineset: LineSet) -> 'GliderBuilder':
        self.lineset = lineset
        return self
    
    def build(self) -> Glider:
        return Glider(cells=self.cells, lineset=self.lineset)

# Usage:
glider = (GliderBuilder()
    .add_cell(cell1)
    .add_cell(cell2)
    .set_lineset(lineset)
    .build())
```

**Priorität:** Niedrig

---

### 5.3 Iterator-Pattern für Collections

**Problem:**
- Keine einfache Möglichkeit, über Rippen oder Zellen zu iterieren

**Vorschlag:**
```python
class Glider:
    def __iter__(self):
        """Iterate over cells."""
        return iter(self.cells)
    
    def iter_ribs(self):
        """Iterate over all ribs."""
        for cell in self.cells:
            yield cell.rib1
            yield from cell.miniribs
            yield cell.rib2

# Usage:
for cell in glider:
    print(cell.name)

for rib in glider.iter_ribs():
    print(rib.name)
```

**Priorität:** Niedrig

---

## 6. Import/Export-Konsistenz

### 6.1 Einheitliche Import/Export-API

**Problem:**
- Unterschiedliche Methoden für verschiedene Formate
- `import_geometry()` vs `import_ods()` vs `import_from_dat()`

**Vorschlag:**
```python
class Glider:
    @classmethod
    def load(cls, path: str, format: Optional[str] = None) -> 'Glider':
        """Load glider from file.
        
        Args:
            path: File path
            format: File format (auto-detected from extension if None)
        """
        if format is None:
            format = path.split(".")[-1].lower()
        
        if format not in IMPORT_FORMATS:
            raise ValueError(f"Unsupported format: {format}")
        
        return IMPORT_FORMATS[format](path)
    
    def save(self, path: str, format: Optional[str] = None, **kwargs) -> None:
        """Save glider to file."""
        if format is None:
            format = path.split(".")[-1].lower()
        
        if format not in EXPORT_FORMATS:
            raise ValueError(f"Unsupported format: {format}")
        
        EXPORT_FORMATS[format](self, path, **kwargs)

# Usage:
glider = Glider.load("glider.json")
glider.save("glider.obj", midribs=2)
```

**Priorität:** Hoch

---

### 6.2 Format-Registry-Pattern

**Problem:**
- Export-Funktionen sind in verschiedenen Modulen verstreut
- Schwer zu erweitern

**Vorschlag:**
```python
class FormatRegistry:
    _importers = {}
    _exporters = {}
    
    @classmethod
    def register_importer(cls, format: str, func: Callable):
        cls._importers[format] = func
    
    @classmethod
    def register_exporter(cls, format: str, func: Callable):
        cls._exporters[format] = func
    
    @classmethod
    def get_importer(cls, format: str) -> Callable:
        if format not in cls._importers:
            raise ValueError(f"No importer for format: {format}")
        return cls._importers[format]
    
    @classmethod
    def get_exporter(cls, format: str) -> Callable:
        if format not in cls._exporters:
            raise ValueError(f"No exporter for format: {format}")
        return cls._exporters[format]

# Registration:
FormatRegistry.register_exporter("obj", export_obj)
FormatRegistry.register_exporter("dxf", export_dxf)
```

**Priorität:** Mittel

---

## 7. Getter/Setter-Patterns

### 7.1 Properties statt direkter Attribute

**Problem:**
- Einige Attribute sollten validiert werden beim Setzen
- Keine Möglichkeit, Side-Effects zu triggern

**Vorschlag:**
```python
class Rib:
    def __init__(self, ...):
        self._chord = chord
        self._profile_2d = profile_2d
    
    @property
    def chord(self) -> float:
        return self._chord
    
    @chord.setter
    def chord(self, value: float) -> None:
        if value <= 0:
            raise ValueError(f"Chord must be positive, got {value}")
        self._chord = value
        # Invalidate cached properties
        self._invalidate_cache()
    
    @property
    def profile_2d(self) -> Profile2D:
        return self._profile_2d
    
    @profile_2d.setter
    def profile_2d(self, value: Profile2D) -> None:
        if value is None:
            raise ValueError("profile_2d cannot be None")
        self._profile_2d = value
        self._invalidate_cache()
```

**Priorität:** Mittel

---

### 7.2 Lazy Loading für teure Berechnungen

**Problem:**
- `profile_3d` wird bei jedem Zugriff neu berechnet (trotz `@cached_property`)
- Könnte expliziter gemacht werden

**Vorschlag:**
```python
class Rib:
    def __init__(self, ...):
        self._profile_3d = None
        self._profile_3d_dirty = True
    
    @property
    def profile_3d(self) -> Profile3D:
        if self._profile_3d is None or self._profile_3d_dirty:
            self._profile_3d = self._compute_profile_3d()
            self._profile_3d_dirty = False
        return self._profile_3d
    
    def invalidate_profile_3d(self) -> None:
        """Mark profile_3d as dirty, will be recomputed on next access."""
        self._profile_3d_dirty = True
```

**Priorität:** Niedrig

---

## 8. Konstruktoren & Factory-Methoden

### 8.1 Factory-Methoden für häufige Fälle

**Problem:**
- Komplexe Konstruktoren mit vielen Parametern
- Schwer, Standard-Gleitschirme zu erstellen

**Vorschlag:**
```python
class Glider:
    @classmethod
    def create_simple(
        cls,
        num_cells: int,
        span: float,
        area: float,
        profile: Profile2D
    ) -> 'Glider':
        """Create a simple rectangular glider.
        
        Args:
            num_cells: Number of cells
            span: Total span in meters
            area: Total area in m²
            profile: Airfoil profile to use
        """
        # Implementation
        pass
    
    @classmethod
    def create_from_shape(
        cls,
        shape: ParametricShape,
        arc: Arc,
        profile: Profile2D
    ) -> 'Glider':
        """Create glider from parametric shape."""
        # Implementation
        pass
```

**Priorität:** Niedrig

---

### 8.2 Named Constructors

**Problem:**
- Verschiedene Wege, Objekte zu erstellen (import, konstruktor, etc.)

**Vorschlag:**
```python
class Profile2D:
    @classmethod
    def from_dat(cls, path: str) -> 'Profile2D':
        """Create profile from .dat file."""
        return cls.import_from_dat(path)
    
    @classmethod
    def from_naca(cls, naca: int, numpoints: int = 100) -> 'Profile2D':
        """Create NACA profile."""
        return cls.compute_naca(naca, numpoints)
    
    @classmethod
    def from_url(cls, name: str, url: str = ...) -> 'Profile2D':
        """Create profile from URL."""
        return cls.from_url(name, url)
```

**Priorität:** Niedrig

---

## 9. Weitere Verbesserungen

### 9.1 Deprecation Warnings

**Problem:**
- Alte Methoden werden nicht als deprecated markiert
- Keine Migrationspfade

**Vorschlag:**
```python
import warnings

def return_ribs(self, num: int = 0, ballooning: bool = True):
    """Get list of rib curves.
    
    .. deprecated:: 0.9.0
        Use :meth:`get_ribs` instead.
    """
    warnings.warn(
        "return_ribs() is deprecated, use get_ribs() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return self.get_ribs(num, ballooning)
```

**Priorität:** Mittel

---

### 9.2 Einheitliche Einheiten

**Problem:**
- Inkonsistente Einheiten (manchmal mm, manchmal m)
- Keine explizite Dokumentation

**Vorschlag:**
```python
class Units:
    """Constants for unit conversion."""
    MM_TO_M = 0.001
    M_TO_MM = 1000.0
    DEG_TO_RAD = math.pi / 180.0
    RAD_TO_DEG = 180.0 / math.pi

class Glider:
    def scale(self, factor: float, unit: str = "m") -> 'Glider':
        """Scale glider.
        
        Args:
            factor: Scale factor
            unit: Unit of measurement ('m' for meters, 'mm' for millimeters)
        """
        if unit == "mm":
            factor *= Units.MM_TO_M
        # ...
```

**Priorität:** Niedrig

---

### 9.3 Logging statt print

**Problem:**
- `print()` Statements in Code
- Keine Möglichkeit, Log-Level zu kontrollieren

**Vorschlag:**
```python
import logging

logger = logging.getLogger(__name__)

def load(filename: str):
    logger.info(f"Loading glider from {filename}")
    try:
        # ...
        logger.debug(f"Successfully loaded {type(res).__name__}")
        return res
    except Exception as e:
        logger.error(f"Failed to load {filename}: {e}", exc_info=True)
        raise
```

**Priorität:** Niedrig

---

## Priorisierte Roadmap

### Phase 1 (Kritisch - Sofort)
1. ✅ Fehlerbehandlung in `load()` und `save()`
2. ✅ Validierung in Konstruktoren
3. ✅ Einheitliche Export-API (`export_3d()` verbessern)
4. ✅ Konsistente Methodennamen (`return_ribs()` → `get_ribs()`)

### Phase 2 (Wichtig - Kurzfristig)
5. ✅ Type Hints hinzufügen
6. ✅ Docstrings vervollständigen
7. ✅ Einheitliche Parameter-Namen (englisch)
8. ✅ Format-Registry-Pattern

### Phase 3 (Verbesserungen - Mittelfristig)
9. ✅ Properties mit Validierung
10. ✅ Factory-Methoden
11. ✅ Iterator-Patterns
12. ✅ Deprecation Warnings

### Phase 4 (Nice-to-have - Langfristig)
13. ✅ Builder-Pattern
14. ✅ Context Manager
15. ✅ Einheitliche Einheiten-API
16. ✅ Logging-System

---

## Zusammenfassung

Die wichtigsten Verbesserungen sind:

1. **Konsistenz**: Einheitliche Namenskonventionen (englisch, get_/set_/export_)
2. **Robustheit**: Fehlerbehandlung und Validierung
3. **Klarheit**: Type Hints und Docstrings
4. **Erweiterbarkeit**: Format-Registry, Factory-Methoden

Diese Verbesserungen würden die API deutlich benutzerfreundlicher und wartbarer machen.

---

*Erstellt am: 2024*
*OpenGlider Version: 0.8.1*

