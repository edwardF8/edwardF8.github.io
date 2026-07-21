#!/usr/bin/env python3
"""Tests for sync_substack conversion. Run: python3 claude/test_sync_substack.py"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_substack import Converter, parse_feed  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    status = "ok  " if cond else "FAIL"
    print(f"  [{status}] {name}" + (f" -- {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def conv(html):
    return Converter("test-post").convert(html)


# --- unit fixtures --------------------------------------------------------- #
def test_formatting():
    md = conv("<h3>Title</h3><p>Some <strong>bold</strong> and <em>italic</em> "
              'and a <a href="https://x.com">link</a>.</p>')
    check("h3 -> ###", "### Title" in md)
    check("bold", "**bold**" in md)
    check("italic", "*italic*" in md)
    check("link", "[link](https://x.com)" in md)


def test_emphasis_boundary_space():
    # space inside <em> must move outside the markers, not vanish
    md = conv("<p>line <em>Title”, </em>they think</p>")
    check("space kept after emphasis", "*Title”,* they think" in md, repr(md))
    md2 = conv("<p>a <strong>bold </strong>b</p>")
    check("space around strong", "a **bold** b" in md2, repr(md2))


def test_list_and_quote():
    md = conv("<ul><li>one</li><li>two</li></ul><blockquote><p>quoted</p></blockquote>")
    check("list item one", "- one" in md)
    check("list item two", "- two" in md)
    check("blockquote", "> quoted" in md)


def test_footnotes():
    html = (
        '<p>Fact<a class="footnote-anchor" id="footnote-anchor-1" '
        'href="#footnote-1">1</a> and more<a class="footnote-anchor" '
        'href="#footnote-2">2</a>.</p>'
        '<div class="footnote"><a class="footnote-number">1</a>'
        '<div class="footnote-content"><p>First note.</p></div></div>'
        '<div class="footnote"><a class="footnote-number">2</a>'
        '<div class="footnote-content"><p>Second note.</p></div></div>'
    )
    md = conv(html)
    check("inline ref [^1]", "Fact[^1]" in md)
    check("inline ref [^2]", "more[^2]" in md)
    check("def [^1]:", "[^1]: First note." in md)
    check("def [^2]:", "[^2]: Second note." in md)
    check("no raw footnote html", "footnote-anchor" not in md and "<div" not in md.split("[^1]:")[0])


def test_image():
    html = (
        '<div class="captioned-image-container"><figure>'
        '<a class="image-link"><picture><img '
        'src="https://cdn/x/y_800x600.jpeg" '
        'data-attrs="{&quot;src&quot;:&quot;https://s3/img/abc_800x600.jpeg&quot;}">'
        '</picture>'
        '<button>x</button><svg><line/></svg></a>'
        '<figcaption class="image-caption">A caption</figcaption>'
        '</figure></div>'
    )
    c = Converter("my-slug")
    md = c.convert(html)
    check("centered div", 'style="text-align: center;"' in md)
    check("relative_url ref", "relative_url" in md and "/assets/img/my-slug-1.jpg" in md)
    check("uses original s3 src", c.images[0][0] == "https://s3/img/abc_800x600.jpeg")
    check("jpeg->jpg ext", c.images[0][1] == "my-slug-1.jpg")
    check("caption rendered", "<em>A caption</em>" in md)
    check("no button/svg leak", "<button" not in md and "<svg" not in md)


# --- invariants on the real post ------------------------------------------- #
def test_real_post():
    here = os.path.dirname(__file__)
    feed_path = os.path.join(here, "fixtures", "feed_sample.xml")
    if not os.path.exists(feed_path):
        print("  [skip] real-post test (fixtures/feed_sample.xml not present)")
        return
    xml = open(feed_path, encoding="utf-8").read()
    item = next(i for i in parse_feed(xml)
                if "responsibility-of-interpretation" in i["link"])
    c = Converter("the-responsibility-of-interpretation")
    md = c.convert(item["content"])

    refs = set(re.findall(r"\[\^(\d+)\]", md.split("[^1]:")[0] if "[^1]:" in md else md))
    defs = set(re.findall(r"^\[\^(\d+)\]:", md, re.M))
    check("every ref has a def", refs.issubset(defs), f"orphans={refs - defs}")
    check("22 footnote defs", len(defs) == 22, f"got {len(defs)}")
    check("4 images", len(c.images) == 4, f"got {len(c.images)}")
    for leak in ("footnote-anchor", "<button", "<svg", "captioned-image",
                 "pencraft", "data-attrs", "class=\"footnote"):
        check(f"no leak: {leak}", leak not in md)
    check("no substack cdn hotlink", "substackcdn.com" not in md)
    check("headings present", "### " in md)


if __name__ == "__main__":
    for t in (test_formatting, test_emphasis_boundary_space, test_list_and_quote,
              test_footnotes, test_image, test_real_post):
        print(t.__name__)
        t()
    print()
    if FAILS:
        print(f"{len(FAILS)} FAILED: {FAILS}")
        sys.exit(1)
    print("All checks passed.")
