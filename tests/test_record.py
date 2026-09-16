"""Decision (j): two writers, and why neither a lock nor a merge is needed.

The three mechanisms (j) offered -- a single-writer queue, a lock,
version-and-merge -- all answer *"what happens when two writers want the same
thing."* No write tool here wants the same thing: both issue a new record and
neither updates one. What is left is a retry landing twice and a reader seeing a
prefix, and these tests are the two closures.
"""

import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from librarian.record import (RecordError, canonical, read_records,
                              record_name, slug, write_record)

DATE = "2026-09-15"


def test_the_same_record_written_twice_is_one_record(tmp_path):
    """Idempotence, and it is load-bearing rather than tidy.

    Oracle promotion requires a session reproduced under **two distinct
    `index_sha`** (FEEDBACK.md §5, decision 21), which exists to stop an agent
    promoting its own retrieval results to ground truth. If a retried
    `kb_feedback` landed twice, one caller calling twice would satisfy a check
    built to need two index states -- so the retry has to collapse, not count.
    """
    rec = {"schema": "librarian.retrieval/0.1", "query": "bleach photons",
           "cited": ["ms:data/fluorophores.yaml#AlexaFluor488"]}
    a = write_record(tmp_path, rec, DATE, "bleach photons")
    b = write_record(tmp_path, dict(reversed(list(rec.items()))), DATE,
                     "bleach photons")
    assert a.created is True and b.created is False
    assert a.path == b.path, "key order must not change the name"
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_a_different_record_never_contends_for_a_name(tmp_path):
    """Two records, two names, no ordering between them and nothing to serialize."""
    one = write_record(tmp_path, {"q": "a"}, DATE, "same label")
    two = write_record(tmp_path, {"q": "b"}, DATE, "same label")
    assert one.path != two.path and one.digest != two.digest
    assert one.created and two.created
    assert len(list(tmp_path.glob("*.json"))) == 2


def test_concurrent_writers_of_the_same_record_produce_one_file(tmp_path):
    """The claim under actual concurrency, not by inspection of the code."""
    rec = {"schema": "librarian.challenge/0.1", "target": "ms:kb/a.md#verdict"}
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(
            lambda _: write_record(tmp_path, rec, DATE, "one target"), range(8)))
    assert sum(r.created for r in results) == 1, "exactly one writer creates it"
    assert len({r.path for r in results}) == 1
    assert len(list(tmp_path.glob("*.json"))) == 1


def test_concurrent_writers_of_different_records_all_land(tmp_path):
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(
            lambda i: write_record(tmp_path, {"i": i}, DATE, "batch"), range(32)))
    assert all(r.created for r in results)
    assert len(list(tmp_path.glob("*.json"))) == 32
    assert len(read_records(tmp_path)) == 32


def test_a_reader_never_sees_a_partial_record(tmp_path):
    """The other half of §8's row: *"an index built over a half-written entry."*

    Append-only removes the lost update; only the atomic rename removes this.
    `scan()` walks files, so a record has to be absent or whole -- never a
    prefix. Asserted by reading every file while writers are running: each read
    is either a clean parse or a `FileNotFoundError`, and never a `JSONDecodeError`.
    """
    errors = []

    def reader():
        for _ in range(400):
            for p in list(tmp_path.glob("*.json")):
                try:
                    json.loads(p.read_text(encoding="utf-8"))
                except FileNotFoundError:
                    pass                       # not yet renamed in: correct
                except json.JSONDecodeError as e:
                    errors.append(f"{p.name}: {e}")

    body = {"note": "x" * 20_000}              # big enough to need many writes
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(reader) for _ in range(3)]
        futures += [pool.submit(write_record, tmp_path, {**body, "i": i},
                                DATE, "partial read") for i in range(60)]
        for f in futures:
            f.result()
    assert errors == [], errors[:3]


def test_no_temp_file_survives_a_write(tmp_path):
    """A leftover `.tmp` is invisible to `read_records` but not to a person, and
    a directory of debris is how a reader stops trusting the listing."""
    for i in range(5):
        write_record(tmp_path, {"i": i}, DATE, "clean up")
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".")] == []


def test_a_name_collision_with_different_bytes_refuses(tmp_path):
    """The name is a digest of the content, so this is a hand-edited record or a
    sha256 collision. Overwriting either would destroy the record it claims to
    be -- and these folders are *"a record, so they are not deleted."*"""
    w = write_record(tmp_path, {"q": "a"}, DATE, "edited")
    w.path.write_text('{"q": "tampered"}\n', encoding="utf-8")
    with pytest.raises(RecordError, match="different content"):
        write_record(tmp_path, {"q": "a"}, DATE, "edited")


