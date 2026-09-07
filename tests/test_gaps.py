"""Regression tests for two precision bugs that produced confident wrong answers."""

import ast
import textwrap

from librarian.gaps import _filled, _reads, gate_functions, registry_fields


def test_presence_means_a_non_empty_value_not_a_key():
    """`power_at_sample_mw` exists as a key on almost every line, and is `{}`.

    `photo/gate.py` states it in prose -- *"power_at_sample_mw is empty for every
    line of every source"* -- and a key-existence check reported 5 of 6 sources
    as supplying it, i.e. the opposite of the truth.
    """
    src = {"lines": {"365": {"power_at_sample_mw": {}},
                     "440": {"power_at_sample_mw": None}}}
    assert _filled(src, "power_at_sample_mw") is False

    src["lines"]["488"] = {"power_at_sample_mw": 6.2}
    assert _filled(src, "power_at_sample_mw") is True


def test_presence_reaches_through_nesting():
    """A flat check reports the wrong location rather than no location."""
    assert _filled({"a": {"b": {"c": {"field": 1}}}}, "field") is True
    assert _filled([{"field": ""}, {"field": 3}], "field") is True


def test_gate_attribution_ignores_bare_identifiers():
    """A registry field reaches a gate as an attribute or a string key.

    Counting `ast.Name` attributed `data/particles.yaml > product` to G11,
    because `validity/check_statistical_power` happens to have a local called
    `product`. `lifetime_ns` in G20 is the real shape: attribute and constant.
    """
    tree = ast.parse(textwrap.dedent('''
        def check_statistical_power(setup):
            """G11: is the reported error bar reachable at all?"""
            product = 1
            for x in setup.streams:
                product *= x
            return product

        def check_saturation(setup):
            """G20: is the dye being driven into saturation?"""
            return setup.lifetime_ns, {"lifetime_ns": setup.lifetime_ns}
    '''))
    fns = {n.name: _reads(n) for n in tree.body}
    assert "product" not in fns["check_statistical_power"]
    assert "streams" in fns["check_statistical_power"]
    assert "lifetime_ns" in fns["check_saturation"]


def test_gate_functions_need_the_id_in_their_own_docstring(tmp_path):
    """`optics/checks.py` carries questions as docstrings and no gate id.

    It therefore contributes nothing, which is a finding about optics rather
    than a parse failure here.
    """
    d = tmp_path / "optics"
    d.mkdir()
    (d / "checks.py").write_text(textwrap.dedent('''
        def check_excitation(channel):
            """Does this line actually excite this dye through this path?"""
            return channel.na
    '''))
    assert gate_functions(tmp_path) == []


def test_registry_fields_read_the_schema_comment(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "fluorophores.yaml").write_text(textwrap.dedent('''
        # Fluorophore registry.
        # fluorophores:
        #   <canonical-name>:
        #     quantum_yield:    fluorescence quantum yield
        #     bleach_photons:   mean photons emitted before bleaching
        fluorophores:
          AlexaFluor488: {quantum_yield: 0.92}
    ''').lstrip())
    fields = registry_fields(tmp_path)["data/fluorophores.yaml"]
    assert {"quantum_yield", "bleach_photons"} <= fields
