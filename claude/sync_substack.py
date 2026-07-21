#!/usr/bin/env python3
"""Sync Substack posts into native al-folio Jekyll posts.

Runs locally (Substack blocks automated fetches from CI IPs, not your machine).
Reads your Substack RSS feed, finds posts that don't yet have a native mirror in
_posts/, converts each post's HTML body to kramdown markdown (footnotes -> [^n],
images downloaded into assets/img/ using the site's centered-<div> convention,
formatting preserved), and writes _posts/<date>-<slug>.md. It never commits,
never publishes, and never overwrites an existing post — you review first.

Usage:
    python3 claude/sync_substack.py                     # sync all un-synced posts
    python3 claude/sync_substack.py --url <substack-url># one specific post
    python3 claude/sync_substack.py --slug shortname    # override output slug
    python3 claude/sync_substack.py --tags "ai-safety"  # set front-matter tags
    python3 claude/sync_substack.py --dry-run           # show plan, write nothing
    python3 claude/sync_substack.py --feed-file f.xml   # use a saved feed (testing)

Standard library only — no pip install required.
"""

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser

# .avif originals (Substack sometimes serves these) are converted to .jpg to
# match the site's all-jpeg convention and avoid host MIME/compat issues. Uses
# macOS `sips` when present; otherwise the avif is kept as-is.
_HAVE_SIPS = shutil.which("sips") is not None

FEED_URL_FALLBACK = "https://edwardfriedman3.substack.com/feed"
USER_AGENT = "Mozilla/5.0 (compatible; substack-sync)"

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSTS_DIR = os.path.join(REPO, "_posts")
IMG_DIR = os.path.join(REPO, "assets", "img")
CONFIG = os.path.join(REPO, "_config.yml")

# Substack UI chrome that rides along in RSS content and must be dropped.
SKIP_CLASS_MARKERS = (
    "subscription-widget",
    "button-wrapper",
    "pencraft",
    "image-link-expand",
    "footnote-hovercard",
    "poll-",
    "share",
)
VOID_TAGS = {"br", "img", "hr", "source", "meta", "input", "link", "wbr"}
HEADINGS = {"h1": 1, "h2": 2, "h3": 3, "h4": 4, "h5": 5, "h6": 6}


# --------------------------------------------------------------------------- #
# Minimal HTML -> DOM (stdlib HTMLParser is event-based; build a tiny tree).   #
# --------------------------------------------------------------------------- #
class Node:
    __slots__ = ("tag", "attrs", "children", "text")

    def __init__(self, tag=None, attrs=None):
        self.tag = tag
        self.attrs = dict(attrs or {})
        self.children = []
        self.text = None  # set for text nodes (tag is None)

    def cls(self):
        return self.attrs.get("class", "") or ""


class DomBuilder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root")
        self.stack = [self.root]

    def handle_starttag(self, tag, attrs):
        node = Node(tag, attrs)
        self.stack[-1].children.append(node)
        if tag not in VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag, attrs):
        self.stack[-1].children.append(Node(tag, attrs))

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return  # tolerate unclosed inner tags

    def handle_data(self, data):
        node = Node(None)
        node.text = data
        self.stack[-1].children.append(node)


def parse_html(fragment):
    b = DomBuilder()
    b.feed(fragment)
    b.close()
    return b.root


