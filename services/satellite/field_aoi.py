"""
Convert KurimaSense field rows into Sentinel Hub-shaped AOI dicts.

Public entry point:
    get_field_aoi(field_id) -> {
        "type": "Polygon",
        "coordinates": [[[lon, lat], ...]],
        "bbox": [minLon, minLat, maxLon, maxLat],
        "area_ha": float,
    }

Resolution order:
1. Cache hit: row in `field_aoi_cache` younger than CACHE_TTL_DAYS.
2. Build from `fields.polygon_coordinates`:
   - 3+ vertices → polygon (ring closed if needed)
   - 1-2 vertices → circular buffer with radius derived from `size_hectares`
3. Compute bbox + area, write back to cache, return.

All coordinates are WGS84 / EPSG:4326. Buffering and area calculations use a
local Azimuthal Equidistant projection centered on the field's centroid so
metres-based operations are accurate at field scale.
"""
from __future__ import annotations

import json
import logging
import math
from typing import Any, Dict, List, Optional, Tuple

from pyproj import CRS, Transformer
from shapely.geometry import Point, Polygon, mapping
from shapely.ops import transform as shp_transform

from database import get_db_connection

logger = logging.getLogger(__name__)

CACHE_TTL_DAYS = 30
WGS84 = CRS.from_epsg(4326)


class FieldNotFoundError(Exception):
    """Raised when the requested field has no row or no usable geometry data."""


# --------------------------------------------------------------------------- #
# Coordinate normalisation
# --------------------------------------------------------------------------- #

def _normalize_coords(raw: Any) -> List[Tuple[float, float]]:
    """
    Accept the various shapes polygon_coordinates may take and return
    a list of (lon, lat) tuples.

    Supported inputs:
      - [{"lat": .., "lon": ..}, ...]
      - [{"lat": .., "lng": ..}, ...]
      - [[lon, lat], ...]
    """
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return []
    if not isinstance(raw, list):
        return []

    out: List[Tuple[float, float]] = []
    for item in raw:
        if isinstance(item, dict):
            lat = item.get("lat")
            lon = item.get("lon")
            if lon is None:
                lon = item.get("lng")
            if lat is None or lon is None:
                continue
            out.append((float(lon), float(lat)))
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            out.append((float(item[0]), float(item[1])))
    return out


# --------------------------------------------------------------------------- #
# Geometry construction
# --------------------------------------------------------------------------- #

def _local_aeqd(lon: float, lat: float) -> CRS:
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"
    )


def _to_local(polygon: Polygon, center_lon: float, center_lat: float) -> Polygon:
    aeqd = _local_aeqd(center_lon, center_lat)
    fwd = Transformer.from_crs(WGS84, aeqd, always_xy=True).transform
    return shp_transform(fwd, polygon)


def _from_local(polygon: Polygon, center_lon: float, center_lat: float) -> Polygon:
    aeqd = _local_aeqd(center_lon, center_lat)
    inv = Transformer.from_crs(aeqd, WGS84, always_xy=True).transform
    return shp_transform(inv, polygon)


def _build_polygon_from_vertices(coords: List[Tuple[float, float]]) -> Polygon:
    """Build a closed polygon ring from 3+ (lon, lat) vertices."""
    if len(coords) < 3:
        raise ValueError("Need at least 3 coordinates to build a polygon")
    if coords[0] != coords[-1]:
        coords = coords + [coords[0]]
    return Polygon(coords)


def _build_circular_aoi(
    center_lon: float, center_lat: float, area_ha: float
) -> Polygon:
    """
    Build a circle of the requested area, centered at (center_lon, center_lat),
    by buffering in a local AEQD projection and reprojecting to WGS84.

    radius_m = sqrt(area_ha * 10000 / pi)
    """
    if area_ha is None or area_ha <= 0:
        raise ValueError("area_ha must be > 0 to build a circular AOI")
    radius_m = math.sqrt(area_ha * 10_000.0 / math.pi)
    local_circle = Point(0.0, 0.0).buffer(radius_m, quad_segs=32)
    return _from_local(local_circle, center_lon, center_lat)


def _centroid_of_points(coords: List[Tuple[float, float]]) -> Tuple[float, float]:
    lons = [c[0] for c in coords]
    lats = [c[1] for c in coords]
    return (sum(lons) / len(lons), sum(lats) / len(lats))


# --------------------------------------------------------------------------- #
# AOI dict assembly
# --------------------------------------------------------------------------- #

