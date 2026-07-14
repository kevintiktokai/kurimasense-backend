"""
Schema self-heal gate (RLS Step D unblocking, July 2026).

With DB_SELF_HEAL_SCHEMA=false the backend must issue NO runtime DDL — the
schema is managed by migrations/015_bootstrap_schema.sql, and the locked-down
NOBYPASSRLS app role (migration 016) cannot run CREATE/ALTER. These tests
guard the gate itself and the consistency of the migration artifacts.
"""

import pathlib
import re

import database
from database import schema_self_heal_enabled

MIGRATIONS = pathlib.Path(__file__).resolve().parent.parent / "migrations"


# --- The flag ---------------------------------------------------------------

def test_self_heal_defaults_on(monkeypatch):
    monkeypatch.delenv("DB_SELF_HEAL_SCHEMA", raising=False)
    assert schema_self_heal_enabled() is True


def test_self_heal_disabled_by_flag(monkeypatch):
    for v in ("false", "0", "no", "FALSE"):
        monkeypatch.setenv("DB_SELF_HEAL_SCHEMA", v)
        assert schema_self_heal_enabled() is False


# --- init_db honors the gate -------------------------------------------------

class _RecordingCursor:
    def __init__(self, log):
        self._log = log

    def execute(self, sql, params=None):
        self._log.append(sql)
        # Satisfy seed_crop_varieties' COUNT check with a populated table.
        self._row = {"n": 999}

    def fetchone(self):
        return getattr(self, "_row", {"n": 999})

    def fetchall(self):
        return []

    def close(self):
        pass


class _RecordingConn:
    def __init__(self, log):
        self._log = log

    def cursor(self, *a, **kw):
        return _RecordingCursor(self._log)

    def commit(self):
        pass

    def close(self):
        pass


def test_init_db_issues_no_ddl_when_disabled(monkeypatch):
    executed: list[str] = []
    monkeypatch.setenv("DB_SELF_HEAL_SCHEMA", "false")
    monkeypatch.setattr(database, "get_db_connection", lambda: _RecordingConn(executed))

    database.init_db()

    ddl = [s for s in executed if re.search(r"\b(CREATE|ALTER|DROP)\b", s, re.I)]
    assert ddl == [], f"runtime DDL issued despite DB_SELF_HEAL_SCHEMA=false: {ddl[:3]}"


def test_notifications_ensure_schema_skips_when_disabled(monkeypatch):
    from services.notifications import repository

    monkeypatch.setenv("DB_SELF_HEAL_SCHEMA", "false")
    monkeypatch.setattr(repository, "_SCHEMA_READY", False)
    # Poison the connection: any DDL attempt would blow up loudly.
    monkeypatch.setattr(
        repository, "get_db_connection",
        lambda: (_ for _ in ()).throw(AssertionError("DDL path used despite flag")),
    )
    assert repository.ensure_schema() is True


# --- Migration artifact consistency ------------------------------------------

def test_bootstrap_migration_covers_every_init_db_table():
    """Every CREATE TABLE the boot path knows must exist in migration 015 —
    otherwise turning self-heal off silently loses schema convergence."""
    init_src = pathlib.Path(database.__file__).read_text()
    notif_src = (
        pathlib.Path(database.__file__).parent / "services" / "notifications" / "repository.py"
    ).read_text()
    runtime_tables = set(
        re.findall(r"CREATE TABLE IF NOT EXISTS (\w+)", init_src + notif_src)
    )
    migration_tables = set(
        re.findall(
            r"CREATE TABLE IF NOT EXISTS (\w+)",
            (MIGRATIONS / "015_bootstrap_schema.sql").read_text(),
        )
    )
    missing = runtime_tables - migration_tables
    assert not missing, f"tables in runtime DDL but not in 015: {sorted(missing)}"


def test_force_migration_never_touches_bootstrap_tables():
    """tenants/tenant_members/profiles must never be FORCEd (runbook: GUC
    derivation chicken-and-egg). Guard the migration against future edits."""
    sql = (MIGRATIONS / "017_force_rls.sql").read_text()
    array_block = re.search(r"isolation_tables text\[\] := ARRAY\[(.*?)\]", sql, re.S).group(1)
    for t in ("tenants", "tenant_members", "profiles"):
        assert f"'{t}'" not in array_block, f"bootstrap table {t} must not be FORCEd"


def test_app_role_migration_grants_no_ddl():
    sql = (MIGRATIONS / "016_app_role_nobypassrls.sql").read_text()
    assert "NOBYPASSRLS" in sql
    assert "GRANT CREATE" not in sql.upper()
    assert re.search(r"GRANT SELECT, INSERT, UPDATE, DELETE", sql)
