"""
Secrets are compared in constant time, and principal resolution is not copied.

Both are lint-shaped rather than unit-shaped, which is unusual here — but both
are the kind of thing that gets reintroduced by someone writing the obvious
`==`, and neither shows up as a failing test anywhere else. They show up as a
timing oracle on a key that reads a whole tenant's fields.
"""

import os
import pathlib
import re

import pytest

import auth_roles

ROOT = pathlib.Path(__file__).resolve().parent.parent

#: Env vars holding a secret. Comparing any of these with `==` is the finding.
SECRET_ENVS = ("INSTITUTIONAL_API_KEY", "ADMIN_TOKEN")


def _source_files():
    for path in ROOT.glob("*.py"):
        if path.name.startswith(("migrate_", "test_")):
            continue
        yield path


def test_no_secret_is_compared_with_a_plain_equality():
    # `==` short-circuits on the first differing byte, so response time leaks
    # the secret's prefix. hmac.compare_digest does not.
    offenders = []
    for path in _source_files():
        for index, line in enumerate(path.read_text().split("\n"), start=1):
            if "compare_digest" in line or line.lstrip().startswith("#"):
                continue
            if re.search(r"(x_api_key|x_admin_token|api_key|admin_token)\s*[!=]=\s*expected", line):
                offenders.append(f"{path.name}:{index}")
            if re.search(r"expected\s*[!=]=\s*(x_api_key|x_admin_token)", line):
                offenders.append(f"{path.name}:{index}")
    assert offenders == [], f"use hmac.compare_digest: {offenders}"


def test_principal_resolution_is_not_hand_copied():
    # app.get_state_principal and season_routes.get_principal were near-identical
    # copies. Two hand-written copies of an authentication decision drift, and
    # the drift is invisible until one of them is the lenient one.
    for name in ("app.py", "season_routes.py"):
        src = (ROOT / name).read_text()
        assert "resolve_principal" in src, name
        # The tell-tale of a re-inlined copy.
        assert 'os.environ.get("INSTITUTIONAL_API_KEY")' not in src, (
            f"{name} resolves the institutional key itself again — "
            "delegate to auth_roles.resolve_principal"
        )


# ── Behaviour ─────────────────────────────────────────────────────────────────


def test_an_absent_key_refuses_rather_than_admitting(monkeypatch):
    # The safe default: with no INSTITUTIONAL_API_KEY configured, presenting one
    # must fail rather than match an empty string.
    monkeypatch.delenv("INSTITUTIONAL_API_KEY", raising=False)
    with pytest.raises(Exception) as exc:
        auth_roles.resolve_principal(None, "anything", "t-1")
    assert getattr(exc.value, "status_code", None) == 401


def test_a_wrong_key_is_refused(monkeypatch):
    monkeypatch.setenv("INSTITUTIONAL_API_KEY", "correct-key")
    with pytest.raises(Exception) as exc:
        auth_roles.resolve_principal(None, "wrong-key", "t-1")
    assert getattr(exc.value, "status_code", None) == 401


def test_a_correct_key_without_a_tenant_is_refused(monkeypatch):
    # The key alone says nothing about scope. Admitting it unscoped would give
    # a caller every tenant.
    monkeypatch.setenv("INSTITUTIONAL_API_KEY", "correct-key")
    with pytest.raises(Exception) as exc:
        auth_roles.resolve_principal(None, "correct-key", None)
    assert getattr(exc.value, "status_code", None) == 401


def test_a_correct_key_with_a_tenant_is_scoped_to_exactly_that_tenant(monkeypatch):
    monkeypatch.setenv("INSTITUTIONAL_API_KEY", "correct-key")
    principal = auth_roles.resolve_principal(None, "correct-key", "t-1")
    assert principal["tenant_ids"] == ["t-1"]
    assert principal["is_admin"] is False


def test_the_api_key_path_never_grants_admin(monkeypatch):
    # Admin is a session-role decision. A shared key must not be able to reach it.
    monkeypatch.setenv("INSTITUTIONAL_API_KEY", "correct-key")
    assert auth_roles.resolve_principal(None, "correct-key", "t-1")["is_admin"] is False