# --------------------------------------------------------------------------- #
# HTML -> kramdown converter                                                   #
# --------------------------------------------------------------------------- #
class Converter:
    def __init__(self, slug):
        self.slug = slug
        self.footnotes = {}          # number(int) -> markdown text
        self.images = []             # list of (source_url, filename)
        self._img_seen = {}          # source_url -> filename (dedupe within post)

    # ---- public ----
    def convert(self, html_body):
        root = parse_html(html_body)
        body = self._render_blocks(root).strip()
        if self.footnotes:
            defs = "\n".join(
                f"[^{n}]: {self.footnotes[n]}" for n in sorted(self.footnotes)
            )
            body = f"{body}\n\n{defs}"
        return body + "\n"

    # ---- block level ----
    def _render_blocks(self, node):
        out = []
        for child in node.children:
            piece = self._render_block(child)
            if piece and piece.strip():
                out.append(piece.strip())
        return "\n\n".join(out)

    def _render_block(self, node):
        if node.tag is None:  # stray text between blocks
            t = node.text.strip()
            return t if t else ""
        if self._is_skippable(node):
            return ""
        tag = node.tag
        if tag in HEADINGS:
            return "#" * HEADINGS[tag] + " " + self._render_inline(node).strip()
        if tag == "p":
            return self._render_inline(node).strip()
        if tag == "hr":
            return "---"
        if tag in ("ul", "ol"):
            return self._render_list(node, ordered=(tag == "ol"))
        if tag == "blockquote":
            inner = self._render_blocks(node)
            return "\n".join(("> " + ln).rstrip() for ln in inner.split("\n"))
        if "captioned-image-container" in node.cls() or tag == "figure":
            return self._render_image(node)
        if tag == "div" and node.cls().split(" ")[0] == "footnote":
            self._record_footnote(node)
            return ""
        # generic container (div/span/section/…): recurse into blocks
        return self._render_blocks(node)

    def _render_list(self, node, ordered):
        lines = []
        i = 1
        for li in node.children:
            if li.tag != "li":
                continue
            marker = f"{i}. " if ordered else "- "
            text = self._render_inline(li).strip()
            lines.append(marker + text)
            i += 1
        return "\n".join(lines)

    # ---- inline level ----
    def _render_inline(self, node):
        parts = []
        for child in node.children:
            if child.tag is None:
                parts.append(child.text or "")
                continue
            if self._is_skippable(child):
                continue
            tag = child.tag
            if tag in ("em", "i"):
                parts.append(self._emphasize(child, "*"))
            elif tag in ("strong", "b"):
                parts.append(self._emphasize(child, "**"))
            elif tag in ("code",):
                parts.append(f"`{self._render_inline(child).strip()}`")
            elif tag == "a":
                if "footnote-anchor" in child.cls():
                    num = self._render_inline(child).strip()
                    parts.append(f"[^{num}]")
                else:
                    href = child.attrs.get("href", "").strip()
                    text = self._render_inline(child).strip()
                    parts.append(f"[{text}]({href})" if href and text else text)
            elif tag == "br":
                parts.append("  \n")
            elif tag == "img":
                parts.append(self._image_markup(child, inline=True))
            else:  # span or other inline wrapper -> passthrough
                parts.append(self._render_inline(child))
        text = "".join(parts)
        return re.sub(r"[ \t]+\n", "\n", text)

    def _emphasize(self, node, marker):
        """Wrap inline content in `marker`, keeping boundary whitespace OUTSIDE
        the markers (markdown emphasis can't hug a space: `* x *` is invalid)."""
        raw = self._render_inline(node)
        core = raw.strip()
        if not core:
            return raw  # whitespace-only emphasis: keep the space, drop markers
        lead = raw[: len(raw) - len(raw.lstrip())]
        trail = raw[len(raw.rstrip()):]
        return f"{lead}{marker}{core}{marker}{trail}"

    # ---- footnotes ----
    def _record_footnote(self, node):
        num = None
        content_node = None
        for c in node.children:
            if c.tag == "a" and "footnote-number" in c.cls():
                raw = self._render_inline(c).strip()
                m = re.search(r"\d+", raw)
                if m:
                    num = int(m.group())
            elif c.tag == "div" and "footnote-content" in c.cls():
                content_node = c
        if num is None or content_node is None:
            return
        text = self._render_blocks(content_node).strip()
        # kramdown footnote defs are single logical line; flatten paragraphs.
        text = re.sub(r"\s*\n\s*", " ", text).strip()
        self.footnotes[num] = text

    # ---- images ----
    def _render_image(self, node):
        img = self._find(node, "img")
        if img is None:
            return ""
        markup = self._image_markup(img, inline=False)
        caption = self._find(node, "figcaption")
        if caption is not None:
            cap_text = self._render_inline(caption).strip()
            if cap_text:
                markup += (
                    '\n<div style="text-align: center;">'
                    f"<em>{cap_text}</em></div>"
                )
        return markup

    def _image_markup(self, img, inline):
        source_url = self._best_image_src(img)
        if not source_url:
            return ""
        filename = self._image_filename(source_url)
        rel = f"/assets/img/{filename}"
        return (
            '<div style="text-align: center;">\n'
            f"  <img src=\"{{{{ '{rel}' | relative_url }}}}\" "
            'style="max-width: 100%; height: auto;">\n'
            "</div>"
        )

    def _best_image_src(self, img):
        # Prefer the original (unresized) source from Substack's data-attrs JSON.
        data_attrs = img.attrs.get("data-attrs")
        if data_attrs:
            try:
                src = json.loads(data_attrs).get("src")
                if src:
                    return src
            except (ValueError, TypeError):
                pass
        return img.attrs.get("src", "").strip() or None

    def _image_filename(self, source_url):
        if source_url in self._img_seen:
            return self._img_seen[source_url]
        n = len(self.images) + 1
        base = source_url.split("?")[0].rstrip("/").split("/")[-1]
        ext_m = re.search(r"\.(avif|webp|jpe?g|png|gif)$", base, re.I)
        ext = ext_m.group(0).lower() if ext_m else ".jpg"
        if ext == ".jpeg":
            ext = ".jpg"
        if ext == ".avif" and _HAVE_SIPS:
            ext = ".jpg"  # converted on download
        filename = f"{self.slug}-{n}{ext}"
        self._img_seen[source_url] = filename
        self.images.append((source_url, filename))
        return filename

    # ---- helpers ----
    def _is_skippable(self, node):
        if node.tag in ("button", "svg", "script", "style"):
            return True
        cls = node.cls()
        return any(m in cls for m in SKIP_CLASS_MARKERS)

    def _find(self, node, tag):
        if node.tag == tag:
            return node
        for c in node.children:
            found = self._find(c, tag)
            if found is not None:
                return found
        return None


