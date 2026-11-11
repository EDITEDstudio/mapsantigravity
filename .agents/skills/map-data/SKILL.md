---
name: map-data
description: Prepare real country and Thai province boundaries and terrain for map videos. Use for geographic data, sources, province lookup, or factual map preparation.
---

# Real map data
Run project .venv/bin/python scripts/map_video.py fetch.
Read data/sources.json and data/processed/thailand_provinces.geojson.
Use EPSG:4326 lon/lat. Keep raster and vector in the same projection; never mix Web Mercator tile pixels with degree coordinates.
Use real geometry, not generated images. Natural Earth is generalized cartography; verify current Thai administrative names and factual counts against authoritative Thai sources before publishing.
Record every source URL, retrieval date, license, hash and corrections. Do not present basemap imagery as current satellite observation.
Identify provinces by iso_3166_2 or verified name/name_th. Inspect properties; never invent a province ID.
For route distances use geodesic distance rather than Euclidean screen distance.
For close street-level or 3D satellite shots choose an explicitly licensed imagery source or Google Earth Studio; preserve required attribution.
