"""
Season persistence.

Read/write access to the ``seasons`` table plus the ``fields`` mirror that keeps
every pre-existing endpoint working. RLS GUCs are armed on each connection
(FORCE-ready), matching ``services/soil_intelligence/repository.py``.

The mirror
----------
``fields.crop_type`` / ``variety`` / ``planting_date`` / ``transplant_date`` are
maintained as a **read-through cache of the active season**. Nothing new should
read them — new code reads ``seasons`` — but dozens of existing queries do, so
they are kept exactly in step. Dropping them is a later cleanup.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from psycopg2.extras import RealDictCursor

from database import get_db_connection

# Every column, in a stable order, for SELECT and serialisation.
SEASON_COLS = """
    id::text AS id, field_id::text AS field_id, tenant_id::text AS tenant_id,
    user_id::text AS user_id, status, season_label, crop_type, variety,
    planned_planting_date, planting_date, transplant_date,
    expected_harvest_date, harvest_date,
    row_spacing_cm, in_row_spacing_cm, target_population_per_ha,
    seed_rate_kg_ha, planting_depth_cm, emergence_date,
    established_population_per_ha, emergence_uniformity,
    previous_crop, tillage_practice, residue_management,
    yield_tonnes_per_ha, notes, created_at, updated_at
"""

# Columns a caller may set directly. Status is excluded on purpose: it moves
# only through the lifecycle transitions in service.py, never by direct PATCH.
WRITABLE_FIELDS = (
    "season_label", "crop_type", "variety",
    "planned_planting_date", "planting_date", "transplant_date",
    "expected_harvest_date", "harvest_date",
    "row_spacing_cm", "in_row_spacing_cm", "target_population_per_ha",
    "seed_rate_kg_ha", "planting_depth_cm", "emergence_date",
    "established_population_per_ha", "emergence_uniformity",
    "previous_crop", "tillage_practice", "residue_management",
    "yield_tonnes_per_ha", "notes",
)


def _arm(conn, user_id: Optional[str], tenant_ids: Optional[List[str]]) -> None:
    if not user_id:
        return
    try:
        from tenancy import arm_rls_gucs, caller_tenant_ids
        tids = tenant_ids if tenant_ids is not None else caller_tenant_ids(user_id)
        arm_rls_gucs(conn, user_id, [str(t) for t in (tids or [])])
    except Exception as e:
        print(f"[seasons.repository] GUC arm failed (continuing): {e}")


def _serialise(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Dates → ISO strings, Decimals → floats, so the row is JSON-ready."""
    if row is None:
        return None
    out: Dict[str, Any] = {}
    for k, v in row.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif hasattr(v, "quantize"):        # Decimal
            out[k] = float(v)
        else:
            out[k] = v
    return out


