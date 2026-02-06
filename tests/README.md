# OpenGlider Tests

Tests laufen mit **pytest**. Abhängigkeiten inkl. pytest: `pip install -e ".[test]"` oder pixi-Environment nutzen.

## Schnellstart

| Ziel | Befehl |
|------|--------|
| Nur Unit-Tests (ohne Visual/GUI) | `pytest tests/ -m "not visual"` |
| Alle Tests inkl. Visual | `pytest tests/` |
| Mit pixi (nur Unit) | `pixi run test` |
| Mit pixi (alle) | `pixi run test-all` |
| Wrapper-Skript (Unit) | `./testall.py` |
| Wrapper-Skript (alle) | `./testall.py -a` |

## Testarten

- **Unit-Tests** (`test_*.py`): Keine GUI, keine VTK/Display – für CI und lokale Schnellläufe. Werden standardmäßig gesammelt.
- **Visual-Tests** (`visual_test_*.py`): Nutzen Graphics/VTK oder Fenster; können in headless-Umgebungen hängen oder fehlschlagen. Sind mit dem Marker `visual` markiert und standardmäßig **nicht** dabei.

## Marker

- `visual` – Visual/GUI-Test (exkludiert mit `-m "not visual"`, nur diese mit `-m visual`).

Konfiguration: `pyproject.toml` → `[tool.pytest.ini_options]`, Marker-Registrierung in `tests/conftest.py`.

## Nützliche Befehle

```bash
# Einzelne Datei
pytest tests/test_glider.py -v

# Nur Tests, deren Name einen Begriff enthalten
pytest tests/ -k "glider" -v

# Tests N-mal wiederholen (z. B. Flaky finden)
pytest tests/ -m "not visual" --count=3

# Mit testall.py: Pattern übergeben
./testall.py -p "glider"
./testall.py -n 2
```

## Verzeichnisstruktur

- `conftest.py` – Pytest-Konfiguration (Pfad, Marker, automatische `visual`-Markierung für `visual_test_*.py`).
- `common/` – Gemeinsame Testdaten (z. B. `demokite.json`, `glider2d.json`) und ggf. Hilfsmodule.
- `test_*.py` – Unit-Tests (immer gesammelt, sofern nicht per `-m` gefiltert).
- `visual_test_*.py` – Visual-Tests (nur bei expliziter Auswahl oder bei `pytest tests/` ohne `-m "not visual"`).

## Abgedeckte Module (Auswahl)

| Testdatei | Modul / Thema |
|-----------|----------------|
| `test_interpolate.py` | `vector.Interpolation` (stückweise linear) |
| `test_polygon.py` | `vector.polygon` (Polygon2D, Circle, Ellipse) |
| `test_utils_extended.py` | `utils.cache` (HashedList, hash_*), `utils.colors` (colorwheel, HeatMap) |
| `test_plane.py` | `vector.plane.Plane` (point, projection, normvector) |
| `test_transformation.py` | `vector.transformation` (Transformation, Rotation, Reflection, Scale, Translation) |
| `test_vector.py` / `test_vector_extended.py` | `vector.functions`, `vector.polyline` |
| `test_bezier.py` | `vector.spline.Bezier` |
| `test_glider*.py` | `glider`, `glider.parametric`, Export/Import |
| `test_mesh.py` | `mesh` |
| `test_lines.py` | `lines.import_text`, `lines.LineSet` |
| `test_ballooning.py` | `glider.ballooning` |
| `test_profile.py` | `airfoil.Profile2D` |
| `test_distribution*.py` | `utils.distribution` |
| `test_patterns.py` | `plots` |
| `test_rib.py` | `glider.rib` |
| weitere `test_*.py` | shape, main module, exports, … |

## Hinweise

- Visual-Tests können blockieren, wenn kein Display/VTK verfügbar ist. Für CI und „schnell durchlaufen“ immer `-m "not visual"` oder `pixi run test` verwenden.
- `testall.py` leitet an pytest weiter und unterstützt `-a` (alle Tests), `-n N` (N Läufe), `-p <pattern>` (Testname-Filter).
