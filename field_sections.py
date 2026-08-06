"""
Field sectioning — pure geometry for zone-level analysis.

Splits a field polygon into a grid of sections (default 2×2 → four zones with
farmer-friendly compass names) so satellite analysis can be sampled PER ZONE.
"Your field is stressed" becomes "the North-East zone is stressed" — the
farmer knows where to walk.

Pure module: no DB, no network, no FastAPI — fully unit-testable. The polygon
shape matches storage: list of {"lat": float, "lon": float}, open ring.
"""

from typing import Dict, List, Optional


Point = Dict[str, float]  # {"lat": ..., "lon": ...}

# 2×2 grid labels, row 0 = NORTH (max lat). Anything larger falls back to
# "Zone R{row+1}C{col+1}" labels.
_COMPASS_2X2 = {
    (0, 0): "North-West",
    (0, 1): "North-East",
    (1, 0): "South-West",
    (1, 1): "South-East",
}


def _clip_halfplane(ring: List[Point], key: str, bound: float, keep_below: bool) -> List[Point]:
    """Sutherland–Hodgman clip of a ring against one axis-aligned bound.

    ``keep_below`` keeps points with ``p[key] <= bound``; otherwise ``>=``.
    """
    if not ring:
        return []

    def inside(p: Point) -> bool:
        return p[key] <= bound if keep_below else p[key] >= bound

    def intersect(a: Point, b: Point) -> Point:
        # Parametric intersection with the line key == bound.
        da = b[key] - a[key]
        t = 0.0 if da == 0 else (bound - a[key]) / da
        other = "lon" if key == "lat" else "lat"
        return {
            key: bound,
            other: a[other] + t * (b[other] - a[other]),
        }

    out: List[Point] = []
    for i in range(len(ring)):
        cur = ring[i]
        prev = ring[i - 1]
        cur_in, prev_in = inside(cur), inside(prev)
        if cur_in:
            if not prev_in:
                out.append(intersect(prev, cur))
            out.append(cur)
        elif prev_in:
            out.append(intersect(prev, cur))
    return out


def clip_to_rect(ring: List[Point], lat_min: float, lat_max: float,
                 lon_min: float, lon_max: float) -> List[Point]:
    """Clip an open polygon ring to an axis-aligned lat/lon rectangle."""
    r = _clip_halfplane(ring, "lat", lat_max, keep_below=True)
    r = _clip_halfplane(r, "lat", lat_min, keep_below=False)
    r = _clip_halfplane(r, "lon", lon_max, keep_below=True)
    r = _clip_halfplane(r, "lon", lon_min, keep_below=False)
    return r


def ring_area(ring: List[Point]) -> float:
    """Shoelace area in squared degrees (relative comparisons only)."""
    n = len(ring)
    if n < 3:
        return 0.0
    total = 0.0
    for i in range(n):
        a, b = ring[i], ring[(i + 1) % n]
        total += a["lon"] * b["lat"] - b["lon"] * a["lat"]
    return abs(total) / 2.0


def ring_centroid(ring: List[Point]) -> Optional[Point]:
    """Area-weighted centroid; falls back to vertex mean for degenerate rings."""
    n = len(ring)
    if n == 0:
        return None
    a2 = 0.0
    cx = cy = 0.0
    for i in range(n):
        p, q = ring[i], ring[(i + 1) % n]
        cross = p["lon"] * q["lat"] - q["lon"] * p["lat"]
        a2 += cross
        cx += (p["lon"] + q["lon"]) * cross
        cy += (p["lat"] + q["lat"]) * cross
    if abs(a2) < 1e-12:
        return {
            "lat": sum(p["lat"] for p in ring) / n,
            "lon": sum(p["lon"] for p in ring) / n,
        }
    return {"lon": cx / (3 * a2), "lat": cy / (3 * a2)}


def _band(index: int, grid: int, axis: str) -> str:
    """Which third of the field this row/column falls in, as a compass word.

    Thirds rather than halves so a 3x3 grid gets a genuine middle ("North",
    "Centre", "South") instead of being forced into a North/South binary that
    puts the middle of the field on one side of a line it isn't on.
    """
    if grid <= 1:
        return ""
    # Evaluate the cell's CENTRE, not its leading edge. Using the edge makes the
    # bands lopsided on even grids (a 4-wide field would put two columns in
    # "West" and one in "East"), so a farmer looking for the north-west corner
    # would find it two columns wide on one side and one on the other.
    third = (index + 0.5) / grid
    if axis == "lat":                      # row 0 is the northern-most
        if third < 1 / 3:
            return "North"
        if third >= 2 / 3:
            return "South"
        return ""                          # middle band carries no lat word
    if third < 1 / 3:
        return "West"
    if third >= 2 / 3:
        return "East"
    return ""


