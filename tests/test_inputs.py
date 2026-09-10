"""The input closure of a computation, and the places a name cannot bridge."""

import ast
import textwrap

import pytest

from librarian.inputs import (
    Leaf,
    Recipe,
    _classes,
    find_function,
    load_aliases,
    recipe,
    registry_keys,
    verify_aliases,
    walk_inputs,
)


def write_module(tmp_path, body: str, name: str = "goa.py"):
    (tmp_path / name).write_text(textwrap.dedent(body).lstrip())
    return tmp_path


MODULE = '''
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Bead:
        """A homogeneous dielectric sphere."""
        radius_m: float
        n: float

    @dataclass(frozen=True)
    class Medium:
        """The immersion medium the bead sits in."""
        n: float
        viscosity_pa_s: float | None

    @dataclass(frozen=True)
    class ObjectiveBeam:
        """The focusing objective and the Gaussian beam it produces."""
        na: float
        wavelength_m: float

    def radial_stiffness_n_per_m(power_w: float, bead: Bead, medium: Medium,
                                 beam: ObjectiveBeam, *,
                                 probe_fraction: float = 0.02,
                                 n_points: int = 96) -> float:
        """Linear-regime radial trap stiffness."""
        return 0.0
'''


# --- walking the signature -------------------------------------------------

def test_the_closure_is_derived_from_the_signature(tmp_path):
    """A hand-written input list goes stale the first time an argument is added.

    Walking the signature cannot drift from the code, because it is the code.
    """
    write_module(tmp_path, MODULE)
    _, fn = find_function(tmp_path, "radial_stiffness_n_per_m")
    leaves = walk_inputs(tmp_path, fn, _classes(tmp_path))
    assert [l.path for l in leaves] == [
        "power_w", "bead.radius_m", "bead.n",
        "medium.n", "medium.viscosity_pa_s",
        "beam.na", "beam.wavelength_m",
    ]


def test_keyword_only_defaults_are_not_inputs(tmp_path):
    """`probe_fraction=0.02` is how the computation runs, not what it needs."""
    write_module(tmp_path, MODULE)
    _, fn = find_function(tmp_path, "radial_stiffness_n_per_m")
    paths = {l.path for l in walk_inputs(tmp_path, fn, _classes(tmp_path))}
    assert "probe_fraction" not in paths and "n_points" not in paths


def test_optional_is_carried_through(tmp_path):
    write_module(tmp_path, MODULE)
    _, fn = find_function(tmp_path, "radial_stiffness_n_per_m")
    leaves = {l.path: l for l in walk_inputs(tmp_path, fn, _classes(tmp_path))}
    assert leaves["medium.viscosity_pa_s"].optional is True
    assert leaves["beam.na"].optional is False


def test_the_declaring_docstring_travels_with_the_leaf(tmp_path):
    """Because `n` is one character and cannot be a search query.

    FTS5 forms no token from it, so the leaf came back with no candidates at
    all. What declares it can be searched instead, and that is read off the
    class rather than guessed.
    """
    write_module(tmp_path, MODULE)
    _, fn = find_function(tmp_path, "radial_stiffness_n_per_m")
    leaves = {l.path: l for l in walk_inputs(tmp_path, fn, _classes(tmp_path))}
    assert leaves["medium.n"].declared_by == "The immersion medium the bead sits in."
    assert leaves["power_w"].declared_by == ""      # not a class field