# --------------------------------------------------------------------------- #
# Feed parsing                                                                 #
# --------------------------------------------------------------------------- #
def _tag(block, name):
    m = re.search(rf"<{name}[^>]*>(.*?)</{name}>", block, re.S)
    if not m:
        return ""
    val = m.group(1)
    cdata = re.search(r"<!\[CDATA\[(.*?)\]\]>", val, re.S)
    if cdata:
        val = cdata.group(1)
    return val.strip()


def parse_feed(xml):
    items = []
    for block in re.split(r"<item>", xml)[1:]:
        block = block.split("</item>")[0]
        link = _tag(block, "link")
        content = ""
        cm = re.search(
            r"<content:encoded>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</content:encoded>",
            block,
            re.S,
        )
        if cm:
            content = cm.group(1)
        items.append(
            {
                "title": html.unescape(_tag(block, "title")),
                "link": link,
                "slug": link.rstrip("/").split("/")[-1],
                "pubdate": _tag(block, "pubDate"),
                "description": html.unescape(_tag(block, "description")),
                "content": content,
            }
        )
    return items


def item_date(item):
    return parsedate_to_datetime(item["pubdate"]).date().isoformat()


# --------------------------------------------------------------------------- #
# Sync-state detection                                                         #
# --------------------------------------------------------------------------- #
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[\s_]+", "-", text).strip("-")


def existing_mirrors():
    """Return list of (date, stem_slug) for every native _posts/*.md."""
    mirrors = []
    for name in os.listdir(POSTS_DIR):
        if not name.endswith(".md") or name.startswith("_"):
            continue
        m = re.match(r"(\d{4}-\d{2}-\d{2})-(.+)\.md$", name)
        if not m:
            continue
        mirrors.append((m.group(1), slugify(m.group(2))))
    return mirrors


def is_synced(item, mirrors):
    """A post is synced when its Substack slug matches an existing post's
    filename stem. Slug is the reliable key; the date can drift (e.g. a file
    dated one day off from Substack's pubDate), so it is not required."""
    slug = item["slug"]
    for _mdate, mstem in mirrors:
        if slug == mstem:
            return True
        # tolerate the native stem being an extended form of the Substack slug
        if len(slug) >= 8 and (slug in mstem or mstem in slug):
            return True
    return False