def _polygon_to_aoi_dict(polygon: Polygon) -> Dict[str, Any]:
    """
    Convert a WGS84 polygon to the Sentinel Hub-shaped AOI dict, computing
    bbox and area_ha (area projected to local AEQD for metres accuracy).
    """
    geom = mapping(polygon)
    # Force a single Polygon shape; shapely may yield MultiPolygon for self-touching.
    if geom["type"] != "Polygon":
        raise ValueError(f"Expected Polygon, got {geom['type']}")

    coordinates = [[list(pt) for pt in ring] for ring in geom["coordinates"]]

    minx, miny, maxx, maxy = polygon.bounds
    center_lon = (minx + maxx) / 2
    center_lat = (miny + maxy) / 2
    local = _to_local(polygon, center_lon, center_lat)
    area_ha = local.area / 10_000.0

    return {
        "type": "Polygon",
        "coordinates": coordinates,
        "bbox": [minx, miny, maxx, maxy],
        "area_ha": area_ha,
    }


def _build_aoi_from_field(
    coords: List[Tuple[float, float]], size_hectares: Optional[float]
) -> Dict[str, Any]:
    if len(coords) >= 3:
        polygon = _build_polygon_from_vertices(coords)
    elif len(coords) >= 1:
        center_lon, center_lat = _centroid_of_points(coords)
        if size_hectares is None or size_hectares <= 0:
            raise ValueError(
                "Field has fewer than 3 coordinates and no size_hectares; "
                "cannot derive a circular AOI"
            )
        polygon = _build_circular_aoi(center_lon, center_lat, float(size_hectares))
    else:
        raise FieldNotFoundError("Field has no usable polygon_coordinates")
    return _polygon_to_aoi_dict(polygon)


# --------------------------------------------------------------------------- #
# Cache I/O
# --------------------------------------------------------------------------- #

def _read_cache(cursor, field_id: str) -> Optional[Dict[str, Any]]:
    cursor.execute(
        """
        SELECT field_id, bbox, geometry, area_ha, last_updated,
               (NOW() - last_updated) < (%s::int * INTERVAL '1 day') AS is_fresh
        FROM field_aoi_cache
        WHERE field_id = %s::uuid
        """,
        (CACHE_TTL_DAYS, field_id),
    )
    row = cursor.fetchone()
    if not row:
        return None
    if not row.get("is_fresh"):
        return None

    bbox = _maybe_parse_json(row["bbox"])
    geometry = _maybe_parse_json(row["geometry"]) if row.get("geometry") else None
    if not geometry or not bbox:
        return None
    return {
        "type": geometry.get("type", "Polygon"),
        "coordinates": geometry.get("coordinates", []),
        "bbox": bbox,
        "area_ha": float(row["area_ha"]) if row.get("area_ha") is not None else 0.0,
    }


def _write_cache(cursor, field_id: str, aoi: Dict[str, Any]) -> None:
    geometry_json = json.dumps({"type": aoi["type"], "coordinates": aoi["coordinates"]})
    bbox_json = json.dumps(aoi["bbox"])
    cursor.execute(
        """
        INSERT INTO field_aoi_cache (field_id, bbox, geometry, area_ha, last_updated)
        VALUES (%s::uuid, %s::jsonb, %s::jsonb, %s, NOW())
        ON CONFLICT (field_id) DO UPDATE SET
            bbox = EXCLUDED.bbox,
            geometry = EXCLUDED.geometry,
            area_ha = EXCLUDED.area_ha,
            last_updated = NOW()
        """,
        (field_id, bbox_json, geometry_json, aoi["area_ha"]),
    )


def _maybe_parse_json(value: Any) -> Any:
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    return value


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #

def get_field_aoi(field_id: str) -> Dict[str, Any]:
    """
    Resolve the AOI for a field, using the field_aoi_cache when fresh.

    Returns a dict with keys: type, coordinates, bbox, area_ha.
    """
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError("Database unavailable — cannot resolve field AOI")

    try:
        from psycopg2.extras import RealDictCursor

        cursor = conn.cursor(cursor_factory=RealDictCursor)

        cached = _read_cache(cursor, field_id)
        if cached is not None:
            logger.info("field_aoi.cache_hit field_id=%s", field_id)
            cursor.close()
            return cached

        cursor.execute(
            """
            SELECT polygon_coordinates, size_hectares
            FROM fields
            WHERE id = %s::uuid
            """,
            (field_id,),
        )
        row = cursor.fetchone()
        if not row:
            cursor.close()
            raise FieldNotFoundError(f"No fields row for id={field_id}")

        coords = _normalize_coords(row.get("polygon_coordinates"))
        size_hectares = row.get("size_hectares")
        if size_hectares is not None:
            size_hectares = float(size_hectares)

        aoi = _build_aoi_from_field(coords, size_hectares)
        _write_cache(cursor, field_id, aoi)
        conn.commit()
        cursor.close()
        logger.info(
            "field_aoi.cache_miss field_id=%s vertices=%d area_ha=%.3f",
            field_id,
            len(coords),
            aoi["area_ha"],
        )
        return aoi
    finally:
        conn.close()
