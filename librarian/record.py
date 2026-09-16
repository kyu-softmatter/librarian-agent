"""One record, written so that two writers never contend.

`PLAN.md` decision (j) asked which of three concurrency mechanisms this
repository needs -- a single-writer queue, a lock, or version-and-merge -- and
the answer is none of them, because the premise does not hold for what the write
tools actually do. `kb_challenge_raise` issues a **challenge** and `kb_feedback`
records a **session**; both emit a new record and **neither updates one**. There
is nothing to merge, and nothing two writers both want.

What is left is two narrower failures, and each is closed by construction rather
than by serialization:

  a retried call becoming two records   -> the name is a hash of the content,
                                           created exclusively, so the second
                                           write is an idempotent no-op

  a reader seeing half a record         -> the bytes land in a sibling temp
                                           file and the final name is created
                                           as a hard link to it, which is
                                           atomic and exclusive in one call

The first matters more than it looks. Oracle promotion requires a session
reproduced under **two distinct `index_sha`** ([../FEEDBACK.md](../FEEDBACK.md)
§5, decision 21), and that condition exists to stop an agent promoting its own
retrieval results to ground truth. If a retried `kb_feedback` could land twice,
one caller calling twice would satisfy a check designed to need two index
states. Idempotence is therefore not tidiness here; it is what keeps the damping
on `C-001`'s loop.

**Nothing in this module touches git.** Committing is a human or CI act, which
is what keeps the worst contention out of a tool's write path entirely.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

#: Long enough that a collision is not a practical concern, short enough that a
#: filename stays readable. A collision does not corrupt anything either way:
#: `write_record` compares the bytes and refuses rather than overwriting.
_HASH_CHARS = 8

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")
_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class RecordError(ValueError):
    """A write that would have produced a record the policy forbids."""


@dataclass(frozen=True)
class Written:
    """What a write did -- including having already been done.

    `created=False` is a success, not a failure: it means this exact record is
    already on disk under this exact name. A caller that treats it as an error
    retries, and retrying is the thing the name exists to make harmless.
    """
    path: Path
    digest: str
    created: bool


def canonical(record: dict[str, Any]) -> bytes:
    """The bytes a record is addressed by, and the bytes that get written.

    Sorted keys and a fixed separator, so the same record hashes the same on
    every machine and in every Python build -- the same requirement the index
    build meets by sorting on `uid`, for the same reason.

    `ensure_ascii=False` because a record may quote an operator in Korean and
    escaping it would make the file unreadable for no gain. Decision 11 puts
    ASCII on **paths**, not in prose.
    """
    return json.dumps(record, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), indent=2).encode("utf-8") + b"\n"


def slug(text: str, limit: int = 40) -> str:
    """A filename-safe fragment of a title. Lossy on purpose -- the hash carries
    identity, and this only has to make a directory listing legible."""
    s = _SLUG_STRIP.sub("-", text.strip().lower()).strip("-")
    return s[:limit].rstrip("-")


def record_name(record: dict[str, Any], date: str, label: str,
                suffix: str = ".json") -> tuple[str, str]:
    """`(filename, digest)` -- the date for order, the label for a reader, the
    digest for identity.

    The date is a parameter rather than `today()`: a record states the day it
    is about, and a clock read inside this function would make the name depend
    on when it ran. That is the same reason `manifest()` carries no timestamp.
    """
    if not _DATE.match(date):
        raise RecordError(f"date {date!r} is not YYYY-MM-DD")
    digest = hashlib.sha256(canonical(record)).hexdigest()[:_HASH_CHARS]
    parts = [date, slug(label), digest]
    return "-".join(p for p in parts if p) + suffix, digest


def write_record(directory: Path, record: dict[str, Any], date: str,
                 label: str, suffix: str = ".json") -> Written:
    """Write one record. Safe to call concurrently, and safe to call twice.

    Not safe to call for an **update**: there is no code path here that
    modifies an existing record, because the policy has none. A correction is a
    new record that supersedes the old one, which is how custody already models
    retirement everywhere else in this repository.
    """
    body = canonical(record)
    name, digest = record_name(record, date, label, suffix)
    directory.mkdir(parents=True, exist_ok=True)
    final = directory / name

    # The whole record goes to a sibling first, then the final name is created
    # as a **hard link** to it. `os.link` is the one call that is atomic *and*
    # exclusive, and both properties are needed at once:
    #
    #   atomic     -> the final path never exists holding a prefix. `scan()`
    #                 walks files, so a record must be absent or whole.
    #   exclusive  -> it raises `FileExistsError` rather than overwriting,
    #                 which is what makes a retry idempotent.
    #
    # **Claiming the name first with `O_CREAT | O_EXCL` does not work, and the
    # concurrency test is what said so.** That gets exclusivity, but it
    # publishes an **empty** file for the length of the write, and a reader
    # scanning then got `JSONDecodeError` on a name that was already visible.
    # The guard defeated the thing it was guarding.
    #
    # The temp name carries a uuid, not just the pid: two *threads* of one
    # process writing the same record would otherwise share one temp path and
    # overwrite each other's bytes under it.
    tmp = directory / f".{name}.{uuid.uuid4().hex}.tmp"
    try:
        tmp.write_bytes(body)
        try:
            os.link(tmp, final)
        except FileExistsError:
            existing = final.read_bytes()
            if existing == body:
                return Written(final, digest, created=False)
            # The name is a digest of the content, so identical names with
            # different bytes is a hand-edited record or a sha256 collision.
            # These folders are "a record, so they are not deleted" -- neither
            # case is worth overwriting.
            raise RecordError(
                f"{final} exists with different content. The name is a digest "
                f"of the record, so this is not a normal collision -- do not "
                f"overwrite it.") from None
        except OSError:
            # A filesystem without hard links (some network and FAT mounts).
            # `os.replace` keeps atomicity and loses only the exclusivity, so
            # `created` may read True for a write that was already on disk --
            # the bytes are identical either way, which is why this is a
            # degradation and not a correctness hole.
            os.replace(tmp, final)
    finally:
        tmp.unlink(missing_ok=True)
    return Written(final, digest, created=True)


def read_records_with_ids(directory: Path, prefix: str,
                          suffix: str = ".json") -> list[dict[str, Any]]:
    """Every record, each carrying its derived id under `_id`.

    The id is not in the file -- identity is the filename's digest, so a stored
    copy could disagree with the file it sits in. A caller that needs to refer
    to a record (an oracle naming the sessions it came from) needs the id back,
    and this is where it is re-derived rather than written down twice.

    The underscore marks it as attached on read: it is not part of the record
    and it is not hashed.
    """
    out = []
    if not directory.is_dir():
        return out
    for p in sorted(directory.glob(f"*{suffix}")):
        if p.name.startswith("."):
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        rec["_id"] = f"{prefix}{p.stem.rsplit('-', 1)[-1]}"
        out.append(rec)
    return out


def read_records(directory: Path, suffix: str = ".json") -> list[dict[str, Any]]:
    """Every record in a directory, in filename order.

    **There is no generated index over these folders, by decision.** A rollup
    file that two writers both append to is the one shape that would need a
    lock -- and it is also BD's `knowledge/source/papers/INDEX.md`, headed *do
    not edit by hand*, naming a generator that is not in the repository and
    stating 40 entries where 42 files exist. That file is why this repository
    exists. The listing is derived at read time instead.
    """
    if not directory.is_dir():
        return []
    out = []
    for p in sorted(directory.glob(f"*{suffix}")):
        if p.name.startswith("."):
            continue
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out
