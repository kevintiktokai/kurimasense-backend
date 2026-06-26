"""
Snapshot a yield_projections row whenever a live projection is computed.
Fail-safe: uses its own connection; a write failure logs and never breaks
the field-state response (Hard Rule 10).
"""

import json
import logging
import threading
from datetime import date
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def _do_snapshot(
    field_id: str,
    tenant_id: Optional[str],
    projected_tonnes_per_ha: Optional[float],
    confidence_band: str,
    confidence_pct: int,
    model_version: str,
    season_progress_pct: Optional[int],
    inputs_snapshot: Optional[Dict[str, Any]],
    projection_date: date,
    is_backtest: bool = False,
) -> None:
    from database import get_db_connection
    conn = get_db_connection()
    if not conn:
        return
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO yield_projections
                (field_id, tenant_id, projection_date, projected_tonnes_per_ha,
                 confidence_band, confidence_pct, model_version, is_backtest,
                 season_progress_pct, inputs_snapshot)
            VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (field_id, projection_date, is_backtest)
            WHERE is_backtest = FALSE
            DO UPDATE SET
                projected_tonnes_per_ha = EXCLUDED.projected_tonnes_per_ha,
                confidence_band = EXCLUDED.confidence_band,
                confidence_pct = EXCLUDED.confidence_pct,
                inputs_snapshot = EXCLUDED.inputs_snapshot,
                season_progress_pct = EXCLUDED.season_progress_pct
            """,
            (
                field_id,
                tenant_id,
                projection_date,
                projected_tonnes_per_ha,
                confidence_band,
                confidence_pct,
                model_version,
                is_backtest,
                season_progress_pct,
                json.dumps(inputs_snapshot) if inputs_snapshot else None,
            ),
        )
        conn.commit()
        cur.close()
    except Exception as exc:
        logger.warning("yield_projections snapshot failed (non-fatal): %s", exc)
        try:
            conn.rollback()
        except Exception:
            pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def snapshot_projection(
    field_row: Dict[str, Any],
    yield_raw: Optional[Dict[str, Any]],
    daily_logs: Optional[list] = None,
    is_backtest: bool = False,
    projection_date: Optional[date] = None,
    season_progress_pct: Optional[int] = None,
) -> None:
    """
    Persist a yield_projections row from the aggregator's raw yield dict.
    Runs in a background thread so it never blocks the HTTP response.
    Idempotent per (field_id, projection_date, is_backtest) via unique-index upsert.
    """
    if not yield_raw:
        return

    from services.calibration import MODEL_VERSION
    from services.field_state.classifiers import confidence_from_fraction

    projected = yield_raw.get("projected_yield") or yield_raw.get("projected_tonnes_per_ha")
    if projected is None:
        return

    band, pct = confidence_from_fraction(yield_raw.get("confidence_score"))

    inputs_snapshot = {
        "ndvi_values": (
            [float(l["ndvi"]) for l in (daily_logs or []) if l.get("ndvi") is not None][-7:]
            if daily_logs else None
        ),
        "confidence_score": yield_raw.get("confidence_score"),
        "adjustment_factors": yield_raw.get("adjustment_factors"),
    }

    field_id = str(field_row.get("id"))
    tenant_id = field_row.get("tenant_id")
    if tenant_id:
        tenant_id = str(tenant_id)

    t = threading.Thread(
        target=_do_snapshot,
        kwargs=dict(
            field_id=field_id,
            tenant_id=tenant_id,
            projected_tonnes_per_ha=float(projected),
            confidence_band=band,
            confidence_pct=pct,
            model_version=MODEL_VERSION,
            season_progress_pct=season_progress_pct,
            inputs_snapshot=inputs_snapshot,
            projection_date=projection_date or date.today(),
            is_backtest=is_backtest,
        ),
        daemon=True,
    )
    t.start()