def test_a_record_is_never_updated_in_place(tmp_path):
    """There is no code path for it, and that is the policy rather than an
    omission: a correction is a new record that supersedes the old one, which
    is how custody already models retirement (README, edge 4)."""
    import librarian.record as record
    exported = {n for n in dir(record) if not n.startswith("_")}
    assert not {n for n in exported
                if any(v in n for v in ("update", "edit", "patch", "delete"))}


def test_the_name_is_reproducible_and_carries_no_clock(tmp_path):
    """A clock read inside the writer would make the name depend on when it ran,
    which is the same reason `manifest()` carries no `built_at`."""
    rec = {"q": "reproducible"}
    first, d1 = record_name(rec, DATE, "a label")
    second, d2 = record_name(rec, DATE, "a label")
    assert first == second and d1 == d2
    assert first.startswith(DATE) and first.endswith(".json")
    assert d1 in first and slug("a label") in first
    with pytest.raises(RecordError, match="YYYY-MM-DD"):
        record_name(rec, "15-09-2026", "a label")


def test_prose_stays_readable_and_paths_stay_ascii(tmp_path):
    """Decision 11 puts ASCII on paths, not in prose. A record may quote the
    operator in Korean; its filename may not."""
    rec = {"note": "드래그캘리브레이션을 해서 트랩 스티프니스를 측정"}
    w = write_record(tmp_path, rec, DATE, "드래그 캘리브레이션 plan")
    assert w.path.name.isascii(), w.path.name
    assert json.loads(w.path.read_text(encoding="utf-8")) == rec
    assert "스티프니스" in canonical(rec).decode("utf-8")


def test_dotfiles_and_temp_names_are_not_records(tmp_path):
    write_record(tmp_path, {"q": "real"}, DATE, "real")
    (tmp_path / ".hidden.json").write_text("{}", encoding="utf-8")
    assert len(read_records(tmp_path)) == 1


# --- the index's half of the same rule --------------------------------------

def test_the_index_is_never_absent_while_it_is_being_rebuilt(tmp_path):
    """`build` used to unlink the old index and create the new one in place.

    That left a window where the file did not exist, and
    `mcp_server.tools._open` answers `status: no_index` when it cannot find
    one -- so a call arriving mid-rebuild got a correct-but-empty answer for no
    reason other than timing. The server opens the index **read-only and per
    call**, which is exactly the shape an atomic rename serves: the caller gets
    the old index or the new one.

    Asserted by watching the path while a rebuild runs over it.
    """
    from concurrent.futures import ThreadPoolExecutor

    from librarian.doc import Doc
    from librarian.index import build

    idx = tmp_path / "kb.sqlite"
    docs = [Doc(repo="ms", path=f"kb/expertise/{i}.md", locator="verdict",
                commit_sha="s1", kind="expertise", title=f"entry {i}",
                body="x" * 4000) for i in range(300)]
    build(docs, idx, {"ms": "s1"})
    assert idx.exists()

    missing = []

    def watch():
        for _ in range(3000):
            if not idx.exists():
                missing.append(1)

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = [pool.submit(watch) for _ in range(2)]
        futures.append(pool.submit(build, docs, idx, {"ms": "s2"}))
        for f in futures:
            f.result()

    assert missing == [], f"the index vanished {len(missing)} times mid-rebuild"
    assert [p.name for p in tmp_path.iterdir() if p.name.startswith(".")] == []


def test_two_identical_rebuilds_race_to_the_same_bytes(tmp_path):
    """Why two concurrent rebuilds need no lock either.

    `build` is deterministic -- sorted by uid, no timestamps (BUILD.md 4-A) --
    so identical inputs give byte-identical output and the race has no losing
    outcome. Differing inputs leave the last writer's index, and `index_stale`
    then reports the truth on the next call rather than the index pretending.
    """
    from concurrent.futures import ThreadPoolExecutor

    from librarian.doc import Doc
    from librarian.index import build

    docs = [Doc(repo="ms", path=f"kb/expertise/{i}.md", locator="verdict",
                commit_sha="s1", kind="expertise", title=f"entry {i}")
            for i in range(50)]
    a, b = tmp_path / "a.sqlite", tmp_path / "b.sqlite"
    build(docs, a, {"ms": "s1"})

    target = tmp_path / "raced.sqlite"
    with ThreadPoolExecutor(max_workers=4) as pool:
        for f in [pool.submit(build, docs, target, {"ms": "s1"})
                  for _ in range(4)]:
            f.result()
    build(docs, b, {"ms": "s1"})
    assert a.read_bytes() == b.read_bytes(), "build is not deterministic"
    assert target.read_bytes() == a.read_bytes()