def list_seasons(
    field_id: str,
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """All seasons for a field, newest first. Empty list on any failure."""
    conn = get_db_connection()
    if not conn:
        return []
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            SELECT {SEASON_COLS} FROM seasons
            WHERE field_id = %s::uuid
            ORDER BY COALESCE(planting_date, planned_planting_date, created_at::date) DESC,
                     created_at DESC
            """,
            (field_id,),
        )
        rows = cur.fetchall()
        cur.close()
        return [_serialise(dict(r)) for r in rows]
    except Exception as e:
        print(f"[seasons.repository] list_seasons failed: {e}")
        return []
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_season(
    season_id: str,
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(f"SELECT {SEASON_COLS} FROM seasons WHERE id = %s::uuid", (season_id,))
        row = cur.fetchone()
        cur.close()
        return _serialise(dict(row)) if row else None
    except Exception as e:
        print(f"[seasons.repository] get_season failed: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def get_active_season(
    field_id: str,
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    if not conn:
        return None
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"SELECT {SEASON_COLS} FROM seasons WHERE field_id = %s::uuid AND status = 'active'",
            (field_id,),
        )
        row = cur.fetchone()
        cur.close()
        return _serialise(dict(row)) if row else None
    except Exception as e:
        print(f"[seasons.repository] get_active_season failed: {e}")
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def create_season(
    field_id: str,
    tenant_id: Optional[str],
    user_id: str,
    payload: Dict[str, Any],
    status: str = "planned",
    tenant_ids: Optional[List[str]] = None,
) -> Optional[Dict[str, Any]]:
    """Insert a season. Returns the created row, or None on failure."""
    cols = ["field_id", "tenant_id", "user_id", "status"]
    vals: List[Any] = [field_id, tenant_id, user_id, status]
    placeholders = ["%s::uuid", "%s::uuid", "%s", "%s"]

    for key in WRITABLE_FIELDS:
        if key in payload and payload[key] is not None:
            cols.append(key)
            vals.append(payload[key])
            placeholders.append("%s")

    conn = get_db_connection()
    if not conn:
        return None
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"""
            INSERT INTO seasons ({", ".join(cols)})
            VALUES ({", ".join(placeholders)})
            RETURNING {SEASON_COLS}
            """,
            tuple(vals),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return _serialise(dict(row)) if row else None
    except Exception as e:
        print(f"[seasons.repository] create_season failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def update_season(
    season_id: str,
    payload: Dict[str, Any],
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
    status: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Patch a season. ``status`` is only ever passed by the lifecycle service."""
    sets: List[str] = []
    vals: List[Any] = []
    for key in WRITABLE_FIELDS:
        if key in payload:
            sets.append(f"{key} = %s")
            vals.append(payload[key])
    if status is not None:
        sets.append("status = %s")
        vals.append(status)
    if not sets:
        return get_season(season_id, user_id, tenant_ids)

    sets.append("updated_at = NOW()")
    vals.append(season_id)

    conn = get_db_connection()
    if not conn:
        return None
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            f"UPDATE seasons SET {', '.join(sets)} WHERE id = %s::uuid RETURNING {SEASON_COLS}",
            tuple(vals),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        return _serialise(dict(row)) if row else None
    except Exception as e:
        print(f"[seasons.repository] update_season failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return None
    finally:
        try:
            conn.close()
        except Exception:
            pass


def mirror_to_field(
    field_id: str,
    season: Dict[str, Any],
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> bool:
    """Copy the active season's crop columns onto ``fields``.

    This is what lets the season entity land without touching the dozens of
    existing queries that still read ``fields.crop_type`` and friends.
    """
    conn = get_db_connection()
    if not conn:
        return False
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE fields
            SET crop_type = %s, variety = %s,
                planting_date = %s, transplant_date = %s
            WHERE id = %s::uuid
            """,
            (
                season.get("crop_type"),
                season.get("variety"),
                season.get("planting_date"),
                season.get("transplant_date"),
                field_id,
            ),
        )
        conn.commit()
        cur.close()
        return True
    except Exception as e:
        print(f"[seasons.repository] mirror_to_field failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return False
    finally:
        try:
            conn.close()
        except Exception:
            pass


def attribute_observations(
    field_id: str,
    season_id: str,
    from_date: str,
    user_id: Optional[str] = None,
    tenant_ids: Optional[List[str]] = None,
) -> int:
    """Attach ``season_id`` to this field's observations from ``from_date`` on.

    Run when a season goes active so satellite history, inputs and activities
    land against the right season from the moment it starts.
    """
    conn = get_db_connection()
    if not conn:
        return 0
    updated = 0
    try:
        _arm(conn, user_id, tenant_ids)
        cur = conn.cursor()
        for table, date_col in (
            ("daily_logs", "log_date"),
            ("field_inputs", "input_date"),
            ("field_activities", "visit_date"),
        ):
            try:
                cur.execute(
                    f"""
                    UPDATE {table} SET season_id = %s::uuid
                    WHERE field_id = %s::uuid AND season_id IS NULL AND {date_col} >= %s
                    """,
                    (season_id, field_id, from_date),
                )
                updated += cur.rowcount or 0
            except Exception as inner:
                # One missing column must not abort the others.
                print(f"[seasons.repository] attribute {table} failed: {inner}")
        conn.commit()
        cur.close()
        return updated
    except Exception as e:
        print(f"[seasons.repository] attribute_observations failed: {e}")
        try:
            conn.rollback()
        except Exception:
            pass
        return 0
    finally:
        try:
            conn.close()
        except Exception:
            pass
