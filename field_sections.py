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


def section_label(row: int, col: int, grid: int) -> str:
    if grid == 2:
        return _COMPASS_2X2[(row, col)]
    return f"Zone R{row + 1}C{col + 1}"


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