def test_a_forward_reference_expands_like_the_class_it_names(tmp_path):
    """`setup: 'SampleSetup'` is the same type, quoted.

    `ast.unparse` renders a string annotation with its quotes, so the base type
    read as `'SampleSetup'` and never matched the dataclass -- the closure
    stopped at the parameter. Every gate in MS's `sample/checks.py` is annotated
    that way, so asking what G15 needs returned one leaf named `setup` instead
    of the objective and the sample index it reads. PEP 563 makes the quoted
    form the normal one, which is what makes this a defect and not an edge case.
    """
    write_module(tmp_path, '''
        from dataclasses import dataclass

        @dataclass(frozen=True)
        class Objective:
            """The objective in the light path."""
            na: float
            immersion: str

        @dataclass(frozen=True)
        class SampleSetup:
            """What lens 4 needs to judge a sample."""
            objective: Objective
            n_sample: float | None = None

        def check_na_feasibility(setup: 'SampleSetup'):
            """G15: NA <= n_immersion."""
    ''', name="checks.py")

    _, fn = find_function(tmp_path, "check_na_feasibility")
    paths = {l.path for l in walk_inputs(tmp_path, fn, _classes(tmp_path))}
    assert "setup.objective.na" in paths
    assert "setup.objective.immersion" in paths
    assert "setup.n_sample" in paths
    # The unexpanded parameter must not survive beside its own fields, or a
    # caller sees the same input twice under two names.
    assert "setup" not in paths


# --- resolving against the registries --------------------------------------

def test_registry_keys_read_the_entries_not_only_the_comment(tmp_path):
    """`data/objectives.yaml` carries no schema comment block.

    A declaration-only lookup finds nothing there — and `na` is the field the
    whole trap calculation turns on.
    """
    d = tmp_path / "data"
    d.mkdir()
    (d / "objectives.yaml").write_text(
        "objectives:\n"
        "  60x-Oil: {magnification: 60, na: 1.4, immersion: oil}\n"
        "  40x-WI:  {magnification: 40, na: 1.15, immersion: water}\n")
    keys = registry_keys(tmp_path)["data/objectives.yaml"]
    assert {"na", "magnification", "immersion"} <= keys


def test_a_stale_alias_is_a_finding_not_a_silent_miss(tmp_path):
    """The same discipline as a hand-maintained `implemented_in` table."""
    (tmp_path / "a.yaml").write_text(textwrap.dedent("""
        aliases:
          radius_m: {registry: data/particles.yaml, field: diameter_um}
          ghost:    {registry: data/particles.yaml, field: gone_field}
          nowhere:  {registry: data/absent.yaml, field: whatever}
    """).lstrip())
    aliases = load_aliases(tmp_path / "a.yaml")
    keys = {"data/particles.yaml": {"diameter_um", "material"}}
    checks = {f.check for f in verify_aliases(aliases, keys)}
    subjects = {f.subject.split(" ->")[0] for f in verify_aliases(aliases, keys)}
    assert checks == {"alias_field_missing", "alias_registry_missing"}
    assert subjects == {"ghost", "nowhere"}
    assert all(f.severity == "error" for f in verify_aliases(aliases, keys))


def test_missing_alias_file_is_not_an_error(tmp_path):
    assert load_aliases(tmp_path / "absent.yaml") == {}


# --- status precedence -----------------------------------------------------

def test_blocked_outranks_unresolved():
    """A named missing input is actionable; a missing mapping is not."""
    ready = Leaf(path="a", name="a", type="float",
                 supplied_by=[{"registry": "r", "field": "a", "filled": 3, "total": 8}])
    blocked = Leaf(path="b", name="b", type="float",
                   supplied_by=[{"registry": "r", "field": "b", "filled": 0, "total": 6}])
    unresolved = Leaf(path="c", name="c", type="float")

    assert ready.status == "ready"
    assert blocked.status == "blocked"
    assert unresolved.status == "unresolved"

    base = dict(computation="f", location="l", signature="s", summary="")
    assert Recipe(**base, leaves=[ready]).status == "ready"
    assert Recipe(**base, leaves=[ready, unresolved]).status == "unresolved"
    assert Recipe(**base, leaves=[ready, unresolved, blocked]).status == "blocked"


def test_an_optional_input_does_not_block_the_recipe():
    opt = Leaf(path="o", name="o", type="float | None", optional=True)
    ok = Leaf(path="a", name="a", type="float",
              supplied_by=[{"registry": "r", "field": "a", "filled": 1, "total": 1}])
    r = Recipe(computation="f", location="l", signature="s", summary="",
               leaves=[ok, opt])
    assert r.status == "ready"


def test_an_unknown_computation_returns_none(tmp_path):
    write_module(tmp_path, MODULE)
    assert recipe(tmp_path, "no_such_function") is None
