# OpenGlider Documentation

Vollständige Sphinx-Dokumentation für OpenGlider (Installation, Konzepte, API, FreeCAD-Workbench).

## Build (lokal)

Voraussetzung: Sphinx installiert (z. B. in einem virtuellen Environment):

```bash
# Im Projektroot
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e . sphinx

# Dokumentation bauen
cd docs
make html
```

Die HTML-Seiten liegen danach in `docs/build/html/` (Start: `index.html`).

## Optional: API-Dateien neu erzeugen

Die API-Referenz verwendet vordefinierte Modul-Seiten. Zum kompletten Neugenerieren aus dem Quellcode:

```bash
cd docs
make apidoc   # überschreibt source/api/*.rst
make html
```

## Inhalt

- **Installation** – pip, pixi, conda, manuell
- **Getting Started** – Schnellstart, Laden/Speichern, Tests
- **Concepts** – Glider-Hierarchie, Koordinaten, Ballooning, LineSet, Mesh
- **FreeCAD Workbench** – GUI in FreeCAD, Installation, Tools
- **Project Structure** – Überblick über die Pakete
- **Developer** – Beitragen, Code-Konventionen, Tests, Doku bauen
- **API Reference** – Aus dem Paket `openglider` generierte API-Dokumentation
