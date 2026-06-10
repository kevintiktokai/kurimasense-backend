"""Tests for scripts/trigger_demo_backfill.py (the API backfill trigger)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import trigger_demo_backfill as tdb  # noqa: E402


def test_read_queue_missing(tmp_path):
    assert tdb.read_queue(str(tmp_path / "nope.txt")) == []


def test_read_queue_reads_ids(tmp_path):
    q = tmp_path / "q.txt"
    q.write_text("id-1\nid-2\n\n  id-3  \n")
    assert tdb.read_queue(str(q)) == ["id-1", "id-2", "id-3"]


def test_main_exits_gracefully_without_queue(tmp_path, capsys):
    rc = tdb.main(["--base-url", "http://x", "--token", "t", "--queue", str(tmp_path / "missing.txt")])
    assert rc == 0
    assert "Nothing to trigger" in capsys.readouterr().out


def test_main_triggers_each_field(tmp_path, monkeypatch, capsys):
    q = tmp_path / "q.txt"
    q.write_text("aaa\nbbb\n")
    calls = []
    monkeypatch.setattr(tdb, "trigger", lambda base, token, fid: calls.append((base, token, fid)) or 200)

    rc = tdb.main(["--base-url", "http://api", "--token", "jwt", "--queue", str(q), "--delay", "0"])
    out = capsys.readouterr().out

    assert rc == 0
    assert [c[2] for c in calls] == ["aaa", "bbb"]
    assert "[1/2] Triggered backfill for field aaa" in out
    assert "[2/2] Triggered backfill for field bbb" in out
