"""The Doc type is where `prose is not state` stops being a request."""

import dataclasses

import pytest

from librarian.doc import Doc, DocError, Finding, Gap

BASE = dict(repo="ms", path="kb/expertise/x.md", locator="verdict",
            commit_sha="abc1234", kind="expertise")


def test_uid_is_a_walkable_coordinate():
    assert Doc(**BASE).uid == "ms:kb/expertise/x.md#verdict"


@pytest.mark.parametrize("kw", [
    dict(repo="nope"), dict(kind="nope"), dict(evidence="probably"),
    dict(provenance="vibes"), dict(reproduced="sort-of"),
])
def test_branchable_fields_reject_prose(kw):
    with pytest.raises(DocError):
        Doc(**{**BASE, **kw})


@pytest.mark.parametrize("kw", [
    dict(path=""), dict(locator=""), dict(commit_sha=""),
    dict(path="kb\\x.md"), dict(locator="검증"),
])
def test_coordinates_are_mandatory_and_ascii(kw):
    with pytest.raises(DocError):
        Doc(**{**BASE, **kw})


def test_review_after_must_be_a_date():
    Doc(**BASE, review_after="2027-08-18")
    with pytest.raises(DocError):
        Doc(**BASE, review_after="<YYYY-MM-DD>")


def test_advances_is_derived_so_it_cannot_disagree():
    """Only a measurement may advance a verdict.

    Stored as a field, `advances` could contradict `evidence`, and that
    contradiction is the shape of BD's recorded accident: `T = 300 K` filed as
    measured when it was a choice, propagating -4% to -14% downstream. Derived,
    the contradiction is not representable -- there is no setter to get wrong.
    """
    assert Doc(**BASE, evidence="measured").advances is True
    assert Doc(**BASE, evidence="assumed").advances is False
    assert Doc(**BASE, evidence=None).advances is False
    with pytest.raises(dataclasses.FrozenInstanceError):
        Doc(**BASE).advances = True          # type: ignore[misc]


def test_prose_fields_are_not_validated():
    d = Doc(**BASE, title="어떤 제목", body="prose, any language", conditions="anything")
    assert d.title and d.body and d.conditions


def test_gap_and_finding_shapes():
    g = Gap(repo="ms", registry="data/fluorophores.yaml",
            entry="fluorophores.AlexaFluor488", field="bleach_photons", present=False)
    assert g.uid.endswith("#fluorophores.AlexaFluor488.bleach_photons")
    with pytest.raises(DocError):
        Finding("c", "s", "d", severity="catastrophic")
