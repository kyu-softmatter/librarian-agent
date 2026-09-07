"""Regression tests for two false-positive classes that buried the real findings."""

import textwrap

from librarian.drift import drift


def _entry(text: str) -> str:
    return textwrap.dedent(text).lstrip()


def test_falsifier_convention_is_set_by_the_majority(tmp_path):
    """2 of 20 files mentioning a falsifier is not a folder convention.

    A `>= 2` threshold reported the other 18 decision logs as defective and
    buried the one finding that mattered. A decision log is not a claim entry
    and owes no falsifier; `kb/expertise/` (5 of 6) does.
    """
    kb = tmp_path / "kb"
    (kb / "decisions").mkdir(parents=True)
    for i in range(20):
        body = "## Falsification conditions\n" if i < 2 else "## Outcome\n"
        (kb / "decisions" / f"d{i:02d}.md").write_text(f"# decision {i}\n\n{body}")

    (kb / "expertise").mkdir()
    for i in range(5):
        (kb / "expertise" / f"e{i}.md").write_text(
            _entry(f"""
            ---
            id: e{i}
            evidence: measured
            ---
            ## Verdict
            ## Falsification conditions
            """))
    (kb / "expertise" / "no-falsifier.md").write_text(
        _entry("""
        ---
        id: no-falsifier
        evidence: measured
        ---
        ## Verdict
        """))

    subjects = [f.subject for f in drift(tmp_path, "t") if f.check == "falsifier_missing"]
    assert subjects == ["t:kb/expertise/no-falsifier.md"]


def test_a_prose_mention_is_not_a_gate_declaration(tmp_path):
    """BD's roadmap discusses the microscope's gates in prose.

    *"G8 needs D or tau_c ... at that repo's G11"* refers to gates BD does not
    own, and BD's own Python namespace is unrelated. Subtracting one set from
    the other reported six of MS's gates as missing from BD.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "06-roadmap.md").write_text(
        "They propagate through its committee: **G8** needs `D`, and settle "
        "at that repo's G11.\n")
    (tmp_path / "engine.py").write_text("GATES = ['G0', 'G1']\n")
    assert [f for f in drift(tmp_path, "t")
            if f.check == "gate_declared_not_implemented"] == []

    # A table row carries the threshold and the default verdict: a declaration.
    (docs / "04-decision-engine.md").write_text(
        "| Gate | What | Threshold | Inputs | Default |\n"
        "|---|---|---|---|---|\n"
        "| G2 | Emission collection | `>= 15%` | curves | BLOCKED |\n")
    found = [f.subject for f in drift(tmp_path, "t")
             if f.check == "gate_declared_not_implemented"]
    assert found == ["t:G2"]


def test_code_that_implements_a_gate_without_naming_it(tmp_path):
    """MS reduced: `optics/gate.py` enforces G1-G4 and writes no gate id.

    Subtracting the ids in code from the ids declared in docs cannot tell
    "nothing implements this" from "the implementation does not label itself",
    and it reported the second as the first, at error severity. The
    implementation-status row is what distinguishes them -- but only as far as
    it can be checked, so a row naming a symbol that is not in the repository
    earns no credit and the gate is still reported as unimplemented.
    """
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "04-decision-engine.md").write_text(_entry("""
        | # | Gate | Criterion | Default |
        |---|---|---|---|
        | G2 | Emission collection | `>= 15%` | BLOCKED |
        | G3 | Excitation blocking | `>= 5 OD` | BLOCKED |

        | Section | Content | Status |
        |---|---|---|
        | G2–G3 | `optics.gate.evaluate` | covered by tests |
        """), encoding="utf-8")

    # No implementation yet: the docs row points at nothing, so the row is
    # ignored and both gates stay errors.
    findings = drift(tmp_path, "t")
    assert {f.subject for f in findings
            if f.check == "gate_declared_not_implemented"} == {"t:G2", "t:G3"}
    assert [f for f in findings if f.check == "gate_not_traceable_to_code"] == []

    # Now the symbol exists, and still no gate id appears anywhere in code.
    opt = tmp_path / "optics"
    opt.mkdir()
    (opt / "gate.py").write_text("def evaluate(channel):\n    return None\n")

    findings = drift(tmp_path, "t")
    assert [f for f in findings if f.check == "gate_declared_not_implemented"] == []
    gates = [f for f in findings if f.check == "gate_not_traceable_to_code"]
    assert {f.subject for f in gates} == {"t:G2", "t:G3"}
    assert {f.severity for f in gates} == {"warn"}
    assert all("optics.gate.evaluate" in f.detail
               and "docs/04-decision-engine.md" in f.detail for f in gates)


def test_generated_artefact_outliving_its_generator(tmp_path):
    """The observed case, reduced: a header that forbids editing, and no generator."""
    d = tmp_path / "papers"
    d.mkdir()
    (d / "INDEX.md").write_text(
        "<!-- Generated: docs/tools/wiki_index.py -- do not edit by hand -->\n"
        "# index\n\n| | |\n|---|---|\n| entries | **1** |\n")
    (d / "a.md").write_text("# a\n")
    (d / "b.md").write_text("# b\n")

    checks = {f.check for f in drift(tmp_path, "t")}
    assert "generator_missing" in checks
    assert "declared_count_mismatch" in checks

    (tmp_path / "docs" / "tools").mkdir(parents=True)
    (tmp_path / "docs" / "tools" / "wiki_index.py").write_text("# regenerates\n")
    checks = {f.check for f in drift(tmp_path, "t")}
    assert "generator_missing" not in checks
    assert "declared_count_mismatch" in checks      # still 1 declared, 2 actual


def test_tier_stated_by_the_path_and_the_field_must_agree(tmp_path):
    kb = tmp_path / "kb" / "literature"
    kb.mkdir(parents=True)
    kb.joinpath("bad.md").write_text(
        _entry("""
        ---
        id: bad
        evidence: measured
        ---
        ## Verdict
        """))
    subjects = [f.subject for f in drift(tmp_path, "t") if f.check == "tier_path_conflict"]
    assert subjects == ["t:kb/literature/bad.md"]
