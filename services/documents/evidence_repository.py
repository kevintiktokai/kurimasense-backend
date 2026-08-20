"""
Gathering what a Season Evidence Pack is allowed to claim.

One batched read per tenant, then :func:`build_evidence_pack` decides what the
document says. The SQL lives here and the judgement lives in
``services/documents/evidence_pack.py``, per this repo's split.

**Which themes this can evidence, and which it cannot.**

The Sustainable Tobacco Programme has four themes the pack must cover. Three
have a source in this database; one does not, and that is stated rather than
approximated:

  ``soil``            a ``soil_profiles`` row for the field
  ``crop_protection`` a ``field_inputs`` row in the coverage window
  ``good_agricultural_practice``
                      a stand check, or a logged activity, in the window
  ``land_use``        **no source yet.** See below.

Land use and deforestation needs multi-year imagery compared against the field
boundary — reachable with the CDSE backfill, not yet wired to anything. Until it
is, no field carries the theme, the pack reports it as "No evidence recorded",
and the reader can tell that we did not check rather than that we checked and
found nothing.

That is deliberate and it should stay uncomfortable. Deforestation is the
reputational exposure a leaf buyer opens the pack for, and a theme quietly
marked covered because the query returned rows would be the single most
dangerous line in the document.

.. warning::

   A field counts as **observed** when it has a ``daily_logs`` row carrying an
   NDVI value inside the coverage window. That is the definition the verified
   hectare figure rests on, and therefore what the verification line asserts.
   Widening it — to any row, or to any date — would inflate covered hectares
   without anything in the document changing to show it.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Optional

from psycopg2.extras import RealDictCursor

from database import get_db_connection

from .evidence_pack import FieldEvidence, GrowerEvidence

#: Themes this repository can currently evidence. ``land_use`` is absent on
#: purpose — see the module docstring.
EVIDENCEABLE_THEMES: frozenset[str] = frozenset(
    {"soil", "crop_protection", "good_agricultural_practice"}
)


class EvidenceUnavailable(RuntimeError):
    """The evidence for a pack could not be read."""


_SQL = """
WITH field_scope AS (
    SELECT f.id, f.name, f.grower_id, f.size_hectares, f.crop_type
    FROM fields f
    WHERE f.tenant_id = %(tenant)s::uuid
      AND f.deleted_at IS NULL
),
observed AS (
    -- NDVI inside the window. This is what "observed" means, and what the
    -- verification line's hectare figure rests on.
    SELECT DISTINCT d.field_id
    FROM daily_logs d
    JOIN field_scope s ON s.id = d.field_id
    WHERE d.log_date BETWEEN %(start)s AND %(end)s
      AND d.ndvi IS NOT NULL
),
soil AS (
    SELECT DISTINCT p.field_id FROM soil_profiles p
    JOIN field_scope s ON s.id = p.field_id
),
protection AS (
    SELECT DISTINCT i.field_id FROM field_inputs i
    JOIN field_scope s ON s.id = i.field_id
    WHERE i.input_date BETWEEN %(start)s AND %(end)s
),
practice AS (
    SELECT DISTINCT field_id FROM (
        SELECT a.field_id FROM field_activities a
        JOIN field_scope s ON s.id = a.field_id
        WHERE a.visit_date BETWEEN %(start)s AND %(end)s
        UNION ALL
        SELECT se.field_id FROM seasons se
        JOIN field_scope s ON s.id = se.field_id
        WHERE se.established_population_per_ha IS NOT NULL
    ) practice_sources
)
SELECT
    fs.id::text            AS field_id,
    fs.name                AS field_name,
    fs.size_hectares       AS hectares,
    fs.crop_type           AS crop,
    fs.grower_id::text     AS grower_id,
    g.name                 AS grower_name,
    g.timb_grower_number   AS timb_grower_number,
    (o.field_id IS NOT NULL)  AS observed,
    (so.field_id IS NOT NULL) AS has_soil,
    (pr.field_id IS NOT NULL) AS has_protection,
    (pa.field_id IS NOT NULL) AS has_practice
FROM field_scope fs
LEFT JOIN growers g   ON g.id = fs.grower_id AND g.deleted_at IS NULL
LEFT JOIN observed o  ON o.field_id = fs.id
LEFT JOIN soil so     ON so.field_id = fs.id
LEFT JOIN protection pr ON pr.field_id = fs.id
LEFT JOIN practice pa ON pa.field_id = fs.id
ORDER BY g.name NULLS LAST, fs.name
"""


def _themes_for(row: dict[str, Any]) -> frozenset[str]:
    """Which STP themes this field has evidence for.

    ``land_use`` is never included. Nothing in this database evidences it yet,
    and inferring it from the presence of a boundary would turn "we have a
    polygon" into "we checked for deforestation".
    """
    themes = set()
    if row.get("has_soil"):
        themes.add("soil")
    if row.get("has_protection"):
        themes.add("crop_protection")
    if row.get("has_practice"):
        themes.add("good_agricultural_practice")
    return frozenset(themes)


def gather_growers(
    tenant_id: str,
    *,
    coverage_start: date,
    coverage_end: date,
    user_id: Optional[str] = None,
    tenant_ids: Optional[list[str]] = None,
) -> tuple[GrowerEvidence, ...]:
    """
    Every grower in the tenant with their fields and what each is evidenced for.

    Fields with no grower are returned under a single unnamed grower rather than
    dropped. They are real hectares under management, and silently excluding
    them would make the pack's hectare figure disagree with the portfolio
    report's for reasons no reader could see.
    """
    from tenancy import arm_rls_gucs

    conn = get_db_connection()
    if not conn:
        raise EvidenceUnavailable("Database unavailable")
    try:
        arm_rls_gucs(conn, user_id, [str(t) for t in (tenant_ids or [])])
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(
            _SQL,
            {"tenant": tenant_id, "start": coverage_start, "end": coverage_end},
        )
        rows = cur.fetchall()
        cur.close()
    finally:
        try:
            conn.close()
        except Exception:  # pragma: no cover - close is best-effort
            pass

    return group_rows([dict(r) for r in rows])


def group_rows(rows: list[dict[str, Any]]) -> tuple[GrowerEvidence, ...]:
    """
    Fold flat field rows into growers. Pure, so the grouping is testable without
    a database — which matters because the ungrouped-field case below is easy to
    get wrong and invisible when it is.
    """
    grouped: dict[Optional[str], dict[str, Any]] = {}

    for row in rows:
        grower_id = row.get("grower_id")
        bucket = grouped.setdefault(
            grower_id,
            {
                "name": row.get("grower_name"),
                "timb": row.get("timb_grower_number"),
                "fields": [],
            },
        )
        bucket["fields"].append(
            FieldEvidence(
                field_id=row.get("field_id") or "",
                field_name=row.get("field_name") or "Field",
                hectares=_as_float(row.get("hectares")),
                crop=row.get("crop"),
                observed=bool(row.get("observed")),
                themes=_themes_for(row),
            )
        )

    out: list[GrowerEvidence] = []
    for grower_id, bucket in grouped.items():
        out.append(
            GrowerEvidence(
                grower_id=grower_id or "unassigned",
                # Named rather than blank: a reader has to be able to see that
                # these hectares belong to nobody in particular, because that is
                # itself the finding.
                grower_name=bucket["name"] or "Not assigned to a grower",
                timb_grower_number=bucket["timb"] if grower_id else None,
                fields=tuple(bucket["fields"]),
            )
        )
    return tuple(out)


def _as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