def section_label(row: int, col: int, grid: int) -> str:
    """A farmer-readable zone name: directional, with a number when needed.

    Zones are named automatically rather than left to the farmer. Asking
    someone to name nine parts of every field before the feature does anything
    is work for no immediate return, and unnamed-by-default is what makes the
    zone view usable on a large farm from the first tap.

    * 2x2  -> "North-West", "North-East", "South-West", "South-East"
    * 3x3  -> the eight compass points plus "Centre"
    * 4x4+ -> compass sector plus an ordinal, e.g. "North-East 2", so a farm
      with dozens of zones still gets names that point somewhere rather than
      "Zone R2C3", which tells a farmer nothing about where to walk.
    """
    if grid == 2:
        return _COMPASS_2X2[(row, col)]

    lat_word = _band(row, grid, "lat")
    lon_word = _band(col, grid, "lon")

    if lat_word and lon_word:
        sector = f"{lat_word}-{lon_word}"
    elif lat_word or lon_word:
        sector = lat_word or lon_word
    else:
        sector = "Centre"

    if grid <= 3:
        return sector

    # Beyond 3x3 a sector holds several cells, so number them within the
    # sector — reading order (north to south, west to east) matches how the
    # zone list is presented.
    ordinal = 1
    for r in range(grid):
        for c in range(grid):
            if r == row and c == col:
                return f"{sector} {ordinal}"
            r_lat, r_lon = _band(r, grid, "lat"), _band(c, grid, "lon")
            r_sector = (
                f"{r_lat}-{r_lon}" if (r_lat and r_lon) else (r_lat or r_lon or "Centre")
            )
            if r_sector == sector:
                ordinal += 1
    return sector


# Roughly the largest a zone can be and still be one walk. Beyond this, "the
# North-East is stressed" stops narrowing anything down.
WALKABLE_ZONE_HA = 5.0


def suggest_grid_size(area_hectares: Optional[float], max_grid: int = 4) -> int:
    """Grid size that keeps zones roughly walkable for a field of this size.

    A fixed 2x2 splits a 2 ha plot into sensible quarters and a 400 ha block
    into four 100 ha slabs — the second is not guidance, it is a shrug. Scaling
    with area keeps "walk the North-East" a real instruction on both.

    Capped, because past a point the farmer is reading a heat map rather than a
    list of places to go.
    """
    if not area_hectares or area_hectares <= 0:
        return 2
    grid = 2
    while grid < max_grid and (area_hectares / (grid * grid)) > WALKABLE_ZONE_HA:
        grid += 1
    return grid


def compute_sections(polygon: List[Point], grid: int = 2) -> List[dict]:
    """Split a field polygon into up to grid×grid clipped sections.

    Returns sections ordered north→south, west→east, each:
    ``{"index", "label", "polygon", "centroid", "area_share"}``.
    Cells whose clipped area is under 2% of the field are dropped (slivers from
    irregular boundaries — not walkable zones). Degenerate inputs (<3 points)
    return [].
    """
    pts = [p for p in (polygon or [])
           if isinstance(p, dict) and "lat" in p and "lon" in p]
    if len(pts) < 3 or grid < 1:
        return []

    lat_min = min(p["lat"] for p in pts)
    lat_max = max(p["lat"] for p in pts)
    lon_min = min(p["lon"] for p in pts)
    lon_max = max(p["lon"] for p in pts)
    if lat_max - lat_min <= 0 or lon_max - lon_min <= 0:
        return []

    total_area = ring_area(pts)
    if total_area <= 0:
        return []

    lat_step = (lat_max - lat_min) / grid
    lon_step = (lon_max - lon_min) / grid

    sections: List[dict] = []
    index = 0
    # Row 0 is the NORTH band (max lat side) so compass labels read naturally.
    for row in range(grid):
        cell_lat_max = lat_max - row * lat_step
        cell_lat_min = cell_lat_max - lat_step
        for col in range(grid):
            cell_lon_min = lon_min + col * lon_step
            cell_lon_max = cell_lon_min + lon_step
            clipped = clip_to_rect(pts, cell_lat_min, cell_lat_max,
                                   cell_lon_min, cell_lon_max)
            area = ring_area(clipped)
            share = area / total_area if total_area else 0.0
            if len(clipped) < 3 or share < 0.02:
                continue
            centroid = ring_centroid(clipped)
            sections.append({
                "index": index,
                "label": section_label(row, col, grid),
                "polygon": clipped,
                "centroid": centroid,
                "area_share": round(share, 4),
            })
            index += 1
    return sections
