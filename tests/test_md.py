from librarian.md import frontmatter, has_falsifier, sections, slug


def test_missing_frontmatter_is_not_an_error():
    """MS's stores are mixed on purpose.

    `kb/expertise/` carries frontmatter and `kb/decisions/` does not. An adapter
    that required it would drop 20 decision records without saying so.
    """
    fm, body = frontmatter("# 2026-08-19 · Lens 4 scope\n\ntext\n")
    assert fm == {}
    assert body.startswith("# 2026-08-19")

    fm, body = frontmatter("---\nid: x\nevidence: measured\n---\n\n## Verdict\n\ny\n")
    assert fm == {"id": "x", "evidence": "measured"}
    assert body.strip().startswith("## Verdict")


def test_a_body_with_no_headings_still_gets_a_coordinate():
    assert [s.locator for s in sections("just prose\n")] == ["#"]


def test_sections_and_duplicate_headings():
    body = "pre\n\n## Verdict\na\n\n## Related\nb\n\n## Verdict\nc\n"
    locs = [s.locator for s in sections(body)]
    assert locs == ["#", "verdict", "related", "verdict-2"]


def test_slug_is_ascii_even_for_non_ascii_headings():
    """Korean headings exist in BD's corpus.

    Passing them through is how BD's `entries/` filenames were produced, and
    those split under NFC/NFD across macOS and Windows -- the same file looks
    like two. Prose in any language; locators in ASCII.
    """
    s = slug("무차원화 규약")
    assert s.startswith("h-") and s.isascii()


def test_has_falsifier_reads_the_convention():
    assert has_falsifier("## Falsification conditions\n1. measure it here\n")
    assert has_falsifier("the observation that would retire this entry")
    assert not has_falsifier("## Verdict\n## Related\n")