# --------------------------------------------------------------------------- #
# Rendering a full post                                                        #
# --------------------------------------------------------------------------- #
def yaml_quote(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def build_post(item, slug, tags):
    conv = Converter(slug)
    body = conv.convert(item["content"])
    fm = [
        "---",
        "layout: post",
        f"title: {yaml_quote(item['title'])}",
        f"date: {item_date(item)}",
        f"description: {yaml_quote(item['description'])}",
        f"tags: {tags or ''}".rstrip(),
        "categories:",
        "toc:",
        "  sidebar: left",
        "---",
        "",
    ]
    return "\n".join(fm) + "\n" + body, conv.images


def download_images(images, dry_run):
    for url, filename in images:
        dest = os.path.join(IMG_DIR, filename)
        if os.path.exists(dest):
            print(f"    image exists, skipping: assets/img/{filename}")
            continue
        if dry_run:
            print(f"    would download: {url}\n      -> assets/img/{filename}")
            continue
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
        src_is_avif = url.split("?")[0].lower().endswith(".avif")
        if src_is_avif and filename.endswith(".jpg") and _HAVE_SIPS:
            tmp = dest + ".avif"
            with open(tmp, "wb") as fh:
                fh.write(data)
            subprocess.run(
                ["sips", "-s", "format", "jpeg", tmp, "--out", dest],
                check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
            os.remove(tmp)
            print(f"    downloaded + converted avif->jpg: assets/img/{filename}")
        else:
            with open(dest, "wb") as fh:
                fh.write(data)
            print(f"    downloaded: assets/img/{filename} ({len(data):,} bytes)")


# --------------------------------------------------------------------------- #
# CLI                                                                          #
# --------------------------------------------------------------------------- #
def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", "replace")


def feed_url():
    """Prefer a live (non-commented) rss_url in _config.yml, else the fallback.
    Retiring the plugin comments out external_sources, so commented lines are
    ignored and we fall back to the constant."""
    try:
        for line in open(CONFIG, encoding="utf-8"):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            m = re.match(r"rss_url:\s*(\S+)", stripped)
            if m:
                return m.group(1)
    except OSError:
        pass
    return FEED_URL_FALLBACK


def main(argv=None):
    ap = argparse.ArgumentParser(description="Sync Substack posts to _posts/.")
    ap.add_argument("--url", help="Sync only this Substack post URL.")
    ap.add_argument("--slug", help="Override output slug (default: Substack slug).")
    ap.add_argument("--tags", default="", help="Front-matter tags line, e.g. 'ai-safety'.")
    ap.add_argument("--dry-run", action="store_true", help="Show plan, write nothing.")
    ap.add_argument("--feed-file", help="Read feed XML from a local file (testing).")
    args = ap.parse_args(argv)

    xml = open(args.feed_file, encoding="utf-8").read() if args.feed_file else fetch(feed_url())
    items = parse_feed(xml)
    mirrors = existing_mirrors()

    if args.url:
        target = args.url.rstrip("/")
        items = [it for it in items if it["link"].rstrip("/") == target]
        if not items:
            print(f"No feed item matches --url {args.url}", file=sys.stderr)
            return 1
        todo = items
    else:
        todo = [it for it in items if not is_synced(it, mirrors)]

    if not todo:
        print("All Substack posts are already synced. Nothing to do.")
        return 0

    print(f"Found {len(todo)} un-synced post(s):")
    for it in todo:
        print(f"  - {it['title']}  ({item_date(it)})")
    print()

    written = []
    for it in todo:
        slug = args.slug if (args.slug and len(todo) == 1) else it["slug"]
        dest = os.path.join(POSTS_DIR, f"{item_date(it)}-{slug}.md")
        rel = os.path.relpath(dest, REPO)
        if os.path.exists(dest):
            print(f"  SKIP (exists): {rel}")
            continue
        content, images = build_post(it, slug, args.tags)
        print(f"  {it['title']}")
        print(f"    -> {rel}  ({len(images)} image(s), footnotes included)")
        download_images(images, args.dry_run)
        if not args.dry_run:
            with open(dest, "w", encoding="utf-8") as fh:
                fh.write(content)
            written.append(rel)

    print()
    if args.dry_run:
        print("Dry run — no files written.")
    elif written:
        print("Wrote:")
        for r in written:
            print(f"  {r}")
        print("\nReview each post, set `tags:` if needed, then commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
